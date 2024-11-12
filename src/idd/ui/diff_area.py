from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel

from textual.reactive import Reactive
from textual.widget import Widget

from ui.figlet_text import FigletText

class DiffArea(Widget):
    """The general widget for displaying diff data."""

    value = Reactive("0")
    widget_title = "title"

    def __init__(self, title ="title", value = "val", component_id: str = None):
        super().__init__()
        self.widget_title = title
        self.value = value

        if component_id:
            self.id = component_id

    def render(self) -> RenderableType:
        return Panel(
                Align.left(FigletText(self.value), vertical="top"),
                title = self.widget_title,
                style="white on rgb(51,51,51)"
            )
