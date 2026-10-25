#!/usr/bin/env python3
"""halt_guard.py — the one stop check every GPU client goes through.

A stop marker in the marker directory stops every client. An allow marker that
names the entry point lets that one client through; an allow marker leaves the
stop marker exactly where it is.

    marker directory : H3_HALT_DIR, or this repository's production/ directory
    stop markers     : H3_STOP_MARKER (default STOPPED.txt)
                        H3_STOP_MARKER_GLOB (default STOPPED-*.txt)
    allow markers    : H3_ALLOW_MARKER_GLOB (default ALLOW-*.txt)
                        one entry point per line, '#' starts a comment

The entry point is the name the caller passes, not the name of the process that
happens to submit. The clip path runs inside h3_comfy.py, and so does the film
render path, so the caller passes its own name down in H3_ENTRY_POINT.

Exit code 3 means "the work is stopped". A caller can tell that from a fault.

Usage:
    from halt_guard import require_not_halted
    require_not_halted("h3_comfy.py")     # raises SystemExit(3) when refused
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# The repository's production directory: production/tools/pinned-h3 -> production
DEFAULT_MARKER_DIR = os.path.dirname(os.path.dirname(HERE))


def marker_dir():
    """The directory the stop and allow markers are read from."""
    return os.path.abspath(os.environ.get("H3_HALT_DIR") or DEFAULT_MARKER_DIR)


def stop_marker():
    """The first stop marker in the marker directory, or None."""
    directory = marker_dir()
    if not os.path.isdir(directory):
        return None
    name = os.environ.get("H3_STOP_MARKER", "STOPPED.txt")
    path = os.path.join(directory, name)
    if os.path.isfile(path):
        return path
    pattern = os.environ.get("H3_STOP_MARKER_GLOB", "STOPPED-*.txt")
    for candidate in sorted(glob.glob(os.path.join(directory, pattern))):
        if os.path.isfile(candidate):
            return candidate
    return None


def allow_markers():
    """Every allow marker in the marker directory."""
    directory = marker_dir()
    if not os.path.isdir(directory):
        return []
    pattern = os.environ.get("H3_ALLOW_MARKER_GLOB", "ALLOW-*.txt")
    return [p for p in sorted(glob.glob(os.path.join(directory, pattern)))
            if os.path.isfile(p)]


def allowed_for(entry):
    """The allow marker that names this entry point, or None."""
    if not entry:
        return None
    for path in allow_markers():
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.split("#", 1)[0].strip()
                    if line and line == entry:
                        return path
        except OSError:
            continue
    return None


def require_not_halted(entry=None):
    """Stop the submission when the work is stopped and nothing allows this entry point.

    Raises SystemExit(3) when refused.
    """
    entry = entry or os.environ.get("H3_ENTRY_POINT") or "unknown"
    directory = marker_dir()
    if not os.path.isdir(directory):
        # A guard whose marker directory is not there has no answer to give, so it
        # stops the run.
        print("[halt] the marker directory %s is not there - stopping" % directory,
              file=sys.stderr)
        raise SystemExit(3)
    marker = stop_marker()
    if marker:
        allow = allowed_for(entry)
        if allow:
            print("[halt] %s may run while %s is in place (allow: %s)."
                  % (entry, marker, allow), file=sys.stderr)
            return True
        print("[halt] %s did not start - %s is in place" % (entry, marker), file=sys.stderr)
        print("[halt] only whoever placed that marker takes it away.", file=sys.stderr)
        raise SystemExit(3)
    return True


if __name__ == "__main__":
    require_not_halted(sys.argv[1] if len(sys.argv) > 1 else None)
    print("running")
