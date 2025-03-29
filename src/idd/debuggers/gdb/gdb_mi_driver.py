import os
import json
import logging, time

from idd.debuggers.gdb.idd_gdb_controller import IDDGdbController
from idd.driver import Driver

from idd.debuggers.gdb.utils import parse_gdb_line

base_response = []
regressed_response = []

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GDBMiDebugger(Driver):
    base_gdb_instance = None

    regressed_gdb_instance = None

    gdb_instances = None

    def __init__(self, base_args, base_script_file_path, regression_args, regression_script_file_path,
                 base_pid=None, regression_pid=None):
        self.base_gdb_instance = IDDGdbController(base_args, base_pid, base_script_file_path)
        self.regressed_gdb_instance = IDDGdbController(regression_args, regression_pid, regression_script_file_path)

        self.gdb_instances = { 'base': self.base_gdb_instance, 'regressed': self.regressed_gdb_instance }

        dirname = os.path.dirname(__file__)
        self.run_parallel_command("source " + os.path.join(dirname, "gdb_commands.py"))

    def run_parallel_command(self, command):
        """Executes a GDB command on both instances in parallel with proper handling."""
        logger.info(f"Running parallel command: {command}")

        # Send command to both GDB instances
        self.base_gdb_instance.write(command)
        time.sleep(0.4)  # Prevent overload
        self.regressed_gdb_instance.write(command)

        # Read outputs with crash handling
        base_result = self.base_gdb_instance.read()
        time.sleep(0.4)  # Prevent overload
        regressed_result = self.regressed_gdb_instance.read()

        if not base_result:
            logger.warning("Base GDB instance may have crashed.")
            # self.base_gdb_instance.handle_gdb_crash()

        if not regressed_result:
            logger.warning("Regressed GDB instance may have crashed.")
            # self.regressed_gdb_instance.handle_gdb_crash()

        return {
            "base": self.parse_command_output(base_result),
            "regressed": self.parse_command_output(regressed_result)
        }


    def parse_command_output(self, raw_result):
        """Parses raw GDB output from PTY into structured data."""
        response = []

        if not raw_result:
            return response  # Return an empty list if no output

        # Split into lines and process each line
        lines = raw_result.strip().split("\r\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue  # Ignore empty lines

            # Handle GDB prompts separately (e.g., interactive confirmations)
            if line.endswith("(y or n)?") or line.endswith("[y/n]"):
                logger.warning(f"GDB is waiting for user input: {line}")
                user_input = input("GDB Prompt detected. Please enter response (y/n): ").strip()
                self.write(user_input)  # Send user response back to GDB
                continue  # Skip further processing of this prompt

            # Process normal GDB output
            processed_output = parse_gdb_line(line)
            response.append(processed_output)

        return response
        #return lines
    
    def run_single_command(self, command, version):
        global base_response
        global regressed_response

        try:
            self.gdb_instances[version].write(((" {command}\n".format(command = command),), {"timeout_sec": 60}))
            raw_result = self.gdb_instances[version].recv()

        except Exception as e:
            logger.exception(f"Error executing GDB command: {command}")
            # self.handle_gdb_crash()
            return []

        return self.parse_command_output(raw_result)

    def run_single_special_command(self, command, version):
        global base_response
        global regressed_response

        try:
            self.gdb_instances[version].write(((" {command}\n".format(command = command),), {"timeout_sec": 60}))
            raw_result = self.gdb_instances[version].recv()
        except Exception as e:
            logger.exception(f"Error executing GDB command: {command}")
            self.handle_gdb_crash()
            return []

        return self.parse_special_command_output(raw_result)

    def parse_special_command_output(self, raw_result):
        response = []

        if not raw_result:
            return response  # Return an empty list if no output

        # Split into lines and process each line
        lines = raw_result.strip().split("\r\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue  # Ignore empty lines

            # Handle GDB prompts separately (e.g., interactive confirmations)
            if line.endswith("(y or n)?") or line.endswith("[y/n]"):
                logger.warning(f"GDB is waiting for user input: {line}")
                user_input = input("GDB Prompt detected. Please enter response (y/n): ").strip()
                self.write(user_input)  # Send user response back to GDB
                continue  # Skip further processing of this prompt

            # Process normal GDB output
            processed_output = parse_gdb_line(line)
            response.append(processed_output)

        return response
    
    def get_state(self, version=None):
        if version is not None:
            return self.run_single_special_command("pstate", version)
        
        # get base and regression state
        self.base_gdb_instance.write((" {command}\n".format(command = "pstate")))
        self.regressed_gdb_instance.write((" {command}\n".format(command = "pstate")))

        # wait till base is done
        raw_result = self.base_gdb_instance.read()
        base_state = self.parse_special_command_output(raw_result)
        
        # wait till regression is done
        raw_result = self.regressed_gdb_instance.read()
        regression_state = self.parse_special_command_output(raw_result)

        return { "base" : base_state, "regressed" : regression_state }

    def get_current_stack_frames(self, state):
        base_stack_frame = state['base']['stack_frame']
        regression_stack_frame = state['base']['stack_frame']

        return { "base" : base_stack_frame, "regressed" : regression_stack_frame }

    def get_current_args(self):
        base_stack_frame = self.run_single_command('pargs', 'base')
        regression_stack_frame = self.run_single_command('pargs', 'regressed')

        return { "base" : base_stack_frame, "regressed" : regression_stack_frame }

    def get_current_local_vars(self):
        base_stack_frame = self.run_single_command('plocals', 'base')
        regression_stack_frame = self.run_single_command('plocals', 'regressed')

        return { "base" : base_stack_frame, "regressed" : regression_stack_frame }

    def get_current_instructions(self):
        base_stack_frame = self.run_single_command('pasm', 'base')
        regression_stack_frame = self.run_single_command('pasm', 'regressed')

        return { "base" : base_stack_frame, "regressed" : regression_stack_frame }

    def get_current_registers(self):
        base_stack_frame = self.run_single_command('pregisters', 'base')
        regression_stack_frame = self.run_single_command('pregisters', 'regressed')

        return { "base" : base_stack_frame, "regressed" : regression_stack_frame }

    def run_parallel_raw_command(self, command):
        self.base_gdb_instance.write((("{command}\n".format(command = command),), {"timeout_sec": 60}))
        self.regressed_gdb_instance.write((("{command}\n".format(command = command),), {"timeout_sec": 60}))

        raw_result = self.base_gdb_instance.recv()
        base_result = str(self.parse_raw_command_output(raw_result))
        raw_result = self.regressed_gdb_instance.recv()
        regression_result = str(self.parse_raw_command_output(raw_result))

        return { "base": base_result, "regressed": regression_result }

    def parse_raw_command_output(self, raw_result):
        result = []
        for item in raw_result:
            result.append(str(item))
        return result

    def run_single_raw_command(self, command, version):
        self.gdb_instances[version].write((("{command}\n".format(command = command),), {"timeout_sec": 60}))
        raw_result = self.gdb_instances[version].recv()
        return self.parse_raw_command_output(raw_result)

    def terminate(self):
        print("Terminating GDB instances")
        self.base_gdb_instance.terminate()
        self.regressed_gdb_instance.terminate()
