from idd.driver import Driver
from idd.debuggers.lldb.lldb_controller import IDDLLDBController  # your PTY-based controller
from idd.debuggers.lldb.lldb_extensions import (
    get_current_stack_frame_from_target,
    get_args_as_list,
    get_local_vars_as_list,
    get_instructions_as_list,
    get_registers_as_list,
)

class LLDBNewDriver(Driver):
    def __init__(self, base_exe=None, base_pid=None, regressed_exe=None, regressed_pid=None):
        self.base_controller = IDDLLDBController(exe=base_exe)
        self.regressed_controller = IDDLLDBController(exe=regressed_exe)

    def run_single_command(self, command, target):
        if target == "base":
            self.base_controller.write(command)
            return self.base_controller.read_until_prompt()
        elif target == "regressed":
            self.regressed_controller.write(command)
            return self.regressed_controller.read_until_prompt()

    def run_parallel_command(self, command):
        base_output = self.run_single_command(command, "base")
        regressed_output = self.run_single_command(command, "regressed")
        return {
            "base": base_output,
            "regressed": regressed_output
        }

    def insert_stdin(self, text):
        self.base_controller.send_input_to_debuggee(text)
        self.regressed_controller.send_input_to_debuggee(text)

    def insert_stdin_single(self, text, target):
        if target == "base":
            self.base_controller.send_input_to_debuggee(text)
        elif target == "regressed":
            self.regressed_controller.send_input_to_debuggee(text)

    def get_state(self, *_):
        base_output = self.base_controller.get_debuggee_output()
        regressed_output = self.regressed_controller.get_debuggee_output()
        return {
            "base": base_output,
            "regressed": regressed_output
        }

    def terminate(self):
        self.base_controller.terminate()
        self.regressed_controller.terminate()