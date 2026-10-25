#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
artifact.py — canonical artifacts for the H3 film pipeline (fixes 1-4).

WHY THIS EXISTS (fix plan group 1)
---------------------------------
ComfyUI never overwrites: a second render of the same shot lands as
`_00002_`, `_00003_`, ... . The pipeline used to compose `_00001_` by hand in
half a dozen scripts, so the gate and the publish graded a STALE file while
the new render sat next to it. The production's own evidence: `film8/` holds
beacon-S2_00001_ .. _00005_ with the `_00001_` timestamps untouched. The
overnight engine then made 53 publish attempts, every one of them grading
the same old file.

THE RULE
--------
1. One canonical name per shot: `<film>-S<shot>.mp4`. No index in the
   production path.
2. A render is promoted onto that name ATOMICALLY: copy to a temporary name in
   the same directory, then `os.replace` onto the canonical name. A partial
   render can never appear as the canonical file.
3. The gate is given PATHS (a manifest), never a composed name.
4. Before a re-grade, the file's hash is compared with the hash of the last
   grading. Unchanged means: report "nothing new to grade" and stop.
5. A manifest records the hash of every file it grades, so a verdict can say
   exactly what it measured.

Commands
--------
  promote   --rendered R --canonical C
  manifest  --dir D --film F --shots 1,2,3 [--out FILE]
  check     --manifest FILE [--state FILE]
  record    --manifest FILE [--state FILE] [--gate NAME]
  verify    --manifest FILE
  hash      --file F
  path      --dir D --film F --shot S            the canonical name (a promote target)
  paths     --dir D --film F --shots 1,2,3        the canonical names, one per line
  resolve   --dir D --film F --shot S            the file that is really there now
  resolve-paths --dir D --film F --shots 1,2,3  the files that are really there now
  resolve-file  --dir D --stem NAME             the newest file of the old indexed family
  resolve-renders --dir D --film F --shots 1,2  the newest render of each shot in a raw output dir

Exit codes
----------
  0  success / something new to grade
  3  nothing new to grade (every hash unchanged)
  4  a file is missing or unreadable
  5  the operation did not complete
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def normalise_shot(shot):
    """The shot id in the production's own form: 'S1' and '1' are the SAME shot.

    The production's loops carry the shot as "S1" and the file is "level-S1.mp4".
    Normalising HERE means no caller has to know which form to pass - and the
    chain scripts never produce "level-SS1.mp4" by accident.
    """
    s = str(shot).strip()
    if len(s) > 1 and s[0] in ('S', 's') and s[1:].isdigit():
        s = s[1:]
    if not s.isdigit():
        raise ValueError('not a shot id: %r' % (shot,))
    return s


def canonical_name(film, shot):
    """The one canonical name for a shot. No index, ever."""
    return '%s-S%s.mp4' % (film, normalise_shot(shot))


def canonical_path(shot_dir, film, shot):
    return os.path.join(shot_dir, canonical_name(film, shot))


def legacy_name(film, shot):
    """The OLD indexed name. It is known HERE and nowhere else.

    The shots that predate the canonical-name rule are still on disk under it.
    No other file in the pipeline may compose this name.
    """
    return '%s-S%s_00001_.mp4' % (film, normalise_shot(shot))


def legacy_path(shot_dir, film, shot):
    return os.path.join(shot_dir, legacy_name(film, shot))


def resolve_path(shot_dir, film, shot, if_missing='canonical'):
    """The file that holds this shot's video, and which name it turned out to have.

    The canonical name wins. The legacy indexed family is accepted ONLY when it is
    what is actually on disk - and when it is, the NEWEST member of that family wins.

    This used to accept only `_00001_.mp4`: a render that ComfyUI had numbered
    `_00007_.mp4` was reported as MISSING while the stale first render sat on disk
    under the very name it looked for. A resolver that finds an older file and calls
    the shot present is the D16 pattern (a stale file satisfying a "does it exist"
    check).

    When neither exists the canonical name comes back (tagged 'missing') so the
    caller reports the name the file WILL have.
    """
    stem = '%s-S%s' % (film, normalise_shot(shot))
    found, tag = resolve_indexed(shot_dir, stem)
    if tag != 'missing':
        return found, tag
    if if_missing == 'legacy':
        return legacy_path(shot_dir, film, shot), 'missing'
    return canonical_path(shot_dir, film, shot), 'missing'


