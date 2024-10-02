import os
import lldb

from driver import Driver
from debuggers.lldb.lldb_extensions import *

base_response = None
regressed_response = None

class LLDBDebugger(Driver):
    is_initted = False

    base_lldb_instance = None
    regression_lldb_instance = None

    base_command_interpreter = None
    regression_command_interpreter = None

    lldb_instances = None

    def __init__(self, base_args, regression_args):
        self.base_lldb_instance = lldb.SBDebugger.Create()
        self.base_lldb_instance.SetAsync(False)
        self.base_lldb_instance.SetUseColor(False)
        
        self.regression_lldb_instance = lldb.SBDebugger.Create()
        self.regression_lldb_instance.SetAsync(False)
        self.regression_lldb_instance.SetUseColor(False)

        base_error = lldb.SBError()
        base_target = self.base_lldb_instance.CreateTarget(base_args, "x86_64", "host", True, base_error)
        if not base_error.Success():
            raise Exception(base_error.GetCString())

        regression_error = lldb.SBError()
        regression_target = self.regression_lldb_instance.CreateTarget(regression_args, "x86_64", "host", True, regression_error)
        if not regression_error.Success():
            raise Exception(regression_error.GetCString())

        self.base_command_interpreter = self.base_lldb_instance.GetCommandInterpreter()
        self.regression_command_interpreter = self.regression_lldb_instance.GetCommandInterpreter()

        base_launch_info = lldb.SBLaunchInfo(None)
        base_launch_info.SetExecutableFile (base_target.GetExecutable(), True)

        regression_launch_info = lldb.SBLaunchInfo(None)
        regression_launch_info.SetExecutableFile (regression_target.GetExecutable(), True)

        dirname = os.path.dirname(__file__)
        self.run_parallel_raw_command("command script import " + os.path.join(dirname, "lldb_commands.py"))

        self.is_initted = True

    def run_parallel_command(self, command):
        raw_base_response = self.run_single_command(command, "base")
        base_response = raw_base_response[0].split("\n")
        
        raw_regression_response = self.run_single_command(command, "regressed")
        regression_response = raw_regression_response[0].split("\n")

        return { "base": base_response, "regressed": regression_response }

    def run_parallel_raw_command(self, command):
        base_response = self.run_single_command(command, "base")
        regression_response = self.run_single_command(command, "regressed")

        return { "base": base_response, "regressed": regression_response }


    def run_single_command(self, command, version):
        command_result = lldb.SBCommandReturnObject()
        if version == "base":
            self.base_command_interpreter.HandleCommand(command, command_result)
        elif version == "regressed":
            self.regression_command_interpreter.HandleCommand(command, command_result)

        if command_result.Succeeded():
            return [command_result.GetOutput()]
        else:
            return [command_result.GetError()]

        return ""

    def get_state(self):
        result = {}
        base_state = {}
        regression_state = {}

        result['stack_frames'] = self.get_current_stack_frames()
        result['locals'] = self.get_current_local_vars(None)
        result['args'] = self.get_current_args()
        result['instructions'] = self.get_current_instructions()
        result['registers'] = self.get_current_registers()

        base_state['stack_frames'] = result['stack_frames']['base']
        regression_state['stack_frames'] = result['stack_frames']['regressed']

        base_state['locals'] = result['locals']['base']
        regression_state['locals'] = result['locals']['regressed']

        base_state['args'] = result['args']['base']
        regression_state['args'] = result['args']['regressed']

        base_state['instructions'] = result['instructions']['base']
        regression_state['instructions'] = result['instructions']['regressed']

        base_state['registers'] = result['registers']['base']
        regression_state['registers'] = result['registers']['regressed']

        return { "base" : base_state, "regressed" : regression_state }

    def get_current_stack_frames(self):
        base_target = self.base_lldb_instance.GetTargetAtIndex(0)
        regression_target = self.regression_lldb_instance.GetTargetAtIndex(0)

        base_stack_frame = get_current_stack_frame_from_target(base_target)
        regression_stack_frame = get_current_stack_frame_from_target(regression_target)

        return { "base" : base_stack_frame, "regressed" : regression_stack_frame }

    def get_current_args(self):
        base_target = self.base_lldb_instance.GetTargetAtIndex(0)
        regression_target = self.regression_lldb_instance.GetTargetAtIndex(0)

        base_args = get_args_as_list(base_target)
        regression_args = get_args_as_list(regression_target)

        return { "base" : base_args, "regressed" : regression_args }

    def get_current_local_vars(self, filters):
        base_target = self.base_lldb_instance.GetTargetAtIndex(0)
        regression_target = self.regression_lldb_instance.GetTargetAtIndex(0)

        base_locals = get_local_vars_as_list(base_target)
        regression_locals = get_local_vars_as_list(regression_target)

        if filters == 'ignore-order-declaration':
            base_locals.sort()
            regression_locals.sort()

        return { "base" : base_locals, "regressed" : regression_locals }

    def get_current_instructions(self):
        base_target = self.base_lldb_instance.GetTargetAtIndex(0)
        regression_target = self.regression_lldb_instance.GetTargetAtIndex(0)

        base_args = get_instructions_as_list(base_target)
        regression_args = get_instructions_as_list(regression_target)

        return { "base" : base_args, "regressed" : regression_args }

    def get_current_registers(self):
        base_target = self.base_lldb_instance.GetTargetAtIndex(0)
        regression_target = self.regression_lldb_instance.GetTargetAtIndex(0)

        base_args = get_registers_as_list(base_target)
        regression_args = get_registers_as_list(regression_target)

        return { "base" : base_args, "regressed" : regression_args }

    def get_current_calls(self):
        base_target = self.base_lldb_instance.GetTargetAtIndex(0)
        regression_target = self.regression_lldb_instance.GetTargetAtIndex(0)

        base_calls = get_call_instructions(base_target)
        regression_calls = get_call_instructions(regression_target)

        return { "base" : base_calls, "regressed" : regression_calls }
    
    def terminate(self):
        pass
