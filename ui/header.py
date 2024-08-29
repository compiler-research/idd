from rich.style import Style
from rich.table import Table

from textual.widgets import Header
from textual import events

class Header(Header):
    """Override the default Header for Styling"""

    def __init__(self) -> None:
        super().__init__()
        self.tall = False
        self.style = Style(color="white", bgcolor="rgb(98,98,98)")

    def render(self) -> Table:
        header_table = Table.grid(padding=(0, 1), expand=True)
        header_table.add_column(justify="left", ratio=0, width=8)
        header_table.add_column("title", justify="center", ratio=1)
        header_table.add_column("clock", justify="right", width=8)
        header_table.add_row(
            "IDD"
        )
        return header_table

    async def on_click(self, event: events.Click) -> None:
        return await super().on_click(event)
