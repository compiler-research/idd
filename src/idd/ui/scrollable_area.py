from __future__ import annotations
from textual.widgets import RichLog


class TextScrollView(RichLog):
    COMPONENT_CLASSES = {
        "box",         # Class for the main text container
        "rich-text--line",   # Class for each line of text
    }
    DEFAULT_CSS = """
    TextScrollView {
        height: 100%;
        scrollbar-size: 1 1;
    }
    """

    def __init__(self, title: str = "", component_id: str = None) -> None:
        super().__init__(name=title, auto_scroll=True, markup=True)
        self.border_title = title
        if component_id:
            self.id = component_id

    def append(self, lines: list[str]):
        self.write("\n".join(lines))

    def text(self, lines: list[str]):
        self.clear()
        self.append(lines)
