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


class CheckerBoard(ScrollView):
    COMPONENT_CLASSES = {
        "checkerboard--white-square",
        "checkerboard--black-square",
    }

    DEFAULT_CSS = """
    CheckerBoard .checkerboard--white-square {
        background: #A5BAC9;
    }
    CheckerBoard .checkerboard--black-square {
        background: #004578;
    }
    """

    def __init__(self, board_size: int) -> None:
        super().__init__()
        self.board_size = board_size
        # Each square is 4 rows and 8 columns
        self.virtual_size = Size(board_size * 8, board_size * 4)

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""

        scroll_x, scroll_y = self.scroll_offset  # The current scroll position
        y += scroll_y  # The line at the top of the widget is now `scroll_y`, not zero!
        row_index = y // 4  # four lines per row

        white = self.get_component_rich_style("checkerboard--white-square")
        black = self.get_component_rich_style("checkerboard--black-square")

        if row_index >= self.board_size:
            return Strip.blank(self.size.width)

        is_odd = row_index % 2

        segments = [
            Segment(" " * 8, black if (column + is_odd) % 2 else white)
            for column in range(self.board_size)
        ]
        strip = Strip(segments, self.board_size * 8)
        # Crop the strip so that is covers the visible area
        strip = strip.crop(scroll_x, scroll_x + self.size.width)
        return strip

class ScrollableArea(ScrollView):
    """A scrollable view for displaying long text content."""

    content: Reactive[str] = Reactive("")

    def __init__(self, board_size: int, cell_text: list[str]) -> None:
        super().__init__()
        self.board_size = board_size
        self.cell_text = cell_text
        # Each cell is 4 rows and 8 columns
        self.virtual_size = Size(board_size * 8, board_size * 4)

    def render_line(self, y: int) -> Strip:
        """Render a line of the widget. y is relative to the top of the widget."""

        scroll_x, scroll_y = self.scroll_offset  # The current scroll position
        y += scroll_y  # The line at the top of the widget is now `scroll_y`, not zero!
        row_index = y // 4  # four lines per row

        cell_style = self.get_component_rich_style("textboard--cell")

        if row_index >= self.board_size:
            return Strip.blank(self.size.width)

        segments = [
            Segment(self.cell_text[row_index * self.board_size + column].center(8), cell_style)
            for column in range(self.board_size)
        ]
        strip = Strip(segments, self.board_size * 8)
        # Crop the strip so that it covers the visible area
        strip = strip.crop(scroll_x, scroll_x + self.size.width)
        return strip


    async def set_text(self, text: str) -> None:
        """Set the text content of the scrollable area."""
        self.content = text

    async def append_text(self, text: str) -> None:
        """Set the text content of the scrollable area."""
        self.content += "\n"
        self.content += text