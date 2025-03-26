import os
import logging
import select, pty, signal

from idd.driver import IDDParallelTerminate
from idd.debuggers.gdb.utils import parse_gdb_line

from pygdbmi.gdbcontroller import GdbController
from pygdbmi.IoManager import IoManager
from pygdbmi.constants import (
    DEFAULT_GDB_TIMEOUT_SEC,
    DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC,
)

from multiprocessing import Process, Pipe

processes = []

DEFAULT_GDB_LAUNCH_COMMAND = ["gdb", "--nx", "--quiet", "--interpreter=mi3"]
logger = logging.getLogger(__name__)

class IDDGdbController(GdbController):
    script_file_path = None
    buffer = []

    def __init__(self, base_args="", base_pid=None, script_file_path=None):
        self.script_file_path = script_file_path
        self.master_fd, self.slave_fd = pty.openpty()  # Create a new PTY pair
        self.base_args = base_args
        self.base_pid = base_pid
        self.gdb_command = DEFAULT_GDB_LAUNCH_COMMAND[:]

        if base_args:
            self.gdb_command.append(base_args)
        elif base_pid:
            self.gdb_command.append(f"--pid={base_pid}")

        self.spawn_new_gdb_subprocess()

    def spawn_new_gdb_subprocess(self):
        """(Re)starts the GDB subprocess inside a PTY."""
        if hasattr(self, "pid") and self.pid:
            self.terminate()  # Ensure the old process is properly killed

        logger.info("Launching GDB: " + " ".join(self.gdb_command))

        self.pid = os.fork()
        if self.pid == 0:  # Child process (GDB)
            os.setsid()  # Start a new session
            os.dup2(self.slave_fd, 0)  # Redirect stdin
            os.dup2(self.slave_fd, 1)  # Redirect stdout
            os.dup2(self.slave_fd, 2)  # Redirect stderr
            os.close(self.master_fd)  # Close master in child process
            os.execvp(self.gdb_command[0], self.gdb_command)  # Start GDB
        else:  # Parent process (Controller)
            os.close(self.slave_fd)  # Close slave in parent process

        logger.info(f"GDB pid: {self.pid}")

    def write(self, command):
        """Send a command to GDB via PTY."""
        os.write(self.master_fd, (command + "\n").encode())

    def read(self):
        """Read GDB's output from PTY with buffering."""
        timeout_sec = 0.5  # Non-blocking read timeout
        ready, _, _ = select.select([self.master_fd], [], [], timeout_sec)

        if ready:
            try:
                new_data = os.read(self.master_fd, 1024).decode(errors="replace")
                self.buffer += new_data  # Append new data to buffer

                if "\n" in self.buffer:
                    lines = self.buffer #.split("\n")
                    self.buffer = lines[-1]  # Keep any incomplete line in the buffer
                    return "\n".join(lines[:-1])  # Return complete lines
            except OSError:
                return None
        return None


    def terminate(self):
        """Terminate GDB session."""
        if hasattr(self, "pid") and self.pid:
            logger.info(f"Terminating GDB process (PID {self.pid})")
            os.kill(self.pid, signal.SIGTERM)  # Graceful termination
            try:
                os.waitpid(self.pid, 0)  # Wait for process to exit
            except ChildProcessError:
                pass
            self.pid = None  # Clear PID after termination