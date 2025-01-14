from __future__ import annotations
from typing import Callable, Dict, List, Optional, Union

from enum import Enum

import re
import random

basestring = (str, bytes)


class NodeType(Enum):
    RAW = -1
    TEXT = 0
    TAG = 1
    ACTION = 2


class Node:

    regexp = re.compile(r"\(([^)]+)\)")

    def __init__(
        self, parent: Union[Grammar, Node], child_index: int, settings: Dict
    ) -> None:
        self.errors = []
        if settings.get("raw", None) is None:
            self.errors.append("Empty input for node")
            settings["raw"] = ""
        if isinstance(parent, Grammar):
            self.grammar = parent
            self.parent = None
            self.depth = 0
            self.child_index = 0
        else:
            self.grammar = parent.grammar
            self.parent = parent
            self.depth = parent.depth + 1
            self.child_index = child_index
        self.raw = settings["raw"]
        self.type = settings.get("type", None)
        self.is_expanded = False

    def expand_children(self, child_rule: str, prevent_recursion: bool = False) -> None:
        self.children = []
        self.finished_text = ""

        self.child_rule = child_rule
        if self.child_rule is not None:
            sections, errors = parse(child_rule)
            self.errors.extend(errors)
            for i, section in enumerate(sections):
                node = Node(self, i, section)
                self.children.append(node)
                if not prevent_recursion:
                    node.expand(prevent_recursion)
                self.finished_text += node.finished_text
        else:
            self.errors.append("No child rule provided, can't expand children")

    def expand(self, prevent_recursion=False) -> None:
        if not self.is_expanded:
            self.is_expanded = True
            # Types of nodes
            # -1: raw, needs parsing
            #  0: Plaintext
            #  1: Tag ("#symbol.mod.mod2.mod3#" or
            #     "#[pushTarget:pushRule]symbol.mod")
            #  2: Action ("[pushTarget:pushRule], [pushTarget:POP]",
            #     more in the future)
            if self.type == NodeType.RAW:
                self.expand_children(self.raw, prevent_recursion)

            elif self.type == NodeType.TEXT:
                self.finished_text = self.raw

            elif self.type == NodeType.TAG:
                self.preactions = []
                self.postactions = []
                parsed = parse_tag(self.raw)
                self.symbol = parsed["symbol"]
                self.modifiers = parsed["modifiers"]
                for preaction in parsed["preactions"]:
                    self.preactions.append(NodeAction(self, preaction["raw"]))
                for preaction in self.preactions:
                    if preaction.type == 0:
                        self.postactions.append(preaction.create_undo())
                for preaction in self.preactions:
                    preaction.activate()
                self.finished_text = self.raw
                selected_rule = self.grammar.select_rule(self.symbol, self, self.errors)
                self.expand_children(selected_rule, prevent_recursion)

                # apply modifiers
                for mod_name in self.modifiers:
                    mod_params = []
                    if mod_name.find("(") > 0:
                        matches = self.regexp.findall(mod_name)
                        if len(matches) > 0:
                            mod_params = matches[0].split(",")
                            mod_name = mod_name[: mod_name.find("(")]
                    mod = self.grammar.modifiers.get(mod_name, None)
                    if mod is None:
                        self.errors.append("Missing modifier " + mod_name)
                        self.finished_text += "((." + mod_name + "))"
                    else:
                        self.finished_text = mod(self.finished_text, *mod_params)
                for postaction in self.postactions:
                    postaction.activate()

            elif self.type == NodeType.ACTION:
                self.action = NodeAction(self, self.raw)
                self.action.activate()
                self.finished_text = ""

    def clear_escape_chars(self) -> None:
        self.finished_text = (
            self.finished_text.replace("\\\\", "DOUBLEBACKSLASH")
            .replace("\\", "")
            .replace("DOUBLEBACKSLASH", "\\")
        )

    def __repr__(self) -> str:
        return f"{self.__class__}{self.type}('{self.raw}' d: {self.depth}')"


