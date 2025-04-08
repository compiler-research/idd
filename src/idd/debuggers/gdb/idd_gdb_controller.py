import os
import logging
import select
import fcntl
import pty
import signal
import threading
import time

from idd.driver import IDDParallelTerminate
from idd.debuggers.gdb.utils import parse_gdb_line

from pygdbmi.gdbcontroller import GdbController

logger = logging.getLogger(__name__)

DEFAULT_GDB_LAUNCH_COMMAND = ["gdb", "--nx", "--quiet", "--interpreter=mi3"]

class IDDGdbController(GdbController):
    script_file_path = None

    def __init__(self, base_args="", base_pid=None, script_file_path=None):
        def make_fd_nonblocking(fd):
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self.pid = None
        self.script_file_path = script_file_path
        self.base_args = base_args
        self.base_pid = base_pid
        self.gdb_command = DEFAULT_GDB_LAUNCH_COMMAND[:]
        self.buffer = ""
        self.debuggee_output_buffer = []
        self.debuggee_stream_thread = None

        # Create PTYs
        self.master_fd, self.slave_fd = pty.openpty()
        self.debuggee_master_fd, self.debuggee_slave_fd = pty.openpty()
        self.debuggee_tty = os.ttyname(self.debuggee_slave_fd)

        make_fd_nonblocking(self.master_fd)
        make_fd_nonblocking(self.debuggee_master_fd)


        if base_args:
            self.gdb_command.append(base_args)
        elif base_pid:
            self.gdb_command.append(f"--pid={base_pid}")

        self.start_debuggee_output_streaming()
        self.spawn_new_gdb_subprocess()

    def spawn_new_gdb_subprocess(self):
        if hasattr(self, "pid") and self.pid:
            self.terminate()

        logger.info("Launching GDB: " + " ".join(self.gdb_command))

        self.pid = os.fork()
        if self.pid == 0:
            os.setsid()
            os.dup2(self.slave_fd, 0)
            os.dup2(self.slave_fd, 1)
            os.dup2(self.slave_fd, 2)
            os.close(self.master_fd)
            os.execvp(self.gdb_command[0], self.gdb_command)
        else:
            os.close(self.slave_fd)

            # Wait for initial GDB prompt to ensure GDB is ready
            self.read_until_prompt(timeout=2.0)

            # Assign inferior TTY to forward debuggee I/O
            self.write(f"set inferior-tty {self.debuggee_tty}")

            # Optional: read again to confirm it's accepted
            self.read_until_prompt(timeout=1.0)

            logger.info(f"GDB pid: {self.pid}")


    def write(self, command):
        os.write(self.master_fd, (command + "\n").encode())

    def read(self):
        try:
            new_data = os.read(self.master_fd, 4096).decode(errors="replace")
            self.buffer += new_data
            if "\n" in self.buffer:
                lines = self.buffer.split("\n")
                self.buffer = lines[-1]
                return "\n".join(lines[:-1])
        except BlockingIOError:
            return None
        except OSError:
            return None
        return None

    def read_until_prompt(self, timeout=0.5, grace_period=0.2) -> str:
        """
        Accumulates GDB output until the final (gdb) prompt is seen and
        no new output appears for a short grace period.
        """
        output = ""
        start_time = time.time()
        last_gdb_prompt_time = None

        while True:
            chunk = self.read()
            if chunk:
                output += chunk
                if "(gdb) " in chunk:
                    last_gdb_prompt_time = time.time()

            now = time.time()

            # Check for grace period after seeing (gdb)
            if last_gdb_prompt_time is not None:
                if now - last_gdb_prompt_time >= grace_period:
                    break

            if now - start_time > timeout:
                logger.warning("read_until_prompt() timed out")
                break

            time.sleep(0.02)

        return output


    def read_debuggee_output(self):
        data = ""
        try:
            while True:
                chunk = os.read(self.debuggee_master_fd, 4096).decode(errors="replace")
                if not chunk:
                    break
                data += chunk
        except BlockingIOError:
            pass  # No more data to read for now
        except OSError:
            return None  # Debuggee might have terminated

        return data if data else None

    def start_debuggee_output_streaming(self):
        def stream():
            logger.debug("[debuggee stream] started")
            while self.is_gdb_alive():
                output = self.read_debuggee_output()
                if output:
                    self.debuggee_output_buffer.append(output)
                    logger.debug(f"[debuggee] {output.strip()}")
                time.sleep(0.01)  # Light pause to prevent tight spin

            logger.debug("[debuggee stream] terminated")

        self.debuggee_stream_thread = threading.Thread(target=stream, daemon=True)
        self.debuggee_stream_thread.start()

    def is_gdb_alive(self):
        try:
            if self.pid:
                os.kill(self.pid, 0)
                return True
        except OSError:
            return False
        return False

    def send_input_to_debuggee(self, user_input):
        try:
            os.write(self.debuggee_master_fd, (user_input + "\n").encode())
            logger.debug(f"[send_input_to_debuggee] Sent: {user_input}")
        except OSError as e:
            logger.error(f"[send_input_to_debuggee] Failed to write input: {e}")

    def get_debuggee_output(self):
        return self.debuggee_output_buffer

    def pop_debuggee_output(self):
        output = self.debuggee_output_buffer
        self.debuggee_output_buffer = []
        return output

    def is_waiting_for_input(self):
        """Detect if the debugged process is waiting for user input based on its output."""
        if not self.debuggee_output_buffer:
            return False

        # Check last few lines of debuggee output
        recent_output = "".join(self.debuggee_output_buffer).splitlines()[-5:]
        for line in recent_output:
            line = line.strip().lower()
            if line.endswith(":") or line.endswith("?"):
                return True
            if any(keyword in line for keyword in ["cin", "scanf", "input", "enter value", "enter", "read"]):
                return True
        return False


    def terminate(self):
        if hasattr(self, "pid") and self.pid:
            logger.info(f"Terminating GDB process (PID {self.pid})")
            os.kill(self.pid, signal.SIGTERM)
            try:
                os.waitpid(self.pid, 0)
            except ChildProcessError:
                pass
            self.pid = None
