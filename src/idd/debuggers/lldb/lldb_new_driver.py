from idd.driver import Driver
from idd.debuggers.lldb.lldb_controller import IDDLLDBController
from idd.debuggers.lldb.lldb_extensions import get_current_stack_frame_from_target,get_args_as_list,get_local_vars_as_list,get_instructions_as_list,get_registers_as_list
from concurrent.futures import ThreadPoolExecutor


class LLDBNewDriver(Driver):
    def __init__(
        self, base_exe=None, base_pid=None, regressed_exe=None, regressed_pid=None
    ):
        self.base_controller = IDDLLDBController(exe=base_exe)
        self.regressed_controller = IDDLLDBController(exe=regressed_exe)

    def run_single_command(self, command, target):
        if target == "base":
            result = self.base_controller.run_lldb_command(command)
            return result
        elif target == "regressed":
            result = self.regressed_controller.run_lldb_command(command)
            return result

    def run_parallel_command(self, command):
        with ThreadPoolExecutor() as executor:
            base_future = executor.submit(self.run_single_command, command, "base")
            regressed_future = executor.submit(
                self.run_single_command, command, "regressed"
            )
            return {
                "base": base_future.result(),
                "regressed": regressed_future.result(),
            }

    def insert_stdin(self, text):
        self.base_controller.send_input_to_debuggee(text)
        self.regressed_controller.send_input_to_debuggee(text)

    def insert_stdin_single(self, text, target):
        if target == "base":
            self.base_controller.send_input_to_debuggee(text)
        elif target == "regressed":
            self.regressed_controller.send_input_to_debuggee(text)

    def get_state(self, target=None):
        if target == "base":
            return {
                "stack_frames": self.get_current_stack_frames(self.base_controller),
                "locals": self.get_current_local_vars(self.base_controller, None),
                "args": self.get_current_args(self.base_controller),
                "instructions": self.get_current_instructions(self.base_controller),
                "registers": self.get_current_registers(self.base_controller),
            }
        if target == "regressed":
            return {
                "stack_frames": self.get_current_stack_frames(self.regressed_controller),
                "locals": self.get_current_local_vars(self.regressed_controller, None),
                "args": self.get_current_args(self.regressed_controller),
                "instructions": self.get_current_instructions(self.regressed_controller),
                "registers": self.get_current_registers(self.regressed_controller),
            }

        with ThreadPoolExecutor() as executor:
            base_future = executor.submit(self.get_state, "base")
            regressed_future = executor.submit(self.get_state, "regressed")
            return {
                "base": base_future.result(),
                "regressed": regressed_future.result(),
            }
        
    def get_console_output(self, target=None):
        if target == "base":
            return self.base_controller.get_debuggee_output()
        if target == "regressed":
            return self.regressed_controller.get_debuggee_output()
        
        with ThreadPoolExecutor() as executor:
            base_future = executor.submit(self.get_console_output, "base")
            regressed_future = executor.submit(self.get_console_output, "regressed")
            return {
                "base": base_future.result(),
                "regressed": regressed_future.result(),
            }

    def get_current_stack_frames(self, controller):
        target = controller.debugger.GetTargetAtIndex(0)
        return get_current_stack_frame_from_target(target) or []

    def get_current_args(self, controller):
        target = controller.debugger.GetTargetAtIndex(0)
        return get_args_as_list(target) or []

    def get_current_local_vars(self, controller, filters):
        target = controller.debugger.GetTargetAtIndex(0)
        locals = get_local_vars_as_list(target)
        if filters == "ignore-order-declaration":
            locals.sort()
        return locals or []

    def get_current_instructions(self, controller):
        target = controller.debugger.GetTargetAtIndex(0)
        return get_instructions_as_list(target) or []

    def get_current_registers(self, controller):
        target = controller.debugger.GetTargetAtIndex(0)
        return get_registers_as_list(target) or []

    def terminate(self):
        self.base_controller.terminate()
        self.regressed_controller.terminate()
