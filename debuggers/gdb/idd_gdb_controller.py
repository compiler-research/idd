import os
import logging
import subprocess
import json

from driver import IDDParallelTerminate
from debuggers.gdb.utils import parse_gdb_line

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

    def __init__(self, base_args="", base_pid=None, script_file_path = None):
        self.script_file_path = script_file_path
        super().__init__( None, DEFAULT_TIME_TO_CHECK_FOR_ADDITIONAL_OUTPUT_SEC)
        
        if base_args != "":
            self.run_single_command('file ' + base_args, 'base')
        elif base_pid != None:
            self.run_single_command('attach ' + base_pid, 'base')
        
        dirname = os.path.dirname(__file__)
        self.run_single_command("source " + os.path.join(dirname, "gdb_commands.py"))

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
    
    def parse_command_output(self, raw_result):
        response = []
        for item in raw_result:
            if item['type'] == 'console':
                input_string = str(item['payload'])
                processed_output = parse_gdb_line(input_string)
                response.append(processed_output)
        return response
    
    def parse_special_command_output(self, raw_result):
        for item in raw_result:
            if item['type'] == 'console':
                input_string = str(item['payload'])
                processed_output = parse_gdb_line(input_string)
                try:
                    parsed_dict = json.loads(processed_output)
                except json.JSONDecodeError:
                    parsed_dict = processed_output

                if parsed_dict:
                    return parsed_dict

    def get_state(self, *_):
        return self.parse_special_command_output(self.write("pstate"))


    def run_single_command(self, command, *_):
        return self.parse_command_output(self.write(command))
    
    def terminate(self):
        return



class IDDParallelGdbController:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    def run(self, pipe):
        gdb = IDDGdbController(*self.args, **self.kwargs)
        while True:
            args, kwargs = pipe.recv()
            if isinstance(args, IDDParallelTerminate) or isinstance(kwargs, IDDParallelTerminate):
                return
            res = gdb.write(*args, **kwargs)
            pipe.send(res)


def create_IDDGdbController(*args, **kwargs):
    global processes

    gdb = IDDParallelGdbController(*args, **kwargs)
    parent_conn, child_conn = Pipe()
    process = Process(target=gdb.run, args=(child_conn,))
    processes.append((process, parent_conn))
    process.start()
    return parent_conn

def terminate_all_IDDGdbController():
    for _, pipe in processes:
        pipe.send((IDDParallelTerminate(), IDDParallelTerminate()))
    for process, _ in processes:
        process.join()
