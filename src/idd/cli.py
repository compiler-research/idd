#!/usr/bin/env python3

import argparse
import sys

from textual import on
from textual import events
from textual.app import App, ComposeResult
from textual.reactive import Reactive
from textual.widgets import Input
from textual.containers import Horizontal, Vertical

from idd.diff_driver import DiffDriver

from idd.ui.footer import Footer
from idd.ui.header import Header
from idd.ui.scrollable_area import TextScrollView


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

    def __init__(self, disable_asm=False, disable_registers=False):
        super().__init__()
        self.disable_asm = disable_asm
        self.disable_registers = disable_registers
        self.common_history = [""]
        self.common_history_index = 0
        self.base_history = [""]
        self.base_history_index = 0
        self.regressed_history = [""]
        self.regressed_history_index = 0

    async def set_command_result(self, version) -> None:
        state = Debugger.get_state(version)

        await self.set_pframes_result(state, version)
        await self.set_pargs_result(state, version)
        await self.set_plocals_result(state, version)
        if not disable_assembly:
            await self.set_pasm_result(state, version)
        if not disable_registers:
            await self.set_pregisters_result(state, version)

    async def set_common_command_result(self, command_result) -> None:
        if command_result:
            raw_base_contents = command_result["base"]
            raw_regression_contents = command_result["regressed"]

            await self.compare_contents(raw_base_contents, raw_regression_contents)

            state = Debugger.get_state()

            await self.set_pframes_command_result(state)
            await self.set_pargs_command_result(state)
            await self.set_plocals_command_result(state)
            if not disable_assembly:
                await self.set_pasm_command_result(state)
            if not disable_registers:
                await self.set_pregisters_command_result(state)

            #calls = Debugger.get_current_calls()

    async def compare_contents(self, raw_base_contents, raw_regression_contents):
        if raw_base_contents != '' and raw_regression_contents != '':
            diff1 = self.diff_driver.get_diff(raw_base_contents, raw_regression_contents, "base")
            self.diff_area1.append(diff1)

            diff2 = self.diff_driver.get_diff(raw_regression_contents, raw_base_contents, "regressed")
            self.diff_area2.append(diff2)
    
    async def set_pframes_result(self, state, version) -> None:
        if state == None or "stack_frames" not in state:
            return

        file_contents = state["stack_frames"]
        if version == "base":
            self.diff_frames1.text(file_contents)
        else:
            self.diff_frames2.text(file_contents)

    async def set_pframes_command_result(self, state) -> None:
        if state["base"] == None or "stack_frames" not in state["base"] or state["regressed"] == None or "stack_frames" not in state["regressed"]:
            return

        base_file_contents = state["base"]["stack_frames"]
        regressed_file_contents = state["regressed"]["stack_frames"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_frames1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_frames2.text(diff2)

    async def set_plocals_result(self, state, version) -> None:
        if state == None or "locals" not in state:
            return
        
        file_contents = state["locals"]
        if version == "base":
            self.diff_locals1.text(file_contents)
        else:
            self.diff_locals2.text(file_contents)


    async def set_plocals_command_result(self, state) -> None:
        if state["base"] == None or "locals" not in state["base"] or state["regressed"] == None or "locals" not in state["regressed"]:
            return

        base_file_contents = state["base"]["locals"]
        regressed_file_contents = state["regressed"]["locals"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_locals1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_locals2.text(diff2)

    async def set_pargs_result(self, state, version) -> None:
        if state == None or "args" not in state:
            return
        
        file_contents = state["args"]
        if version == "base":
            self.diff_args1.text(file_contents)
        else:
            self.diff_args2.text(file_contents)

    async def set_pargs_command_result(self, state) -> None:
        if state["base"] == None or "args" not in state["base"] or state["regressed"] == None or "args" not in state["regressed"]:
            return

        base_file_contents = state["base"]["args"]
        regressed_file_contents = state["regressed"]["args"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_args1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_args2.text(diff2)

    async def set_pasm_result(self, state, version) -> None:
        if state == None or "instructions" not in state:
            return
        
        file_contents = state["instructions"]
        if version == "base":
            self.diff_asm1.text(file_contents)
        else:
            self.diff_asm2.text(file_contents)

    async def set_pasm_command_result(self, state) -> None:
        if state["base"] == None or "instructions" not in state["base"] or state["regressed"] == None or "instructions" not in state["regressed"]:
            return

        base_file_contents = state["base"]["instructions"]
        regressed_file_contents = state["regressed"]["instructions"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_asm1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_asm2.text(diff2)

    async def set_pregisters_result(self, state, version) -> None:
        if state == None or "registers" not in state:
            return
        
        file_contents = state["registers"]
        if version == "base":
            self.diff_reg1.text(file_contents)
        else:
            self.diff_reg2.text(file_contents)

    async def set_pregisters_command_result(self, state) -> None:
        if state["base"] == None or "registers" not in state["base"] or state["regressed"] == None or "registers" not in state["regressed"]:
            return

        base_file_contents = state["base"]["registers"]
        regressed_file_contents = state["regressed"]["registers"]

        diff1 = self.diff_driver.get_diff(base_file_contents, regressed_file_contents, "base")
        self.diff_reg1.text(diff1)

        diff2 = self.diff_driver.get_diff(regressed_file_contents, base_file_contents, "regressed")
        self.diff_reg2.text(diff2)

    def compose(self) -> ComposeResult:
        """Compose the layout of the application."""
        with Vertical():
            yield Header()

            with Horizontal(classes="row1"):
                yield self.diff_frames1
                yield self.diff_frames2

            with Horizontal(classes="row2"):
                with Horizontal():
                    yield self.diff_locals1
                    yield self.diff_args1
                if not self.disable_registers and not self.disable_asm:
                    with Vertical():
                        with Horizontal():
                            yield self.diff_reg1
                        with Horizontal():
                            yield self.diff_asm1
                elif not self.disable_asm:
                    with Vertical():
                            yield self.diff_asm1
                elif not self.disable_registers:
                    with Vertical():
                            yield self.diff_reg1
                
                with Horizontal():
                    yield self.diff_locals2
                    yield self.diff_args1
                    yield self.diff_args2
                if not self.disable_registers and not self.disable_asm:
                    with Vertical():
                        with Horizontal():
                            yield self.diff_reg2
                        with Horizontal():
                            yield self.diff_asm2
                elif not self.disable_asm:
                    with Vertical():
                            yield self.diff_asm2
                elif not self.disable_registers:
                    with Vertical():
                            yield self.diff_reg2

            #yield self.executable_path1
            #yield self.executable_path2

            with Horizontal(classes="row3"):
                with Vertical():
                    yield self.base_command_bar
                with Vertical():
                    yield self.regressed_command_bar

            with Horizontal(classes="row4"):
                yield self.diff_area1
                yield self.diff_area2

            with Horizontal(classes="row5"):
                yield self.parallel_command_bar

            self.parallel_command_bar.focus()

            yield Footer()

    @on(Input.Submitted)
    async def execute_debugger_command(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if event.control.id == 'parallel-command-bar':
            if self.parallel_command_bar.value == "quit" or \
                self.parallel_command_bar.value == "exit":
                Debugger.terminate()
                exit(0)
            if self.parallel_command_bar.value != "":
                result = Debugger.run_parallel_command(self.parallel_command_bar.value)

                self.diff_area1.append([self.parallel_command_bar.value])
                self.diff_area2.append([self.parallel_command_bar.value])

                # append to history
                self.common_history.append(self.parallel_command_bar.value)
                self.common_history_index = len(self.common_history)
            
            else:
                # execute last command from history
                result = Debugger.run_parallel_command(self.common_history[-1])

                self.diff_area1.append([self.parallel_command_bar.value])
                self.diff_area2.append([self.parallel_command_bar.value])

            await self.set_common_command_result(result)

            self.parallel_command_bar.value = ""

        elif event.control.id == 'base-command-bar':
            if self.base_command_bar.value != "":
                result = Debugger.run_single_command(self.base_command_bar.value, "base")
                self.diff_area1.append([self.base_command_bar.value])
                self.diff_area1.append(result)

                # append to history
                self.base_history.append(self.base_command_bar.value)
                self.base_history_index = len(self.base_history)
            
            else:
                # execute last command from history
                result = Debugger.run_single_command(self.base_history[-1], "base")
                
                self.diff_area1.append([self.base_command_bar.value])
                self.diff_area1.append(result)

            await self.set_command_result("base")

            self.base_command_bar.value = ""

        elif event.control.id == 'regressed-command-bar':
            if self.regressed_command_bar.value != "":
                result = Debugger.run_single_command(self.regressed_command_bar.value, "regressed")
                self.diff_area2.append([self.regressed_command_bar.value])
                self.diff_area2.append(result)

                # append to history
                self.regressed_history.append(self.regressed_command_bar.value)
                self.regressed_history_index = len(self.regressed_history)
            
            else:
                # execute last command from history
                result = Debugger.run_single_command(self.regressed_history[-1], "regressed")
                self.diff_area2.append([self.regressed_command_bar.value])
                self.diff_area2.append(result)

            await self.set_command_result("regressed")
    
            self.regressed_command_bar.value = ""

    async def on_key(self, event: events.Key) -> None:
        if self.focused.id == "parallel-command-bar":
            if event.key == "up":
                self.common_history_index = (self.common_history_index - 1) % len(self.common_history)
            elif event.key == "down":
                self.common_history_index = (self.common_history_index + 1) % len(self.common_history)
            else:
                return
            
            self.parallel_command_bar.value = self.common_history[self.common_history_index]

        elif self.focused.id == "base-command-bar":
            if event.key == "up":
                self.base_history_index = (self.base_history_index - 1) % len(self.base_history)
            elif event.key == "down":
                self.base_history_index = (self.base_history_index + 1) % len(self.base_history)
            else:
                return
            
            self.base_command_bar.value = self.base_history[self.base_history_index]

        elif self.focused.id == "regressed-command-bar":
            if event.key == "up":
                self.regressed_history_index = (self.regressed_history_index - 1) % len(self.regressed_history)
            elif event.key == "down":
                self.regressed_history_index = (self.regressed_history_index + 1) % len(self.regressed_history)
            else:
                return
            
            self.regressed_command_bar.value = self.regressed_history[self.regressed_history_index]


def main() -> None:
    Debugger = None

    parser = argparse.ArgumentParser(description='Diff Debug for simple debugging!')
    parser.add_argument('-c','--comparator', help='Choose a comparator', default='gdb')
    parser.add_argument('-ba','--base-args', help='Base executable args', default="", nargs='+')
    parser.add_argument('-bpid','--base-processid', help='Base process ID', default=None)
    parser.add_argument('-bs','--base-script-path', help='Base preliminary script file path', default=None, nargs='+')
    parser.add_argument('-ra','--regression-args', help='Regression executable args', default="", nargs='+')
    parser.add_argument('-rpid','--regression-processid', help='Regression process ID', default=None)
    parser.add_argument('-rs','--regression-script-path', help='Regression preliminary script file path', default=None, nargs='+')
    parser.add_argument('-r','--remote_host', help='The host of the remote server', default='localhost')
    parser.add_argument('-p','--platform', help='The platform of the remote server: macosx, linux', default='linux')
    parser.add_argument('-t','--triple', help='The target triple: x86_64-apple-macosx, x86_64-gnu-linux', default='x86_64-gnu-linux')
    parser.add_argument('-lvf','--local-vars-filter', help='Filter for the local vars: local-vars-filter', default='x86_64-gnu-linux')
    parser.add_argument('--disable-assembly', help='Disables the assembly panel', default=False, action='store_true')
    parser.add_argument('--disable-registers', help='Disables the registers panel', default=False, action='store_true')
    args = vars(parser.parse_args())

    comparator = args['comparator']
    ba = ' '.join(args['base_args'])
    bpid = args['base_processid']
    bs = ' '.join(args['base_script_path']) if args['base_script_path'] is not None else None
    ra = ' '.join(args['regression_args'])
    rpid = args['regression_processid']
    rs = ' '.join(args['regression_script_path']) if args["regression_script_path"] is not None else None

    if comparator == 'gdb':
        from idd.debuggers.gdb.gdb_mi_driver import GDBMiDebugger

        if ba != "" and bpid is not None:
            raise Exception("Both executable and process ID given for base. This is not possible")
        if ra != "" and rpid is not None:
            raise Exception("Both executable and process ID given for regression. This is not possible")
        
        if ba == "":
            if ra == "":
                Debugger = GDBMiDebugger(ba, bs, ra, rs, base_pid=bpid, regression_pid=rpid)
            else:
                Debugger = GDBMiDebugger(ba, bs, ra, rs, base_pid=bpid)
        else:
            if ra == "":
                Debugger = GDBMiDebugger(ba, bs, ra, rs, regression_pid=rpid)
            else:
                Debugger = GDBMiDebugger(ba, bs, ra, rs)

    elif comparator == 'lldb':
        from idd.debuggers.lldb.lldb_driver import LLDBParallelDebugger

        if ba == "" or ra == "":
            raise Exception("LLDB can only be used by launching executable and executable is not provided")
        Debugger = LLDBParallelDebugger(ba, ra)
    else:
        sys.exit("Invalid comparator set")

    disable_registers = args["disable_registers"]
    disable_assembly = args["disable_assembly"]
    dd = DiffDebug(disable_assembly, disable_registers)
    dd.run()
