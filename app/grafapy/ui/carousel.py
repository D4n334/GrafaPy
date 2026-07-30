from __future__ import annotations


class Carousel:
    def __init__(self, interval: float) -> None:
        self.interval = interval
        self.enabled = True
        self._advancing = False
        self._last_active_pane_id: str | None = None

    @property
    def status_text(self) -> str:
        return "carousel on" if self.enabled else "carousel off"

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def next_tab(self, tab_ids: list[str], active: str | None) -> str | None:
        if not self.enabled or len(tab_ids) < 2 or active not in tab_ids:
            return None
        next_index = (tab_ids.index(active) + 1) % len(tab_ids)
        self._advancing = True
        return tab_ids[next_index]

    def note_activation(self, pane_id: str) -> bool:
        if pane_id == self._last_active_pane_id:
            return False
        is_first_activation = self._last_active_pane_id is None
        self._last_active_pane_id = pane_id
        was_advancing = self._advancing
        self._advancing = False
        if is_first_activation or was_advancing or not self.enabled:
            return False
        self.enabled = False
        return True
