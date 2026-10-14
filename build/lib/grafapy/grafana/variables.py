from __future__ import annotations

import re

_VAR_RE = re.compile(r"\$\{(\w+)(?::[^}]*)?\}|\$(\w+)\b|\[\[(\w+)\]\]")
_LABEL_VALUES_RE = re.compile(r"^label_values\((?:(.+),\s*)?(\w+)\)$")


def substitute_variables(expr: str, variables: dict[str, str]) -> str:
    def replace(m: re.Match) -> str:
        name = m.group(1) or m.group(2) or m.group(3)
        return variables.get(name, m.group(0))

    return _VAR_RE.sub(replace, expr)


def parse_label_values_query(query_str: str) -> tuple[str | None, str] | None:
    match = _LABEL_VALUES_RE.match(query_str.strip())
    if not match:
        return None
    return match.groups()
