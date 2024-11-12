import os
import lldb

from idd.driver import Driver, IDDParallelTerminate
from idd.debuggers.lldb.lldb_extensions import *
from multiprocessing import Process, Pipe


processes = []


class LLDBGetState:
    pass

class LLDBDebugger:
    is_initted = False

    lldb_instance = None

    command_interpreter = None

    lldb_instances = None

    def __init__(self, exe="", pid=None):
        self.lldb_instance = lldb.SBDebugger.Create()
        self.lldb_instance.SetAsync(False)
        self.lldb_instance.SetUseColor(False)

        self.command_interpreter = self.lldb_instance.GetCommandInterpreter()

        if exe != "":
            error = lldb.SBError()
            target = self.lldb_instance.CreateTarget(exe, "x86_64", "host", True, error)
            if not error.Success():
                raise Exception(error.GetCString())

            launch_info = lldb.SBLaunchInfo(None)
            launch_info.SetExecutableFile (target.GetExecutable(), True)
        elif pid is not None:
            self.run_single_command("attach -p " + str(pid))

        dirname = os.path.dirname(__file__)
        self.run_single_command("command script import " + os.path.join(dirname, "lldb_commands.py"))

        self.is_initted = True

    def run_single_command(self, command, *_):
        command_result = lldb.SBCommandReturnObject()
        self.command_interpreter.HandleCommand(command, command_result)

        if command_result.Succeeded():
            return command_result.GetOutput().split("\n")
        else:
            return command_result.GetError().split("\n")

    def get_state(self, *_):
        return {
            'stack_frames': self.get_current_stack_frames(),
            'locals': self.get_current_local_vars(None),
            'args': self.get_current_args(),
            'instructions': self.get_current_instructions(),
            'registers': self.get_current_registers(),
        }

    def get_current_stack_frames(self):
        target = self.lldb_instance.GetTargetAtIndex(0)
        stack_frame = get_current_stack_frame_from_target(target)
        return stack_frame

    def get_current_args(self):
        target = self.lldb_instance.GetTargetAtIndex(0)
        args = get_args_as_list(target)
        return args

    def get_current_local_vars(self, filters):
        target = self.lldb_instance.GetTargetAtIndex(0)
        target_locals = get_local_vars_as_list(target)
        if filters == 'ignore-order-declaration':
            target_locals.sort()
        return target_locals

    def get_current_instructions(self):
        target = self.lldb_instance.GetTargetAtIndex(0)
        args = get_instructions_as_list(target)
        return args

    def get_current_registers(self):
        target = self.lldb_instance.GetTargetAtIndex(0)
        args = get_registers_as_list(target)
        return args

    def get_current_calls(self):
        target = self.lldb_instance.GetTargetAtIndex(0)
        calls = get_call_instructions(target)
        return calls

    def terminate(self):
        return

    @staticmethod
    def run(lldb_args, pipe):
        lldb = LLDBDebugger(*lldb_args)
        while True:
            args, kwargs = pipe.recv()
            if isinstance(args, IDDParallelTerminate) or isinstance(kwargs, IDDParallelTerminate):
                return
            if isinstance(args, LLDBGetState) or isinstance(kwargs, LLDBGetState):
                res = lldb.get_state()
                pipe.send(res)
            else:
                res = lldb.run_single_command(*args, **kwargs)
                pipe.send(res)



class LLDBParallelDebugger(Driver):
    def __init__(self, base_args="", base_pid=None, regression_args="", regression_pid=None):
        self.base_pipe = create_LLDBDebugger_for_parallel(base_args, base_pid)
        self.regressed_pipe = create_LLDBDebugger_for_parallel(regression_args, regression_pid)

    def get_state(self, target=None):
        if target == "base":
            self.base_pipe.send((LLDBGetState(), LLDBGetState()))
            return self.base_pipe.recv()
        if target == "regressed":
            self.regressed_pipe.send((LLDBGetState(), LLDBGetState()))
            return self.regressed_pipe.recv()
        
        self.base_pipe.send((LLDBGetState(), LLDBGetState()))
        self.regressed_pipe.send((LLDBGetState(), LLDBGetState()))

        return {
            "base": self.base_pipe.recv(),
            "regressed": self.regressed_pipe.recv(),
        }

    def run_single_command(self, command, target):
        if target == "base":
            self.base_pipe.send(((command,), {}))
            return self.base_pipe.recv()
        if target == "regressed":
            self.regressed_pipe.send(((command,), {}))
            return self.regressed_pipe.recv()

    def run_parallel_command(self, command):
        self.base_pipe.send(((command,), {}))
        self.regressed_pipe.send(((command,), {}))

        return {
            "base": self.base_pipe.recv(),
            "regressed": self.regressed_pipe.recv(),
        }
    
    def terminate(self):
        terminate_all_IDDGdbController()


def terminate_all_IDDGdbController():
    for _, pipe in processes:
        pipe.send((IDDParallelTerminate(), IDDParallelTerminate()))
    for process, _ in processes:
        process.join()

def create_LLDBDebugger_for_parallel(*args):
    global processes

    parent_conn, child_conn = Pipe()
    process = Process(target=LLDBDebugger.run, args=(args, child_conn))
    processes.append((process, parent_conn))
    process.start()
    return parent_conn
