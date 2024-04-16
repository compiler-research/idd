from textual import events
from textual.app import App
from textual_inputs import TextInput
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Static
from typing import Union

from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from diff_driver import DiffDriver
from ui.figlet_text import FigletText

import argparse
import sys
import rich.box

class CustomHeader(Header):
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
            "IDD", self.full_title, self.get_clock() if self.clock else ""
        )
        return header_table

    async def on_click(self, event: events.Click) -> None:
        return await super().on_click(event)
class TDiffFooter(Footer):
    """Override the default Footer for Styling"""

    def make_key_text(self) -> Text:
        """Create text containing all the keys."""
        text = Text(
            style="white on rgb(98,98,98)",
            no_wrap=True,
            overflow="ellipsis",
            justify="left",
            end="",
        )
        for binding in self.app.bindings.shown_keys:
            key_display = (
                binding.key.upper()
                if binding.key_display is None
                else binding.key_display
            )
            hovered = self.highlight_key == binding.key
            key_text = Text.assemble(
                (f" {key_display} ", "reverse" if hovered else "default on default"),
                f" {binding.description} ",
                meta={"@click": f"app.press('{binding.key}')", "key": binding.key},
            )
            text.append_text(key_text)
        return text
class DiffArea(Widget):
    """The general widget for displaying diff data."""

    value = Reactive("0")
    widget_title = "title"

    def render(self) -> RenderableType:
        return Panel(
                Align.left(FigletText(self.value), vertical="top"),
                title = self.widget_title,
                style="white on rgb(51,51,51)"
            )

