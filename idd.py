#https://stackoverflow.com/questions/59591466/how-to-import-lldb-module-for-python-on-mac
#https://stackoverflow.com/questions/46012328/import-lldb-in-python-3-on-mac

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Input
from textual.reactive import Reactive
from textual.widgets import Static
from rich.panel import Panel
from textual.containers import Grid, Container
from textual import events

from diff_driver import DiffDriver

from ui.header import Header
from ui.footer import Footer
from ui.scrollable_area import TextScrollView
from ui.diff_area import DiffArea

import argparse
import sys

class DiffDebug(App):
    CSS_PATH = "layout.tcss"

    current_index: Reactive[int] = Reactive(-1)
    tab_index = ["parallel_command_bar", "base_command_bar", "regressed_command_bar"]
    show_bar = Reactive(False)

    debugger_command_input_box: None
    diff_driver = DiffDriver()
    base_args = ""
    regression_args = ""

    diff_area1 = TextScrollView(title="Base Diff", component_id="diff-area1")
    diff_area2 = TextScrollView(title="Regression Diff", component_id = "diff-area2")
    diff_frames1 = TextScrollView(title="Base Stackframe", component_id = "diff-frames1")
    diff_frames2 = TextScrollView(title="Regression Stackframe", component_id = "diff-frames2")
    diff_locals1 = TextScrollView(title="Base Locals", component_id = "diff-locals1")
    diff_locals2 = TextScrollView(title="Regression Locals", component_id = "diff-locals2")
    diff_args1 = TextScrollView(title="Base Args", component_id = "diff-args1")
    diff_args2 = TextScrollView(title="Regression Args", component_id = "diff-args2")
    diff_asm1 = TextScrollView(title="Base Asm", component_id = "diff-asm1")
    diff_asm2 = TextScrollView(title="Regression Asm", component_id = "diff-asm2")
    diff_reg1 = TextScrollView(title="Base Registers", component_id = "diff-reg1")
    diff_reg2 = TextScrollView(title="Regression Registers", component_id = "diff-reg2")
    #executable_path1 = DiffArea(title="base executable and arguments", value="")
    #executable_path2 = DiffArea(title="regression executable and arguments", value="")

    # Command input bars
    parallel_command_bar = Input(placeholder="Enter your command here...", name="command", id="parallel-command-bar")
    base_command_bar = Input(placeholder="Enter your base command here...", name="base_command_bar", id="base-command-bar")
    regressed_command_bar = Input(placeholder="Enter your regression command here...", name="regressed_command_bar", id="regressed-command-bar")

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
            self.diff_area1.append(diff1)

            diff2 = self.diff_driver.get_diff(raw_regression_contents, raw_base_contents, "regressed")
            self.diff_area2.append(diff2)

    async def set_pframes_command_result(self, state) -> None:
        if state["base"] == None or "stack_frames" not in state["base"] or state["regressed"] == None or "stack_frames" not in state["regressed"]:
            return

        base_file_contents = state["base"]["stack_frames"]
        regressed_file_contents = state["regressed"]["stack_frames"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_frames1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_frames2.text(diff2)

    async def set_plocals_command_result(self, state) -> None:
        if state["base"] == None or "locals" not in state["base"] or state["regressed"] == None or "locals" not in state["regressed"]:
            return

        base_file_contents = state["base"]["locals"]
        regressed_file_contents = state["regressed"]["locals"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_locals1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_locals2.text(diff2)

    async def set_pargs_command_result(self, state) -> None:
        if state["base"] == None or "args" not in state["base"] or state["regressed"] == None or "args" not in state["regressed"]:
            return

        base_file_contents = state["base"]["args"]
        regressed_file_contents = state["regressed"]["args"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_args1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_args2.text(diff2)

    async def set_pasm_command_result(self, state) -> None:
        if state["base"] == None or "instructions" not in state["base"] or state["regressed"] == None or "instructions" not in state["regressed"]:
            return

        base_file_contents = state["base"]["instructions"]
        regressed_file_contents = state["regressed"]["instructions"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_asm1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_asm2.text(diff2)

    async def set_pregisters_command_result(self, state) -> None:
        if state["base"] == None or "registers" not in state["base"] or state["regressed"] == None or "registers" not in state["regressed"]:
            return

        base_file_contents = state["base"]["registers"]
        regressed_file_contents = state["regressed"]["registers"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_reg1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_reg2.text(diff2)

    async def on_load(self) -> None:
        self.bind("q", "quit", description="Quit")
        self.bind("b", "toggle_sidebar", description="Toggle sidebar")
        self.bind("escape", "reset_focus")
        self.bind("enter", "submit", description="Submit")
        self.bind("ctrl+i", "next_tab_index")
        self.bind("shift+tab", "previous_tab_index")

    def watch_show_bar(self, show_bar: bool) -> None:
        """Called when show_bar changes."""
        self.bar.animate("layout_offset_x", 0 if show_bar else -40)

    async def action_reset_focus(self) -> None:
        self.current_index = -1
        await self.header.focus()

    def action_toggle_sidebar(self) -> None:
        """Called when user hits 'b' key."""
        #self.show_bar = not self.show_bar
        #self.diff_area1.page_down()
        #self.diff_area1.target_y += self.diff_area1.max_scroll_y
        #self.diff_area1.scroll_to(y = self.diff_area1.max_scroll_y)
        #self.diff_area1.window.scroll_y = self.diff_area1.virtual_size.height - self.diff_area1.size.height

    async def action_submit(self) -> None:
        formatted = f"""
command: {self.parallel_command_bar.value}
        """

        if self.parallel_command_bar.value != "":
            result = Debugger.run_parallel_command(self.parallel_command_bar.value)
            await self.set_common_command_result(result)
            self.parallel_command_bar.value = ""

            #await self.bar.update(
            #    Panel(formatted, title="Report", border_style="blue", box=rich.box.SQUARE)
            #)

        if self.base_command_bar.value != "":
            result = Debugger.run_single_command(self.base_command_bar.value, "base")
            self.diff_area1.append(result)
            self.base_command_bar.value = ""

        if self.regressed_command_bar.value != "":
            result = Debugger.run_single_command(self.regressed_command_bar.value, "regressed")
            self.diff_area2.append(result)
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


    def compose(self) -> ComposeResult:
        """Compose the layout of the application."""

        yield Header()

        # Diff areas
        yield self.diff_frames1
        yield self.diff_frames2
        
        yield self.diff_locals1
        yield self.diff_locals2
 
        yield self.diff_args1
        yield self.diff_args2
        
        yield self.diff_asm1
        yield self.diff_asm2 

        yield self.diff_reg1
        yield self.diff_reg2
        
        #yield self.executable_path1
        #yield self.executable_path2
        
        # Compose the view
        yield self.base_command_bar
        yield self.regressed_command_bar

        yield self.diff_area1
        yield self.diff_area2

        yield self.parallel_command_bar

        yield Footer()

    @on(Input.Submitted)
    async def execute_debugger_command(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if event.control.id == 'parallel-command-bar':
            formatted = f"""
command: {self.parallel_command_bar.value}
        """

        if self.parallel_command_bar.value != "":
            result = Debugger.run_parallel_command(self.parallel_command_bar.value)
            await self.set_common_command_result(result)
            self.parallel_command_bar.value = ""

            #await self.bar.update(
            #    Panel(formatted, title="Report", border_style="blue", box=rich.box.SQUARE)
            #)

        if self.base_command_bar.value != "":
            result = Debugger.run_single_command(self.base_command_bar.value, "base")
            self.diff_area1.value = result
            self.base_command_bar.value = ""

        if self.regressed_command_bar.value != "":
            result = Debugger.run_single_command(self.regressed_command_bar.value, "regressed")
            self.diff_area2.value = result
            self.regressed_command_bar.value = ""
        a = event

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