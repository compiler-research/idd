import os, sys, pty, tty, select, time, threading, signal
sys.path.append("/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python")

import lldb

from idd.driver import Driver
from idd.debuggers.lldb.lldb_extensions import *


class IDDLLDBController:
    def __init__(self, exe="", pid=None):
        self.exe = exe
        self.pid = pid
        self.debugger = lldb.SBDebugger.Create()
        self.debugger.SetAsync(False)

        self.master_fd, self.slave_fd = pty.openpty()
        self.slave_name = os.ttyname(self.slave_fd)
        self.ttyname = os.ttyname(self.slave_fd)


        self.debuggee_output = []
        self._start_output_stream_thread()

        self.target = self.debugger.CreateTarget(self.exe)
        if not self.target.IsValid():
            raise Exception("Failed to create target")

        self._launch_process()

    def _launch_process(self):
        launch_info = lldb.SBLaunchInfo(None)

        # Open PTY master/slave
        master_fd, slave_fd = pty.openpty()
        slave_name = os.ttyname(slave_fd)

        # Optional: put slave into raw mode (for terminal emulation)
        tty.setraw(master_fd)

        # Configure launch info
        launch_info = lldb.SBLaunchInfo([])
        # Redirect stdin/stdout/stderr using file actions
        launch_info.AddOpenFileAction(0, slave_name, True, False)  # stdin
        launch_info.AddOpenFileAction(1, slave_name, False, True)  # stdout
        launch_info.AddOpenFileAction(2, slave_name, False, True)  # stderr


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

    def send_input(self, text):
        os.write(self.master_fd, (text + "\n").encode())

    def get_output(self):
        return "".join(self.debuggee_output)

    def pop_output(self):
        output = self.debuggee_output
        self.debuggee_output = []
        return output

    def terminate(self):
        if self.process:
            self.process.Kill()
        os.close(self.master_fd)
        os.close(self.slave_fd)
        lldb.SBDebugger.Destroy(self.debugger)