class DiffDebug(App):
    current_index: Reactive[int] = Reactive(-1)
    tab_index = ["parallel_command_bar", "base_command_bar", "regression_command_bar"]
    show_bar = Reactive(False)

    common_command_result: Union[Reactive[str], str] = Reactive("")
    pframes_command_result: Union[Reactive[str], str] = Reactive("")
    plocals_command_result: Union[Reactive[str], str] = Reactive("")
    pargs_command_result: Union[Reactive[str], str] = Reactive("")
    pasm_command_result: Union[Reactive[str], str] = Reactive("")
    pregisters_command_result: Union[Reactive[str], str] = Reactive("")

    debugger_command_input_box: None
    diff_driver = DiffDriver()
    base_args = ""
    regression_args = ""

    async def set_common_command_result(self, command_result) -> None:
        if command_result:
            raw_base_contents = command_result["base"]
            raw_regression_contents = command_result["regressed"]

            await self.compare_contents(raw_base_contents, raw_regression_contents)

            state = Debugger.get_state()

            await self.set_pframes_command_result(state)
            await self.set_pargs_command_result(state)
            await self.set_plocals_command_result(state)
            await self.set_pasm_command_result(state)
            await self.set_pregisters_command_result(state)

            #calls = Debugger.get_current_calls()

    async def compare_contents(self, raw_base_contents, raw_regression_contents):
        if raw_base_contents != '' and raw_regression_contents != '':
            diff1 = self.diff_driver.get_diff(raw_base_contents, raw_regression_contents, "base")
            #await self.diff_area1.set_text(diff1)
            self.diff_area1.value = diff1

            diff2 = self.diff_driver.get_diff(raw_regression_contents, raw_base_contents, "regressed")
            #await self.diff_area2.set_text(diff2)
            self.diff_area2.value = diff2

    async def set_pframes_command_result(self, state) -> None:
        if state["base"] == None or "stack_frames" not in state["base"] or state["regressed"] == None or "stack_frames" not in state["regressed"]:
            return

        base_file_contents = state["base"]["stack_frames"]
        regressed_file_contents = state["regressed"]["stack_frames"]

        self.diff_frames1.value = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_frames2.value = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")

    async def set_plocals_command_result(self, state) -> None:
        if state["base"] == None or "locals" not in state["base"] or state["regressed"] == None or "locals" not in state["regressed"]:
            return

        base_file_contents = state["base"]["locals"]
        regressed_file_contents = state["regressed"]["locals"]

        self.diff_locals1.value = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_locals2.value = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")

    async def set_pargs_command_result(self, state) -> None:
        if state["base"] == None or "args" not in state["base"] or state["regressed"] == None or "args" not in state["regressed"]:
            return

        base_file_contents = state["base"]["args"]
        regressed_file_contents = state["regressed"]["args"]

        self.diff_args1.value = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_args2.value = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")

    async def set_pasm_command_result(self, state) -> None:
        if state["base"] == None or "instructions" not in state["base"] or state["regressed"] == None or "instructions" not in state["regressed"]:
            return

        base_file_contents = state["base"]["instructions"]
        regressed_file_contents = state["regressed"]["instructions"]

        #await self.diff_asm1.set_text(self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base"), False)
        self.diff_asm1.value = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        #await self.diff_asm2.set_text(self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed"), False)
        self.diff_asm2.value = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")

    async def set_pregisters_command_result(self, state) -> None:
        if state["base"] == None or "registers" not in state["base"] or state["regressed"] == None or "registers" not in state["regressed"]:
            return

        base_file_contents = state["base"]["registers"]
        regressed_file_contents = state["regressed"]["registers"]

        self.diff_reg1.value = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_reg2.value = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")

    async def on_load(self) -> None:
        await self.bind("q", "quit", "Quit")
        await self.bind("b", "toggle_sidebar", "Toggle sidebar")
        await self.bind("escape", "reset_focus", show=False)
        await self.bind("enter", "submit", "Submit")
        await self.bind("ctrl+i", "next_tab_index", show=False)
        await self.bind("shift+tab", "previous_tab_index", show=False)

    def watch_show_bar(self, show_bar: bool) -> None:
        """Called when show_bar changes."""
        self.bar.animate("layout_offset_x", 0 if show_bar else -40)

    async def action_reset_focus(self) -> None:
        self.current_index = -1
        await self.header.focus()

    def action_toggle_sidebar(self) -> None:
        """Called when user hits 'b' key."""
        self.show_bar = not self.show_bar

    async def action_submit(self) -> None:
        formatted = f"""
command: {self.parallel_command_bar.value}
        """

        if self.parallel_command_bar.value != "":
            result = Debugger.run_parallel_command(self.parallel_command_bar.value)
            await self.set_common_command_result(result)
            self.parallel_command_bar.value = ""

            await self.bar.update(
                Panel(formatted, title="Report", border_style="blue", box=rich.box.SQUARE)
            )

        if self.base_command_bar.value != "":
            result = Debugger.run_single_command(self.base_command_bar.value, "base")
            self.diff_area1.value = result
            self.base_command_bar.value = ""

        if self.regressed_command_bar.value != "":
            result = Debugger.run_single_command(self.regressed_command_bar.value, "regressed")
            self.diff_area2.value = result
            self.regressed_command_bar.value = ""

    async def action_next_tab_index(self) -> None:
        """Changes the focus to the next form field"""
        if self.current_index < len(self.tab_index) - 1:
            self.current_index += 1
            await getattr(self, self.tab_index[self.current_index]).focus()

    async def action_previous_tab_index(self) -> None:
        """Changes the focus to the previous form field"""
        if self.current_index > 0:
            self.current_index -= 1
            await getattr(self, self.tab_index[self.current_index]).focus()    

    async def on_mount(self) -> None:
        """Make a simple grid arrangement."""

        self.parallel_command_bar = TextInput(
            name="command",
            placeholder="Enter your command here...",
            title="Debugger Command",
        )
        # self.parallel_command_bar.on_change_handler_name = "handle_command_on_change"

        self.base_command_bar = TextInput(
            name="base_command_bar",
            placeholder="Enter your base command here...",
            title="Base Debugger Command",
        )

        self.regression_command_bar = TextInput(
            name="regression_command_bar",
            placeholder="Enter your regression command here...",
            title="Regression Debugger Command",
        )

        self.bar = Static(
            renderable=Panel(
                "", title="Report", border_style="blue", box=rich.box.SQUARE
            )
        )
        self.bar.layout_offset_x = -40
        await self.view.dock(self.bar, edge="left", size=40, z=1)

        self.header = CustomHeader()
        await self.view.dock(self.header, edge="top")
        await self.view.dock(TDiffFooter(), edge="bottom")
        await self.view.dock(self.parallel_command_bar, edge="bottom", size=3)

        self.diff_frames1 = DiffArea()
        self.diff_frames1.widget_title = "base stackframe"

        self.diff_frames2 = DiffArea()
        self.diff_frames2.widget_title = "regression stackframe"

        self.diff_locals1 = DiffArea()
        self.diff_locals1.widget_title = "base locals"

        self.diff_locals2 = DiffArea()
        self.diff_locals2.widget_title = "regression locals"

        self.diff_args1 = DiffArea()
        self.diff_args1.widget_title = "base args"

        self.diff_args2 = DiffArea()
        self.diff_args2.widget_title = "regression args"

        #self.diff_asm1 = ScrollWindow()
        self.diff_asm1 = DiffArea()
        self.diff_asm1.widget_title = "base asm"

        #self.diff_asm2 = ScrollWindow()
        self.diff_asm2 = DiffArea()
        self.diff_asm2.widget_title = "regression asm"

        self.diff_reg1 = DiffArea()
        self.diff_reg1.widget_title = "base registers"

        self.diff_reg2 = DiffArea()
        self.diff_reg2.widget_title = "regression registers"

        self.diff_area1 = DiffArea()
        #self.diff_area1.set_text("base")
        #self.diff_area1.widget_title = "base"
        self.diff_area2 = DiffArea()
        #self.diff_area2.widget_title = "regression"

        self.executable_path1 = DiffArea()
        self.executable_path1.widget_title = "base executable and arguments"
        self.executable_path1.value = args['base_args']

        self.executable_path2 = DiffArea()
        self.executable_path2.widget_title = "regression executable and arguments"
        self.executable_path2.value = args['regression_args']

        grid = await self.view.dock_grid()
        grid.add_column("leftmost", fraction=1, min_size=20)
        grid.add_column("leftmiddle", fraction=1, min_size=20)
        grid.add_column("rightmiddle", fraction=1, min_size=20)
        grid.add_column("rightmost", fraction=1, min_size=20)

        grid.add_row("1", fraction=1, max_size=10)
        grid.add_row("2", fraction=1, max_size=10)
        grid.add_row("3", fraction=1, max_size=10)
        grid.add_row("4", fraction=1, max_size=10)
        grid.add_row("5", fraction=1, max_size=10)
        grid.add_row("6", fraction=1, min_size=20, max_size=30)

        grid.add_areas(
            left1="leftmost-start|leftmiddle-end,1",
            right1="rightmiddle-start|rightmost-end,1",

            left2="leftmost-start|leftmiddle-end,2",
            right2="rightmiddle-start|rightmost-end,2",

            leftmost3="leftmost,3",
            leftmiddle3="leftmiddle,3",

            rightmiddle3="rightmiddle,3",
            rightmost3="rightmost,3",

            leftmost4 = "leftmost, 4",
            leftmiddle4 = "leftmiddle, 4",

            rightmiddle4 = "rightmiddle, 4",
            rightmost4 = "rightmost, 4",

            left5="leftmost-start|leftmiddle-end,5",
            right5="rightmiddle-start|rightmost-end,5",

            left6="leftmost-start|leftmiddle-end,6",
            right6="rightmiddle-start|rightmost-end,6"
        )

        grid.place(
            left1 = self.executable_path1,
            right1 = self.executable_path2,

            left2 = self.diff_frames1,
            right2 = self.diff_frames2,

            leftmost3 = self.diff_locals1,
            leftmiddle3 = self.diff_locals2,

            rightmiddle3 = self.diff_args1,
            rightmost3 = self.diff_args2,

            leftmost4 = self.diff_asm1,
            leftmiddle4 = self.diff_asm2,

            rightmost4 = self.diff_reg1,
            rightmiddle4 = self.diff_reg2,

            left5 = self.base_command_bar,
            right5 = self.regression_command_bar,

            left6 = self.diff_area1,
            right6 = self.diff_area2
        )

