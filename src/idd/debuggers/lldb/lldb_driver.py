import os
import lldb

from idd.driver import Driver, IDDParallelTerminate
from idd.debuggers.lldb.lldb_extensions import *
from idd.debuggers.lldb.lldb_io import IOManager, ParallelFlag
from multiprocessing import Process, Pipe
from threading import Thread


processes = []


class LLDBGetState:
    pass


class LLDBStdin:
    def __init__(self, text: str):
        self.text = text

class LLDBEventHandler(Thread):
    def __init__(self, debugger):
        self.debugger = debugger
        super().__init__()

    def run(self):
        listener = self.debugger.lldb_instance.GetListener()
        event = lldb.SBEvent()
        while True:
            if listener.WaitForEvent(1, event):
                if event.GetBroadcaster().GetName() == "lldb.process":
                    if (
                        event.GetType() == lldb.SBProcess.eBroadcastBitStateChanged
                        and self.debugger.target.GetProcess().GetState() == lldb.eStateStopped
                    ):
                        output = self.debugger.run_single_command("process status")
                        if output:
                            self.debugger.fileio.append(output)
                    elif event.GetType() == lldb.SBProcess.eBroadcastBitSTDOUT:
                        output = self.debugger.target.GetProcess().GetSTDOUT(1024 * 1024 * 10).split("\n")
                        if output:
                            self.debugger.fileio.append(output)
                    elif event.GetType() == lldb.SBProcess.eBroadcastBitSTDERR:
                        output = self.debugger.target.GetProcess().GetSTDERR(1024 * 1024 * 10).split("\n")
                        if output:
                            self.debugger.fileio.append(output)

                stream = lldb.SBStream()
                event.GetDescription(stream)

        listener.Clear()

class LLDBDebugger:
    is_initted = False

    lldb_instance = None

    command_interpreter = None

    lldb_instances = None

    def __init__(self, fileio, exe="", pid=None):
        self.lldb_instance = lldb.SBDebugger.Create()
        self.lldb_instance.SetAsync(True)
        self.lldb_instance.SetUseColor(False)
        self.fileio = fileio

        self.command_interpreter = self.lldb_instance.GetCommandInterpreter()

        if exe != "":
            error = lldb.SBError()
            self.target = self.lldb_instance.CreateTarget(exe, "x86_64", "host", True, error)
            if not error.Success():
                raise Exception(error.GetCString())

            launch_info = lldb.SBLaunchInfo(None)
            launch_info.SetExecutableFile(self.target.GetExecutable(), True)
        elif pid is not None:
            self.run_single_command("attach -p " + str(pid))

        dirname = os.path.dirname(__file__)
        self.run_single_command("command script import " + os.path.join(dirname, "lldb_commands.py"))

        self.is_initted = True

        # class to handle events asynchronously
        LLDBEventHandler(self).start()
        print("Called LLDBEventHandler(self, self.fileio).start()")
        
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
    
    def insert_stdin(self, text: str):
        self.target.GetProcess().PutSTDIN(text)

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
            elif isinstance(args, LLDBStdin):
                lldb.insert_stdin(args.text)
            else:
                res = lldb.run_single_command(*args, **kwargs)
                stdout = lldb.target.GetProcess().GetSTDOUT(1024 * 1024 * 10)
                if stdout:
                    res.extend(stdout.split("\n"))
                stderr = lldb.target.GetProcess().GetSTDERR(1024 * 1024 * 10)
                if stderr:
                    res.extend(stderr.split("\n"))
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
    
    def insert_stdin(self, text: str):
        text = LLDBStdin(text)
        self.base_pipe.send((text, text))
        self.regressed_pipe.send((text, text))
    
    def insert_stdin_single(self, text: str, target: str):
        text = LLDBStdin(text)
        if target == "base":
            self.base_pipe.send((text, text))
        if target == "regressed":
            self.regressed_pipe.send((text, text))
    
    def terminate(self):
        terminate_all_IDDGdbController()

class LLDBAsyncDebugger(Driver):
    def __init__(self, fileio_base, fileio_regression, base_args="", base_pid=None, regression_args="", regression_pid=None):
        self.is_parallel = ParallelFlag()
        self.io_manager = IOManager(fileio_base, fileio_regression, self.is_parallel)
        self.base_pipe = LLDBDebugger(self.io_manager.get_base_file(), base_args, base_pid)
        self.regressed_pipe = LLDBDebugger(self.io_manager.get_regression_file(), regression_args, regression_pid)

    def get_state(self, target=None):
        self.is_parallel.is_parallel = target is None
        if target == "base":
            return self.base_pipe.get_state()
        if target == "regressed":
            return self.regressed_pipe.get_state()
        
        return {
            "base": self.base_pipe.get_state(),
            "regressed": self.regressed_pipe.get_state(),
        }

    def run_single_command(self, command, target):
        self.is_parallel.is_parallel = False
        if target == "base":
            return self.base_pipe.run_single_command(command)
        if target == "regressed":
            return self.regressed_pipe.run_single_command(command)

    def run_parallel_command(self, command):
        self.is_parallel.is_parallel = True
        return {
            "base": self.base_pipe.run_single_command(command),
            "regressed": self.regressed_pipe.run_single_command(command)
            }
    
    def insert_stdin(self, text: str):
        self.is_parallel.is_parallel = True
        self.base_pipe.insert_stdin(text)
        self.regressed_pipe.insert_stdin(text)
    
    def insert_stdin_single(self, text: str, target: str):
        self.is_parallel.is_parallel = False
        if target == "base":
            self.base_pipe.insert_stdin(text)
        if target == "regressed":
            self.regressed_pipe.insert_stdin(text)
    
    def terminate(self):
        return


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
