from __future__ import annotations

from textual.reactive import Reactive
from textual.widgets import Static
from textual.scroll_view import ScrollView
from textual.app import App, ComposeResult
from textual.geometry import Size
from rich.console import RenderableType
from textual.widgets import Markdown
from rich.text import Text


from textual.app import App, ComposeResult
from textual.geometry import Size
from textual.strip import Strip
from textual.scroll_view import ScrollView

from rich.segment import Segment

class TextScrollView(ScrollView):
    COMPONENT_CLASSES = {
        "box",         # Class for the main text container
        "rich-text--line",   # Class for each line of text
    }
    DEFAULT_CSS = """
    TextScrollView {
        height: 100%;
    }
    """

    def __init__(self, title = "", lines: list[str] = None, component_id: str = None) -> None:
        super().__init__()
        self.border_title = title
        self.lines = lines if lines is not None else []
        self.lines = lines
        if lines:
            self.virtual_size = Size(0, len(lines))
        else:
            self.virtual_size = Size(0, 5)

        if component_id:
            self.id = component_id

    def update_virtual_size(self) -> None:
        """Update the virtual size based on the number of lines."""
        self.virtual_size = Size(0, len(self.lines))

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""
        scroll_x, scroll_y = self.scroll_offset
        y += scroll_y

        if self.lines:
            if y >= len(self.lines):
                return Strip.blank(self.size.width)

            rich_text = Text.from_markup(self.lines[y])
            segments = list(rich_text.render(self.app.console))

            strip = Strip(segments, sum(segment.cell_length for segment in segments))
            strip = strip.crop(scroll_x, scroll_x + self.size.width)
            return strip
        return Strip.blank(self.size.width)
    
    def append(self, lines: list[str]):
        if not self.lines:
            self.lines = []

        self.lines += lines
        self.update_virtual_size()
        self.refresh(layout=True)
        self.scroll_to(y = self.max_scroll_y, speed=300)

    def text(self, lines: list[str]):
        if not self.lines:
            self.lines = []

        self.lines = lines
        self.update_virtual_size()
        self.refresh(layout=True)
        self.scroll_to(y = self.max_scroll_y, speed=300)