if __name__ == "__main__":
    Debugger = None

    parser = argparse.ArgumentParser(description='Diff Debug for simple debugging!')
    parser.add_argument('-c','--comparator', help='Choose a comparator', default='gdb')
    parser.add_argument('-ba','--base-args', help='Base executable args', default='[]', nargs='+')
    parser.add_argument('-ra','--regression-args', help='Regression executable args', default='[]', nargs='+')
    parser.add_argument('-r','--remote_host', help='The host of the remote server', default='localhost')
    parser.add_argument('-p','--platform', help='The platform of the remote server: macosx, linux', default='linux')
    parser.add_argument('-t','--triple', help='The target triple: x86_64-apple-macosx, x86_64-gnu-linux', default='x86_64-gnu-linux')
    parser.add_argument('-lvf','--local-vars-filter', help='Filter for the local vars: local-vars-filter', default='x86_64-gnu-linux')
    args = vars(parser.parse_args())

    comperator = args['comparator']
    ba = ' '.join(args['base_args'])
    ra = ' '.join(args['regression_args'])

    if comperator == 'gdb':
        from debuggers.gdb.gdb_mi_driver import GDBMiDebugger

        Debugger = GDBMiDebugger(ba, ra)
    elif comperator == 'lldb':
        from debuggers.lldb.lldb_driver import LLDBDebugger

        Debugger = LLDBDebugger(ba, ra)
    else:
        sys.exit("Invalid comparator set")

    dd = DiffDebug()
    dd.run()