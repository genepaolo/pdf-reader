"""Tests for tts_pronunciation word substitutions."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.tts_pronunciation import apply_pronunciation_substitutions


def test_lumian_to_loomian_basic():
    assert apply_pronunciation_substitutions("Lumian walked.") == "Loomian walked."


def test_lumian_case_insensitive():
    assert apply_pronunciation_substitutions("LUMIAN left.") == "LOOMIAN left."
    assert apply_pronunciation_substitutions("lumian said") == "Loomian said"


def test_lumian_possessive():
    assert apply_pronunciation_substitutions("Lumian's coat") == "Loomian's coat"


def test_lumian_word_boundary():
    assert apply_pronunciation_substitutions("Alumian") == "Alumian"
    assert apply_pronunciation_substitutions("x Lumian y") == "x Loomian y"


def test_disable_defaults():
    s = "Lumian walked."
    assert apply_pronunciation_substitutions(s, disable_defaults=True) == s


def test_user_rule_appended():
    rules = [{"word": "Xyz", "spoken_as": "EcksWhyZee", "case_insensitive": True}]
    out = apply_pronunciation_substitutions("Lumian and Xyz.", user_rules=rules)
    assert out == "Loomian and EcksWhyZee."
