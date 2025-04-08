import os, sys, pty, tty, select, threading
import platform
import lldb
from lldb import eLaunchFlagStopAtEntry

class IDDLLDBController:
    def __init__(self, exe="", pid=None):
        self.exe = exe
        self.pid = pid
        self.debugger = lldb.SBDebugger.Create()
        self.debugger.SetAsync(False)
        self.debugger.SetUseColor(False)

        error = lldb.SBError()
        self.target = self.debugger.CreateTarget(exe, platform.machine(), "host", True, error)
        if not error.Success():
            raise Exception(error.GetCString())

        # self.master_fd, self.slave_fd = pty.openpty()
        # self.slave_name = os.ttyname(self.slave_fd)
        # tty.setraw(self.master_fd)

        # self.debuggee_output = []
        # self._start_output_stream_thread()

        # self.target = self.debugger.CreateTarget(self.exe)
        # if not self.target.IsValid():
        #     raise Exception("Failed to create target")

        # self._launch_process()

    def _launch_process(self):
        launch_info = lldb.SBLaunchInfo([])
        # launch_info.SetArguments(["./tmp/main.py"], True)
        # launch_info.SetWorkingDirectory(os.getcwd())
        launch_info.SetLaunchFlags(eLaunchFlagStopAtEntry)

        launch_info.AddOpenFileAction(0, self.slave_name, read=True, write=False)  # stdin
        launch_info.AddOpenFileAction(1, self.slave_name, read=False, write=True)  # stdout
        launch_info.AddOpenFileAction(2, self.slave_name, read=False, write=True)  # stderr

        error = lldb.SBError()
        self.process = self.target.Launch(launch_info, error)

        if not error.Success():
            raise Exception(f"Launch failed: {error.GetCString()}")

    def _start_output_stream_thread(self):
        def stream_output():
            while True:
                try:
                    r, _, _ = select.select([self.master_fd], [], [], 0.1)
                    if r:
                        data = os.read(self.master_fd, 1024).decode(errors="replace")
                        self.debuggee_output.append(data)
                except OSError:
                    break

        self.output_thread = threading.Thread(target=stream_output, daemon=True)
        self.output_thread.start()

    # def write(self, command: str):
    #     """Send LLDB command as if typed in interactive shell."""
    #     if not command.endswith("\n"):
    #         command += "\n"
    #     os.write(self.master_fd, command.encode())

    def run_lldb_command(self, command: str):
        result = lldb.SBCommandReturnObject()
        self.debugger.GetCommandInterpreter().HandleCommand(command, result)
        if result.Succeeded():
            return result.GetOutput().splitlines()
        return result.GetError().splitlines()


    def send_input_to_debuggee(self, text):
        """Send input to the debugged process' stdin."""
        # if not text.endswith("\n"):
        #     text += "\n"
        # os.write(self.master_fd, text.encode())
        self.target.GetProcess().PutSTDIN(text)

    def get_debuggee_output(self):
        """Return all captured debuggee output so far."""
        # os.set_blocking(self.master_fd, False)
        # try:
        #     content = os.read(self.master_fd, 1024 * 1024 * 10).decode(errors="replace")
        # except BlockingIOError:
        #     content = ""
        # return content.splitlines()
        return (self.target.GetProcess().GetSTDOUT(1024*1024*10) + self.target.GetProcess().GetSTDERR(1024*1024*10)).splitlines()

    # def pop_output(self):
    #     """Return and clear debuggee output buffer."""
    #     output = self.debuggee_output
    #     self.debuggee_output = []
    #     return output

    def terminate(self):
        # if self.process:
        #     self.process.Kill()
        # os.close(self.master_fd)
        # os.close(self.slave_fd)
        lldb.SBDebugger.Destroy(self.debugger)