def resolve_indexed(shot_dir, stem):
    """Resolve <stem>.mp4, or the NEWEST <stem>_0000N_.mp4 of the old indexed family.

    This is how a render that ComfyUI named for itself (beacon-S3_00007_.mp4) is
    found: by what it is, not by an index somebody wrote down.
    """
    canonical = os.path.join(shot_dir, stem + '.mp4')
    if os.path.isfile(canonical):
        return canonical, 'canonical'
    best, best_mtime = None, -1.0
    try:
        names = os.listdir(shot_dir)
    except OSError:
        names = []
    # ComfyUI wraps the index in underscores on BOTH sides: "_00001_.mp4".
    pat = re.compile(r'^%s_\d{5}_?\.mp4$' % re.escape(stem))
    for name in names:
        if not pat.match(name):
            continue
        p = os.path.join(shot_dir, name)
        try:
            mt = os.path.getmtime(p)
        except OSError:
            continue
        if mt > best_mtime:
            best, best_mtime = p, mt
    if best:
        return best, 'legacy'
    return canonical, 'missing'


def atomic_promote(rendered, canonical):
    """Put the rendered file onto the canonical name, atomically.

    The temporary file lives in the SAME directory so os.replace is a rename on
    the same filesystem: the canonical name either is absent or is a
    complete file. There is never a half-written canonical file.
    """
    rendered = os.path.abspath(rendered)
    canonical = os.path.abspath(canonical)
    if not os.path.isfile(rendered):
        print('PROMOTE ERROR: no rendered file at %s' % rendered, file=sys.stderr)
        return 5
    if os.path.getsize(rendered) == 0:
        print('PROMOTE ERROR: rendered file is empty: %s' % rendered, file=sys.stderr)
        return 5
    if os.path.abspath(rendered) == canonical:
        digest = sha256(canonical)
        write_sidecar(canonical, digest)
        print('%s\t%s' % (canonical, digest))
        return 0

    os.makedirs(os.path.dirname(canonical) or '.', exist_ok=True)
    tmp = '%s.tmp.%d' % (canonical, os.getpid())
    try:
        shutil.copyfile(rendered, tmp)
        # fsync the data before the rename, so the canonical name can never
        # point at a file whose bytes are still in flight.
        fd = os.open(tmp, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, canonical)
    except OSError as e:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        print('PROMOTE ERROR: %s' % e, file=sys.stderr)
        return 5
    digest = sha256(canonical)
    write_sidecar(canonical, digest)
    print('%s\t%s' % (canonical, digest))
    return 0


def write_sidecar(path, digest):
    try:
        with open(path + '.sha256', 'w') as f:
            f.write('%s  %s\n' % (digest, os.path.basename(path)))
    except OSError:
        pass


def load_manifest(path):
    with open(path) as f:
        return json.load(f)


def read_paths_file(path):
    """A paths file is either an artifact.py manifest (JSON) or one path per line."""
    with open(path) as f:
        text = f.read()
    if text.lstrip().startswith('{'):
        data = json.loads(text)
        return [e['path'] for e in data.get('shots', [])]
    return [l.strip() for l in text.splitlines() if l.strip()]


def sha256_of(path):
    """The hash of a file, or None when the file is unreadable.

    The one implementation of this. It used to be copied into motion_gate.py and
    scene_continuity.py, so three files could drift apart and only one of them would
    be the one the production actually runs.
    """
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def manifest_from_paths(paths):
    """A manifest built from a list of exact paths - the files the gate grades."""
    entries = []
    missing = []
    for p in paths:
        if not os.path.isfile(p):
            missing.append(p)
            continue
        st = os.stat(p)
        entries.append({'shot': None, 'path': p, 'sha256': sha256(p),
                        'size': st.st_size, 'mtime': st.st_mtime})
    return {'shots': entries, 'missing': missing}


