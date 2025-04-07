from idd.driver import Driver
from idd.debuggers.lldb.lldb_controller import IDDLLDBController
from idd.debuggers.lldb.lldb_extensions import *

class LLDBNewDriver(Driver):
    def __init__(self, base_exe=None, base_pid=None, regressed_exe=None, regressed_pid=None):
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
        base_output = self.run_single_command(command, "base")
        regressed_output = self.run_single_command(command, "regressed")
        return {
            "base": base_output,
            "regressed": regressed_output
        }

    # def insert_stdin(self, text):
    #     self.base_controller.send_input_to_debuggee(text)
    #     self.regressed_controller.send_input_to_debuggee(text)

    # def insert_stdin_single(self, text, target):
    #     if target == "base":
    #         self.base_controller.send_input_to_debuggee(text)
    #     elif target == "regressed":
    #         self.regressed_controller.send_input_to_debuggee(text)

    def get_state(self, *_):
        return {
            'base' : {
                'stack_frames': self.get_current_stack_frames(),
                'locals': self.get_current_local_vars(None),
                'args': self.get_current_args(),
                'instructions': self.get_current_instructions(),
                'registers': self.get_current_registers()
            },
            'regressed' : {
                'stack_frames': self.get_current_stack_frames(),
                'locals': self.get_current_local_vars(None),
                'args': self.get_current_args(),
                'instructions': self.get_current_instructions(),
                'registers': self.get_current_registers()
            }
        }

    def get_current_stack_frames(self):
        target = self.base_controller.debugger.GetTargetAtIndex(0)
        return get_current_stack_frame_from_target(target) or []

    def get_current_args(self):
        target = self.base_controller.debugger.GetTargetAtIndex(0)
        return get_args_as_list(target) or []

    def get_current_local_vars(self, filters):
        target = self.base_controller.debugger.GetTargetAtIndex(0)
        locals = get_local_vars_as_list(target)
        if filters == 'ignore-order-declaration':
            locals.sort()
        return locals or []

    def get_current_instructions(self):
        target = self.base_controller.debugger.GetTargetAtIndex(0)
        return get_instructions_as_list(target) or []

    def get_current_registers(self):
        target = self.base_controller.debugger.GetTargetAtIndex(0)
        return get_registers_as_list(target) or []

    def terminate(self):
        self.base_controller.terminate()
        self.regressed_controller.terminate()