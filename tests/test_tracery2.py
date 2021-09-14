#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for pytracery
"""
from __future__ import print_function, unicode_literals
import unittest
import json

import sys
import os.path

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)

import tracery
from tracery.modifiers import base_english

verbs = [
    "accept",
    "allow",
    "ask",
    "believe",
    "borrow",
    "break",
    "bring",
    "buy",
    "can”,”be able",
    "cancel",
    "change",
    "clean",
    "comb",
    "complain",
    "cough",
    "count",
    "cut",
    "dance",
    "draw",
    "drink",
    "drive",
    "eat",
    "explain",
    "fall",
    "fill",
    "find",
    "finish",
    "fit",
    "fix",
    "fly",
    "forget",
    "give",
    "go",
    "have",
    "hear",
    "hurt",
    "know",
    "learn",
    "leave",
    "listen",
    "live",
    "look",
    "lose",
    "make”,”do",
    "need",
    "open",
    "close",
    "shut",
    "organise",
    "pay",
    "play",
    "put",
    "rain",
    "read",
    "reply",
    "run",
    "say",
    "see",
    "sell",
    "send",
    "sign",
    "sing",
    "sit",
    "sleep",
    "smoke",
    "speak",
    "spell",
    "spend",
    "stand",
    "start”,”begin",
    "study",
    "succeed",
    "swim",
    "take",
    "talk",
    "teach",
    "tell",
    "think",
    "translate",
    "travel",
    "try",
    "turn off",
    "turn on",
    "type",
    "understand",
    "use",
    "wait",
    "wake up",
    "want",
    "watch",
    "work",
    "worry",
    "write",
]


def random_string(key):
    count = int(random.random() * random.random() * random.random() * 5) + 1
    s = ""
    for i in range(count):
        s += chr(97 + ord(key[0]) - 65)
    return s


def inQuotes(s):
    return '"' + s + '"'


def make_grammar():

    keys = list("ABCDEFGH")
    rule_grammar = tracery.Grammar(
        {
            "key": keys,
            "modifier": ["capitalize", "s", "ed"],
            "character": list(
                "aaabbcccdddddeeeeefffghhhiijklmmnooopqrrrrsssssttttuuvwxyz....,,,!!??"
            ),
            "plaintext": ["#character##plaintext#", "#character#"],
            "tagContents": ["#key#", "#key#.#modifier#"],
            "section": ["#plaintext#", "#plaintext#", "#tagContents.inTags#"],
            "rule": ["#section#", "#section##section#", "#section##section##section#"],
            "multiRuleSet": [
                "#rule.inQuotes#",
                "#multiRuleSet#,#rule.inQuotes#",
                "#multiRuleSet#,#rule.inQuotes#",
            ],
            "ruleset": [
                "#rule.inQuotes#",
                "#multiRuleSet.inBrackets#",
                "#multiRuleSet.inBrackets#",
            ],
        }
    )
    rule_grammar.modifiers["inQuotes"] = lambda x: f'"{x}"'
    rule_grammar.modifiers["inTags"] = lambda x: "\\#" + f"{x}" + "\\#"
    rule_grammar.modifiers["inBrackets"] = lambda x: "\\[" + f"{x}" + "\\]"

    def func(key):
        rules = rule_grammar.flatten("#ruleset#")
        return f"{inQuotes(key)}: {rules}"

    symbols = ",\n".join([func(key) for key in keys])

    raw = f"{{{symbols}}}"
    print(raw)
    grammar = tracery.Grammar(json.loads(raw))
    grammar.add_modifiers(base_english)
    for key in keys:
        expansions = []
        for j in range(5):
            expansions.append(grammar.flatten(f"#{key}#"))
        print(f"Expand {key}: {', '.join(expansions)}")


class TestPytracery(unittest.TestCase):
    """Common setUp and helpers"""

    def assert_starts_with(self, a, b, msg=None):
        self.assertTrue(
            a.startswith(b), msg or "{} does not start with {}".format(a, b)
        )

    def assert_ends_with(self, a, b, msg=None):
        self.assertTrue(a.endswith(b), msg or "{} does not end with {}".format(a, b))


class TestBasics(TestPytracery):
    def test_plaintext_short(self):
        make_grammar()
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()

# End of file