def manifest_for(args):
    """The manifest to work on: --manifest FILE, or --paths-file FILE."""
    if getattr(args, 'paths_file', None):
        return manifest_from_paths(read_paths_file(args.paths_file))
    return load_manifest(args.manifest)


def load_state(path):
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get('graded', {})
    except (OSError, ValueError):
        return {}


def save_state(path, state):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    tmp = '%s.tmp.%d' % (path, os.getpid())
    with open(tmp, 'w') as f:
        json.dump({'graded': state}, f, indent=2, sort_keys=True)
        f.write('\n')
    os.replace(tmp, path)


def cmd_promote(args):
    return atomic_promote(args.rendered, args.canonical)


def cmd_check(args):
    """The change-check (fix 3).

    Exit 3 = nothing new to grade AND the last grading of those exact bytes
    passed, so the gate must not run again. Exit 0 = there is something to
    grade (a new file, or the last grading was rejected).
    """
    m = manifest_for(args)
    state = load_state(args.state)
    if not m['shots']:
        print('MISSING: no shot files to grade', file=sys.stderr)
        return 4
    new = []
    unchanged = []
    for e in m['shots']:
        prev = state.get(e['path'])
        if prev and prev.get('sha256') == e['sha256']:
            unchanged.append((e['path'], prev))
        else:
            new.append(e['path'])
    if new:
        print('NEW TO GRADE: %d file(s)' % len(new))
        for p in new:
            print('  + %s' % p)
    if unchanged:
        print('UNCHANGED since the last grading: %d file(s)' % len(unchanged))
        for p, prev in unchanged:
            print('  = %s  (graded %d time(s), last verdict: %s)'
                  % (p, prev.get('gradings', 1) or 1,
                     prev.get('verdict', 'unknown')))
    if new:
        return 0
    rejected = [p for p, prev in unchanged
                if (prev.get('verdict') or '').lower() != 'pass']
    if rejected:
        print('NOTHING NEW TO GRADE, but the last grading was REJECTED for %d file(s) -'
              % len(rejected))
        print('the gate must run again.')
        for p in rejected:
            print('  ! %s' % p)
        return 0
    print('NOTHING NEW TO GRADE - stopping before the gate')
    return 3


def cmd_record(args):
    """Record that these exact bytes were graded, and with what verdict."""
    m = manifest_for(args)
    state = load_state(args.state)
    now = time.time()
    for e in m['shots']:
        prev = state.get(e['path']) or {}
        state[e['path']] = {
            'sha256': e['sha256'],
            'size': e.get('size'),
            'graded_at': now,
            'gate': args.gate or 'unspecified',
            'verdict': args.verdict,
            'gradings': (prev.get('gradings', 0) or 0) + 1,
        }
    save_state(args.state, state)
    print('recorded %d graded file(s) in %s (verdict: %s)'
          % (len(m['shots']), args.state, args.verdict))
    return 0


def cmd_path(args):
    """The canonical path for ONE shot. A promote target is ALWAYS this."""
    print(canonical_path(args.dir, args.film, args.shot))
    return 0


def cmd_resolve(args):
    """The file that holds this shot's video RIGHT NOW.

    This is what a READ uses: the canonical name when it is there, the legacy
    indexed name when that is what is actually on disk.
    """
    path, which = resolve_path(args.dir, args.film, args.shot, args.if_missing)
    print(path)
    if which == 'missing':
        print('MISSING %s' % path, file=sys.stderr)
        return 4
    if which == 'legacy':
        print('LEGACY NAME (still on disk): %s' % path, file=sys.stderr)
    return 0