class ActionType(Enum):
    PUSH = 0  # [key:rule]
    POP = 1  # [key:POP]
    FUNCTION = 2  # [function(param0,param1)]


class NodeAction:  # has a 'raw' attribute
    def __init__(self, node: Node, raw: str) -> None:
        self.node = node
        sections = raw.split(":")
        self.target = sections[0]
        if len(sections) == 1:
            self.type = ActionType.FUNCTION
        else:
            self.rule = sections[1]
            if self.rule == "POP":
                self.type = ActionType.POP
            else:
                self.type = ActionType.PUSH

    def create_undo(self) -> Optional[NodeAction]:
        if self.type == ActionType.PUSH:
            return NodeAction(self.node, self.target + ":POP")
        return None

    def activate(self) -> None:
        grammar = self.node.grammar
        if self.type == ActionType.PUSH:
            self.rule_sections = self.rule.split(",")
            self.finished_rules = []
            for rule_section in self.rule_sections:
                n = Node(grammar, 0, {"type": NodeType.RAW, "raw": rule_section})
                n.expand()
                self.finished_rules.append(n.finished_text)
            grammar.push_rules(self.target, self.finished_rules)
        elif self.type == ActionType.POP:
            grammar.pop_rules(self.target)
        elif self.type == ActionType.FUNCTION:
            grammar.flatten(self.target, True)

    def __repr__(self) -> str:
        return f"{self.__class__}{self.type}('{self.node}' {self.target})"


class RuleSet:
    def __init__(self, grammar: Grammar, raw: Union[List[str], str]) -> None:
        self.raw = raw
        self.grammar = grammar
        # self.default_uses = [] not used
        if isinstance(raw, list):
            self.default_rules = raw
        elif isinstance(raw, basestring):
            self.default_rules = [raw]
        else:
            self.default_rules = []

    def select_rule(self) -> str:
        # in kate's code there's a bunch of stuff for different methods of
        # selecting a rule, none of which seem to be implemented yet! so for
        # now I'm just going to ...
        return random.choice(self.default_rules)

    def clear_state(self) -> None:
        # self.default_uses = [] not used
        pass


class Symbol:
    def __init__(self, grammar: Grammar, key: str, raw_rules: List[str]) -> None:
        self.grammar = grammar
        self.key = key
        self.raw_rules = raw_rules
        self.base_rules = RuleSet(grammar, raw_rules)
        self.clear_state()

    def clear_state(self) -> None:
        self.stack = [self.base_rules]
        self.uses: List[Dict] = []
        self.base_rules.clear_state()

    def push_rules(self, raw_rules) -> None:
        rules = RuleSet(self.grammar, raw_rules)
        self.stack.append(rules)

    def pop_rules(self) -> None:
        self.stack.pop()

    def select_rule(self, node, errors) -> str:
        self.uses.append({"node": node})
        if len(self.stack) == 0:
            errors.append(
                "The rule stack for '" + self.key + "' is empty, too many pops?"
            )
        return self.stack[-1].select_rule()

    def get_active_rules(self) -> Optional[str]:
        if len(self.stack) == 0:
            return None
        return self.stack[-1].select_rule()


