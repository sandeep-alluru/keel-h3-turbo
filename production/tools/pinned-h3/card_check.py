#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""card_check.py — a card may not contradict itself, and the camera clause must be its own.

FIX 14 (2026-10-23). Root cause M4: "the S4 card said 'side view' while the schema emitted
'front-facing' - the card contradicted itself and the schema followed the wrong half." The
Level's S4 says "a side view of the woman walking between two parked cars" and "she walks
screen-left to screen-right", but its enter_state says "she is walking toward camera". The
prompt carried both, and the model read the half that was wrong.

So:

  * FACING is a thing a card can say, and it says it in several places at once: the size, the
    framing, the promise, the action, the enter_state, the exit_state, the camera. If two of
    those places say DIFFERENT facings, the card contradicts itself and is REFUSED - before
    it is rendered, not after;
  * the CAMERA CLAUSE is what the card actually says about where the camera stands, and it is
    emitted from the card's own words - never from the other half of a contradiction.

Usage:
    card_check.py <card.json>              # refuse a card that contradicts itself
    card_check.py <card.json> --clause 4   # print the camera clause of shot 4
"""

import json
import re
import sys

# The fields of a shot that can state a facing.
FACING_FIELDS = ("size", "framing", "promise", "action", "enter_state", "exit_state", "camera")

# The words that state a facing. Ordered: the first family that hits wins.
# "in front of her" is NOT here: the cards use it for the shadow, not for the camera.
FRONT = (
    r"towards?\s+the\s+camera|towards?\s+camera|facing\s+the\s+camera|"
    r"front[-\s]?facing|close\s+to\s+the\s+lens|"
    r"front[-\s]?left|front[-\s]?right|from\s+the\s+front"
)
SIDE = (
    r"side[-\s]?view|in\s+profile|\bprofile\b|side[-\s]?on|"
    r"screen[-\s]?left\s+to\s+screen[-\s]?right|screen[-\s]?right\s+to\s+screen[-\s]?left|"
    r"from\s+the\s+side|lit\s+from\s+the\s+side"
)
BACK = r"from\s+behind|back\s+to\s+the\s+camera|away\s+from\s+the\s+camera"

_FACINGS = (("front", FRONT), ("side", SIDE), ("back", BACK))
_COMPILED = [(name, re.compile(pattern, re.IGNORECASE)) for name, pattern in _FACINGS]

# What the camera clause says, for each facing.
# R3-L1: these used to read "the camera is in front of her, facing her", and the
# sentence built from them read "The camera: the camera is ...". The clause is now
# the clause; the sentence that carries it says "The camera is ...".
CLAUSE = {
    "front": "in front of her, facing her",
    "side": "side-on, in profile",
    "back": "behind her",
}


def facing_of(text):
    """The facing a piece of text states, or None when it states none."""
    if not text:
        return None
    for name, pattern in _COMPILED:
        if pattern.search(text):
            return name
    return None


def shot_number(shot):
    for key in ("n", "shot", "number"):
        if key in shot:
            return shot[key]
    return "?"


def all_facings_of(text):
    """Every facing a piece of text states - not just the first.

    R2-M23: a field that said BOTH "in profile" and "towards the camera" used to be
    read as whichever came first. A contradiction inside ONE field is as much a
    contradiction as one across two fields, and the model reads the wrong half either
    way.
    """
    if not text:
        return []
    return [name for name, pattern in _COMPILED if pattern.search(text)]


def shot_facings(shot):
    """Every (field, facing) the shot states."""
    found = []
    for field in FACING_FIELDS:
        facing = facing_of(shot.get(field, ""))
        if facing:
            found.append((field, facing))
    return found


def check_shot(shot, label=None):
    """Refuse a shot that contradicts itself. Returns the facing, or None."""
    label = label or ("S%s" % shot_number(shot))

    # R2-M23: a field that contradicts ITSELF is refused, before the cross-field check.
    for field in FACING_FIELDS:
        stated = all_facings_of(shot.get(field, ""))
        if len(stated) > 1:
            raise SystemExit(
                "%s contradicts itself inside one field: '%s' says %s. A field that says both "
                "is two shots, and the model will read the wrong half."
                % (label, field, " and ".join(stated)))

    found = shot_facings(shot)
    if not found:
        return None
    first = found[0]
    for field, facing in found[1:]:
        if facing != first[1]:
            raise SystemExit(
                "%s contradicts itself: '%s' says %s, but '%s' says %s. A shot that says both is "
                "not a shot - it is two shots, and the model will read the wrong half."
                % (label, first[0], first[1], field, facing))
    return first[1]


def check_scene_contract(data):
    """The SCENE contract, from scene_schema: one subject, one place, at most three beats.

    R3-M7: the production had a second card check (scene_schema.check_card) and the card
    builder used it while the RENDER used this one - so a card that broke the scene
    contract could be rendered, and a card that passed the contract could be built.
    The contract is now enforced HERE, at the one entry point every render goes
    through, and scene_schema keeps only the contract itself.

    A card that carries no scene fields at all (the card check's own minimal
    fixtures) is not a scene card, and the scene contract never applies to it. A card
    that carries them at the card level but not in its shots is refused: that is a card
    that was half built.
    """
    shots = data.get("shots") or []
    if not shots:
        return
    if "subject" not in data or "place" not in data:
        return                      # not a scene card
    required = ("place", "subject", "sound")
    if not all(k in shot for shot in shots for k in required):
        raise SystemExit("the card carries the scene fields and its shots do not - "
                         "it was half built")
    try:
        from scene_schema import SceneCard, check_card as _contract
    except ImportError as exc:
        raise SystemExit(
            "scene_schema.py holds the scene contract and is not in this tree. "
            "Put the production tree on PYTHONPATH to run this toolset."
        ) from exc
    _contract(SceneCard.from_json(data))


def check_card(data):
    """Refuse a card that contradicts itself. Returns the facing of each shot."""
    facings = {}
    # RC-H3: a card that declares the RE-ROLL DISCIPLINE must give every one of its
    # shots a rewritten prompt, or its re-roll is seed-only - and the rule is that a shot
    # the motion gate rejects is "re-rolled with a rewritten prompt, not just a new
    # seed". Nine of the thirty clip shots carried no rewritten field at all, so their
    # re-roll silently fell back to the base text.
    #
    # The discipline is DECLARED, because the production's other cards (the Level's) have the
    # same shape and are not re-rolled at all. A card that carries a rewritten field on
    # ANY shot declares it too, so a half-built clip card is caught rather than
    # slipping through with the marker missing.
    shots = data.get("shots") or []
    declares_reroll = (data.get("reroll_prompts") == "required"
                       or any(s.get("reroll_action") or s.get("reroll_camera") for s in shots))
    for shot in shots:
        label = "S%s" % shot_number(shot)
        if declares_reroll and not (shot.get("reroll_action") or shot.get("reroll_camera")):
            raise SystemExit(
                "%s carries no rewritten prompt (no 'reroll_action' and no 'reroll_camera'). "
                "A re-roll with the same prompt is a seed-only re-roll, which the re-roll "
                "discipline forbids."
                % label)
        facings[shot_number(shot)] = check_shot(shot, label)
    check_scene_contract(data)
    return facings


def camera_clause(shot):
    """The camera clause the card actually says, or None when the card says nothing."""
    facings = shot_facings(shot)
    if not facings:
        return None
    first = facings[0]
    for field, facing in facings[1:]:
        if facing != first[1]:
            raise SystemExit(
                "S%s contradicts itself: '%s' says %s, but '%s' says %s. The camera clause is not "
                "emitted for a card that says both." % (shot_number(shot), first[0], first[1],
                                                        field, facing))
    return CLAUSE[first[1]]


def camera_clause_sentence(shot):
    """The clause as a sentence, ready for a prompt. Empty when the card says nothing."""
    clause = camera_clause(shot)
    return ("The camera is %s." % clause) if clause else ""


def main():
    args = [a for a in sys.argv[1:]]
    clause_for = None
    if "--clause" in args:
        i = args.index("--clause")
        clause_for = args[i + 1]
        del args[i:i + 2]
    if not args:
        print("usage: card_check.py <card.json> [--clause <shot>]", file=sys.stderr)
        return 2
    with open(args[0], encoding="utf-8") as fh:
        data = json.load(fh)
    if clause_for is not None:
        for shot in data.get("shots", []):
            if str(shot_number(shot)) == str(clause_for):
                print(camera_clause_sentence(shot))
                return 0
        print("no shot %s in %s" % (clause_for, args[0]), file=sys.stderr)
        return 1
    facings = check_card(data)
    for number, facing in facings.items():
        print("S%s  facing %s" % (number, facing or "unstated"))
    print("CARD CLEAN: no shot contradicts itself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
