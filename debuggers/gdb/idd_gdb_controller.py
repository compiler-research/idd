import logging
import subprocess
import os
from distutils.spawn import find_executable
from typing import Union, List, Optional
from pygdbmi.gdbcontroller import GdbController
from pygdbmi.IoManager import IoManager
from pygdbmi.constants import (
    DEFAULT_GDB_TIMEOUT_SEC,
    DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC,
)

DEFAULT_GDB_LAUNCH_COMMAND = ["gdb", "--nx", "--quiet", "--interpreter=mi3"]
logger = logging.getLogger(__name__)

class IDDGdbController(GdbController):
    def spawn_new_gdb_subprocess(self) -> int:
        if self.gdb_process:
            logger.debug(
                "Killing current gdb subprocess (pid %d)" % self.gdb_process.pid
            )
            self.exit()

        logger.debug(f'Launching gdb: {" ".join(self.command)}')

        my_env = os.environ.copy()

        # Use pipes to the standard streams
        self.gdb_process = subprocess.Popen(
            self.command,
            shell=False,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env=my_env
        )

        self.io_manager = IoManager(
            self.gdb_process.stdin,
            self.gdb_process.stdout,
            self.gdb_process.stderr,
            self.time_to_check_for_additional_output_sec,
        )
        return self.gdb_process.pid