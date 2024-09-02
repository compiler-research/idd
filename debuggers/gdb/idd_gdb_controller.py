import logging
import subprocess

from pygdbmi.gdbcontroller import GdbController
from pygdbmi.IoManager import IoManager
from pygdbmi.constants import (
    DEFAULT_GDB_TIMEOUT_SEC,
    DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC,
)

DEFAULT_GDB_LAUNCH_COMMAND = ["gdb", "--nx", "--quiet", "--interpreter=mi3"]
logger = logging.getLogger(__name__)

class IDDGdbController(GdbController):
    script_file_path = None

    def __init__(self, script_file_path = None):
        self.script_file_path = script_file_path
        super().__init__( None, DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC)

    def spawn_new_gdb_subprocess(self) -> int:
        if self.gdb_process:
            logger.debug(
                "Killing current gdb subprocess (pid %d)" % self.gdb_process.pid
            )
            self.exit()

        if self.script_file_path:
            logger.debug(f'Configuring to run bash script: {self.script_file_path} before starting GDB')
            # The modified command will source the script and then run gdb
            self.command = ["/bin/bash", "-c", f"source {self.script_file_path} && {' '.join(self.command)}"]

        logger.debug(f'Launching gdb: {" ".join(self.command)}')

        # Use pipes to the standard streams
        self.gdb_process = subprocess.Popen(
            self.command,
            shell=False,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0
        )

        self.io_manager = IoManager(
            self.gdb_process.stdin,
            self.gdb_process.stdout,
            self.gdb_process.stderr,
            self.time_to_check_for_additional_output_sec,
        )
        return self.gdb_process.pid