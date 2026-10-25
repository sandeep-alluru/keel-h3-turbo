#!/usr/bin/env python3
"""prompt_compiler.py — build H3 prompts that never omit a researched rule.

Written after an audit found 3 of 12 researched rules applied in 0 of 24 prompts: named permanent features,
<Subject N> labels, and in-render cuts. Rules were being remembered rather than enforced; this compiles them in.

Usage:
    from prompt_compiler import Shot, Subject, compile_prompt
    p = compile_prompt(shot)
"""
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional

# FIX 14: the facing vocabulary and the contradiction check live in ONE place.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import card_check  # noqa: E402

I2VA_LINE = ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully "
             "referenced.")
FL2VA_LINE = ("How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the "
              "0.00-second mark of the target video; Picture 2 (from Shot {n}) aligns with the {dur}-second mark of "
              "the target video.")
MOOD_WORDS = ("epic", "majestic", "eerie", "ominous", "tense", "dramatic", "cinematic", "beautiful",
              "epic-sounding", "emotional", "moody", "atmospheric")


@dataclass
class Subject:
    """A thing that must stay the same across every shot. Named features are what make it stay the same —
    unnamed detail flattens toward an average (MiniMax reference guide, and our own persona drift)."""
    id: int
    name: str
    features: List[str]          # permanent, distinguishing, by location and size

    def define(self) -> str:
        joined = ", ".join(self.features)
        return f"<Subject {self.id}> is {self.name}: {joined}."


@dataclass
class Beat:
    """One visible event at a stated time inside the shot."""
    start: float
    end: float
    event: str

    def render(self) -> str:
        return f"from {self.start:.2f} to {self.end:.2f} s {self.event}"


@dataclass
class Shot:
    size: str                      # e.g. "an extreme wide shot"
    setting: str                   # where we are
    camera: str                    # "pushes in with large amplitude at slow speed"
    beats: List[Beat] = field(default_factory=list)
    subjects: List[Subject] = field(default_factory=list)
    soundscape: str = ""
    music: str = "N/A"
    style: str = "Live-action, cinematic"
    cuts: Optional[List[tuple]] = None   # [(time, description)] for in-render cuts
    duration: float = 5.17


def _clean_sound(s: str) -> str:
    """Drop the banned MOOD words - as WORDS - and clean up what is left behind.

    R2-H6: this used to be a substring replace, so "Intense wind, epic-sounding drums."
    became "In wind, -sounding drums." - the word was carved out of the middle of
    another word and left the wreckage behind. A banned word is a banned WORD; a
    hyphenated compound that merely contains one is a different word.

    R3-L1: three defects were left in it.
      * the removal left the punctuation behind: "Wind, tense, low hum." became
        "Wind, , low hum." and "wind (ominous) hum" became "wind () hum";
      * only the lower case and the title case were removed, so "EPIC" survived;
      * a word followed by a hyphen was not a word, so "cinematic-style" survived.
    """
    # the longest mood word first: "epic-sounding" must be matched as itself, not as
    # "epic" with a tail left over.
    for w in sorted(MOOD_WORDS, key=len, reverse=True):
        # a mood word is a word: it may not be glued to letters on either side. A
        # hyphen after it is consumed with it ("cinematic-style" -> "style").
        s = re.sub(r"(?<![A-Za-z])%s(?![A-Za-z])\s*-?\s*" % re.escape(w), " ", s,
                   flags=re.IGNORECASE)
    s = " ".join(s.split())
    # the wreckage: an empty pair of brackets, a doubled comma, a dangling separator
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\[\s*\]", "", s)
    s = re.sub(r"\s*,\s*,+", ", ", s)
    s = re.sub(r"^[\s,;.]+", "", s)
    s = re.sub(r"[\s,;.]+$", "", s)
    return " ".join(s.split())      # the cleanup above can leave gaps behind


def compile_prompt(shot: Shot, fl2va: bool = False) -> str:
    """Emit instruction line, blank line, then the three fields — in that order, always."""
    head = FL2VA_LINE.format(n=len(shot.cuts) + 1 if shot.cuts else 1, dur=f"{shot.duration:.2f}") if fl2va else I2VA_LINE

    # FIX 14: the card may not contradict itself. Every field that states where the camera
    # stands must say the SAME thing; a card that says "side view" in one field and
    # "toward the camera" in another is two shots, and the model reads the wrong half.
    # R2-H6: this block was pasted THREE times, so the contradiction check ran three times
    # and the camera clause was appended three times ("The camera:" x3). It runs once now.
    stated = {"size": shot.size, "camera": shot.camera, "setting": shot.setting}
    for b in shot.beats:
        stated["action"] = stated.get("action", "") + " " + b.event
    card_check.check_shot(stated, "the shot")     # raises when the card contradicts itself
    # the camera clause the card actually says - never the other half of a contradiction.
    # card_check owns the sentence, so there is ONE place that writes it (R2-OE7).
    clause_sentence = card_check.camera_clause_sentence(stated)

    parts = [f"[Shot 1] {shot.style}, {shot.size} of {shot.setting}."]
    for s in shot.subjects:                       # named permanent features (was 0/24)
        parts.append(s.define())                  # <Subject N> labels (was 0/24)
    if shot.beats:
        parts.append("During the shot " + "; ".join(b.render() for b in shot.beats) + ".")
    # R3-L1: ONE camera line. It used to be two: the card's own words, then
    # "The camera: the camera is ...", which says "the camera" twice and reads as a
    # label followed by a restatement.
    parts.append(f"The camera {shot.camera}. {clause_sentence}" if clause_sentence
                 else f"The camera {shot.camera}.")

    body = " ".join(parts)

    if shot.cuts:                                 # in-render cuts (was 0/24)
        extra = []
        for t, desc in shot.cuts:
            extra.append(f"[Shot {len(extra)+2}] At {t:06.3f}, the camera cuts to {desc}.")
        body += " " + " ".join(extra)

    # R3-L1: the soundscape is checked AFTER it is cleaned. It used to be checked
    # before, so a soundscape of only "Epic." passed the check and then compiled to
    # "overall_soundscape: ." - a prompt field with nothing in it.
    soundscape = _clean_sound(shot.soundscape)
    if not soundscape:
        raise SystemExit(
            "[prompt] the soundscape is empty once the banned mood words are removed: %r"
            % (shot.soundscape,))
    return (f"{head}\n\n"
            f"integrated_multimodal_description: {body}\n\n"
            f"overall_soundscape: {soundscape}\n\n"
            f"non_diegetic_music: {shot.music}")