def cmd_resolve_paths(args):
    """The files that hold the shots RIGHT NOW, one per line.

    This is what a GATE is handed: the exact paths, never a composed name.
    Only the shots that actually exist are listed.
    """
    shots = [s.strip() for s in args.shots.split(',') if s.strip()]
    missing = []
    for s in shots:
        path, which = resolve_path(args.dir, args.film, s, args.if_missing)
        if which == 'missing':
            missing.append(path)
            continue
        print(path)
    if missing and not args.allow_missing:
        for p in missing:
            print('MISSING %s' % p, file=sys.stderr)
        return 4
    return 0


def cmd_resolve_file(args):
    """The file that really is on disk for a name that is not a shot id.

    <stem>.mp4 if it is there, else the newest <stem>_0000N_.mp4.
    """
    path, which = resolve_indexed(args.dir, args.stem)
    print(path)
    if which == 'missing':
        print('MISSING %s' % path, file=sys.stderr)
        return 4
    if which == 'legacy':
        print('LEGACY NAME (still on disk): %s' % path, file=sys.stderr)
    return 0


def cmd_resolve_renders(args):
    """The renders of the shots, in a RAW ComfyUI output directory.

    For each shot: <film>-S<shot>.mp4 when it is there, else the NEWEST
    <film>-S<shot>_0000N_.mp4. This is how a step finds what a render actually
    produced - the newest one - instead of an index somebody wrote down.
    """
    shots = [s.strip() for s in args.shots.split(',') if s.strip()]
    missing = []
    for s in shots:
        path, which = resolve_indexed(args.dir,
                                      '%s-S%s' % (args.film, normalise_shot(s)))
        if which == 'missing':
            missing.append(path)
            continue
        print(path)
    if missing and not args.allow_missing:
        for p in missing:
            print('MISSING %s' % p, file=sys.stderr)
        return 4
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd')

    p = sub.add_parser('promote')
    p.add_argument('--rendered', required=True)
    p.add_argument('--canonical', required=True)
    p.set_defaults(func=cmd_promote)

    p = sub.add_parser('check')
    p.add_argument('--manifest')
    p.add_argument('--paths-file',
                   help='the exact files to grade, one path per line')
    p.add_argument('--state', required=True)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser('record')
    p.add_argument('--manifest')
    p.add_argument('--paths-file',
                   help='the exact files that were graded, one path per line')
    p.add_argument('--state', required=True)
    p.add_argument('--gate')
    p.add_argument('--verdict', required=True, choices=['pass', 'reject'],
                   help='pass or reject: a rejected grading must be re-run. R2-L2: this '
                        'defaulted to "pass", so a caller that forgot it recorded a PASS '
                        'for bytes that were never graded. It is required now.')
    p.set_defaults(func=cmd_record)

    p = sub.add_parser('path')
    p.add_argument('--dir', required=True)
    p.add_argument('--film', required=True)
    p.add_argument('--shot', required=True)
    p.set_defaults(func=cmd_path)

    p = sub.add_parser('resolve')
    p.add_argument('--dir', required=True)
    p.add_argument('--film', required=True)
    p.add_argument('--shot', required=True)
    p.add_argument('--if-missing', default='canonical', choices=['canonical', 'legacy'])
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser('resolve-paths')
    p.add_argument('--dir', required=True)
    p.add_argument('--film', required=True)
    p.add_argument('--shots', required=True)
    p.add_argument('--if-missing', default='canonical', choices=['canonical', 'legacy'])
    p.add_argument('--allow-missing', action='store_true')
    p.set_defaults(func=cmd_resolve_paths)

    p = sub.add_parser('resolve-file')
    p.add_argument('--dir', required=True)
    p.add_argument('--stem', required=True)
    p.set_defaults(func=cmd_resolve_file)

    p = sub.add_parser('resolve-renders')
    p.add_argument('--dir', required=True)
    p.add_argument('--film', required=True)
    p.add_argument('--shots', required=True)
    p.add_argument('--allow-missing', action='store_true')
    p.set_defaults(func=cmd_resolve_renders)

    args = ap.parse_args()
    if not getattr(args, 'func', None):
        ap.print_help()
        return 5
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
