from textual.reactive import Reactive
from textual.widgets import Static, ScrollView

class ScrollableArea(ScrollView):
    """A scrollable view for displaying long text content."""

    content: Reactive[str] = Reactive("")

    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "border_title"
        self.content = text

    async def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Add the long text to the scrollable area
        static = Static(self.content)
        await self.update(static)

    async def set_text(self, text: str) -> None:
        """Set the text content of the scrollable area."""
        self.content = text
        static = Static(self.content)
        await self.update(static)

    async def append_text(self, text: str) -> None:
        """Set the text content of the scrollable area."""
        self.content += "\n"
        self.content += text
        static = Static(self.content)
        await self.update(static)

        self.window.scroll_y = self.max_scroll_y
