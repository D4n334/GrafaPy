from __future__ import annotations

import html
import re

from textual.widgets import Static

from ..panels import PanelResult

_TAG_RE = re.compile(r"<[^>]+>")
_BLOCK_TAGS_RE = re.compile(r"</(p|div|br|li|h[1-6])>", re.IGNORECASE)


def _html_to_text(raw: str) -> str:
    text = _BLOCK_TAGS_RE.sub("\n", raw)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip()


class TextPanel(Static):
    def update_result(self, result: PanelResult) -> None:
        options = result.panel.get("options", {})
        content = options.get("content", "")
        mode = options.get("mode", "markdown")
        if mode == "html":
            content = _html_to_text(content)
        self.update(content)