class Grammar:
    def __init__(self, raw: str, settings=None) -> None:
        self.modifiers: Dict[str, Callable] = {}
        self.load_from_raw_obj(raw)
        self.errors: List[str] = []
        if settings is None:
            self.settings: Dict[str, str] = {}

    def clear_state(self) -> None:
        for val in self.symbols.values():
            val.clear_state()

    def add_modifiers(self, mods) -> None:
        # not sure what this is for yet
        for key in mods:
            self.modifiers[key] = mods[key]

    def load_from_raw_obj(self, raw) -> None:
        self.raw = raw
        self.symbols = {}
        if raw:
            self.symbols = dict((k, Symbol(self, k, v)) for k, v in raw.items())

    def create_root(self, rule: str) -> Node:
        return Node(self, 0, {"type": NodeType.RAW, "raw": rule})

    def expand(self, rule: str, allow_escape_chars: bool = False) -> Node:
        root = self.create_root(rule)
        root.expand()
        if not allow_escape_chars:
            root.clear_escape_chars()
        self.errors.extend(root.errors)
        return root

    def flatten(self, rule: str, allow_escape_chars: bool = False) -> str:
        root = self.expand(rule, allow_escape_chars)
        return root.finished_text

    def push_rules(self, key: str, raw_rules: List[str]) -> None:
        if key not in self.symbols:
            self.symbols[key] = Symbol(self, key, raw_rules)
        else:
            self.symbols[key].push_rules(raw_rules)

    def pop_rules(self, key) -> None:
        if key not in self.symbols:
            self.errors.append("Can't pop: no symbol for key " + key)
        else:
            self.symbols[key].pop_rules()

    def select_rule(self, key: str, node: Node, errors: List[str]) -> str:
        if key in self.symbols:
            return self.symbols[key].select_rule(node, errors)
        else:
            if key is None:
                key = str(None)
            self.errors.append("No symbol for " + key)
            return "((" + key + "))"


def parse_tag(tag_contents) -> Dict:
    """
    returns a dictionary with 'symbol', 'modifiers', 'preactions',
    'postactions'
    """
    parsed = dict(symbol=None, preactions=[], postactions=[], modifiers=[])
    sections, _ = parse(tag_contents)
    symbol_section = None
    for section in sections:
        if section["type"] == NodeType.TEXT:
            if symbol_section is None:
                symbol_section = section["raw"]
            else:
                raise Exception("multiple main sections in " + tag_contents)
        else:
            parsed["preactions"].append(section)
    if symbol_section is not None:
        components = symbol_section.split(".")
        parsed["symbol"] = components[0]
        parsed["modifiers"] = components[1:]
    return parsed


def parse(rule) -> tuple[List, List]:
    depth = 0
    in_tag = False
    sections = []
    escaped = False
    errors = []
    start = 0
    escaped_substring = ""
    last_escaped_char = None

    if rule is None:
        return sections, errors

    def create_section(start: int, end: int, type_: NodeType) -> None:
        if end - start < 1:
            if type_ == NodeType.TAG:
                errors.append(str(start) + ": empty tag")
            elif type_ == NodeType.ACTION:
                errors.append(str(start) + ": empty action")
        raw_substring = None
        if last_escaped_char is not None:
            raw_substring = escaped_substring + "\\" + rule[last_escaped_char + 1 : end]
        else:
            raw_substring = rule[start:end]
        sections.append({"type": type_, "raw": raw_substring})

    for i, c in enumerate(rule):
        if not escaped:
            if c == "[":
                if depth == 0 and not in_tag:
                    if start < i:
                        create_section(start, i, NodeType.TEXT)
                        last_escaped_char = None
                        escaped_substring = ""
                    start = i + 1
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0 and not in_tag:
                    create_section(start, i, NodeType.ACTION)
                    last_escaped_char = None
                    escaped_substring = ""
                    start = i + 1
            elif c == "#":
                if depth == 0:
                    if in_tag:
                        create_section(start, i, NodeType.TAG)
                        last_escaped_char = None
                        escaped_substring = ""
                        start = i + 1
                    else:
                        if start < i:
                            create_section(start, i, NodeType.TEXT)
                            last_escaped_char = None
                            escaped_substring = ""
                        start = i + 1
                    in_tag = not in_tag
            elif c == "\\":
                escaped = True
                escaped_substring = escaped_substring + rule[start:i]
                start = i + 1
                last_escaped_char = i
        else:
            escaped = False
    if start < len(rule):
        create_section(start, len(rule), NodeType.TEXT)
        last_escaped_char = None
        escaped_substring = ""

    if in_tag:
        errors.append("unclosed tag")
    if depth > 0:
        errors.append("too many [")
    if depth < 0:
        errors.append("too many ]")

    sections = [
        s for s in sections if not (s["type"] == NodeType.TEXT and len(s["raw"]) == 0)
    ]
    return sections, errors
