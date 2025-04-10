import os
import json
import logging, threading

from pygdbmi import gdbmiparser

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
        self.run_parallel_command("set debuginfod enabled off")

    def run_parallel_command(self, command):
        base_result = []
        regressed_result = []

        def get_result(instance, output_holder):
            raw_result = instance.read_until_prompt()
            parsed = self.parse_command_output(raw_result)
            output_holder.append(parsed)

        # Start both receivers in parallel
        base_thread = threading.Thread(target=get_result, args=(self.base_gdb_instance, base_result))
        regressed_thread = threading.Thread(target=get_result, args=(self.regressed_gdb_instance, regressed_result))

        #self.base_gdb_instance.flush_debuggee_output()
        self.base_gdb_instance.write(command)

        #self.base_gdb_instance.flush_debuggee_output()
        self.regressed_gdb_instance.write(command)

        base_thread.start()
        regressed_thread.start()
        base_thread.join()
        regressed_thread.join()

        return {
            "base": base_result[0],
            "regressed": regressed_result[0],
        }


    def parse_command_output(self, raw_result):
        """Parses raw GDB output from PTY into structured data."""
        response = []

        if not raw_result:
            return response  # Return an empty list if no output

        # Split by carriage returns (used in PTY), but also clean up empty lines
        lines = [line.strip() for line in raw_result.strip().split("\r") if line.strip()]

        for raw_line in lines:
            try:
                parsed = gdbmiparser.parse_response(raw_line)
            except ValueError as e:
                logger.warning(f"Unparsable line from GDB: {raw_line!r} ({e})")
                continue

            if parsed["type"] == "console":
                line = str(parsed["payload"]).strip()

                if not line:
                    continue

                # Detect interactive GDB prompts
                if line.endswith("(y or n)?") or line.endswith("[y/n]"):
                    logger.warning(f"GDB is waiting for user input: {line}")
                    try:
                        user_input = input("GDB Prompt detected. Please enter response (y/n): ").strip()
                    except KeyboardInterrupt:
                        logger.warning("User cancelled GDB input prompt.")
                        user_input = "n"

                    self.write(user_input)
                    continue  # Skip this prompt line

                # Parse the cleaned line (e.g., remove MI wrappers, etc.)
                processed_output = parse_gdb_line(line)
                response.append(processed_output)

            #elif parsed["type"] in {"log", "target", "notify"}:
                # You can optionally handle these too
                #response.append(f"[{parsed['type']}] {parsed.get('payload', '')}")

            #elif parsed["type"] == "result":
                # Sometimes it's helpful to log MI command results too
                #response.append(f"[MI Result] ^{parsed.get('message', '')}")

        return response

    
    def run_single_command(self, command, version):
        global base_response
        global regressed_response

        try:
            #self.gdb_instances[version].flush_debuggee_output()
            self.gdb_instances[version].write(command)
            raw_result = self.gdb_instances[version].read_until_prompt()

        except Exception as e:
            logger.exception(f"Error executing GDB command: {command}")
            # self.handle_gdb_crash()
            return []

        return self.parse_command_output(raw_result)

    def run_single_special_command(self, command, version):
        global base_response
        global regressed_response

        try:
            #self.gdb_instances[version].flush_debuggee_output()
            self.gdb_instances[version].write(command)
            raw_result = self.gdb_instances[version].read_until_prompt()
        except Exception as e:
            logger.exception(f"Error executing GDB command: {command}")
            # self.handle_gdb_crash()
            return []

        return self.parse_special_command_output(raw_result)

    def parse_special_command_output(self, raw_result):
        response = []

        if not raw_result:
            return response  # Return an empty list if no output

        # Split by carriage returns (used in PTY), but also clean up empty lines
        lines = [line.strip() for line in raw_result.strip().split("\r") if line.strip()]

        for raw_line in lines:
            try:
                parsed = gdbmiparser.parse_response(raw_line)
            except ValueError as e:
                logger.warning(f"Unparsable line from GDB: {raw_line!r} ({e})")
                continue

            if parsed["type"] == "console":
                line = str(parsed["payload"]).strip()

                if not line:
                    continue

                # Detect interactive GDB prompts
                if line.endswith("(y or n)?") or line.endswith("[y/n]"):
                    logger.warning(f"GDB is waiting for user input: {line}")
                    try:
                        user_input = input("GDB Prompt detected. Please enter response (y/n): ").strip()
                    except KeyboardInterrupt:
                        logger.warning("User cancelled GDB input prompt.")
                        user_input = "n"

                    self.write(user_input)
                    continue  # Skip this prompt line

                # Parse the cleaned line (e.g., remove MI wrappers, etc.)
                processed_output = parse_gdb_line(line)
                try:
                    parsed_dict = json.loads(processed_output)
                except json.JSONDecodeError:
                    parsed_dict = processed_output

                if parsed_dict:
                    return parsed_dict
    
    def get_state(self, version=None):
        if version is not None:
            return self.run_single_special_command("pstate", version)

        #self.base_gdb_instance.flush_debuggee_output()
        #self.regressed_gdb_instance.flush_debuggee_output()
        # get base and regression state
        self.base_gdb_instance.write((" {command}\n".format(command = "pstate")))
        self.regressed_gdb_instance.write((" {command}\n".format(command = "pstate")))

        # wait till base is done
        raw_result = self.base_gdb_instance.read_until_prompt()
        base_state = self.parse_special_command_output(raw_result)
        
        # wait till regression is done
        raw_result = self.regressed_gdb_instance.read_until_prompt()
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

    def insert_stdin(self, text: str):
        self.base_gdb_instance.send_input_to_debuggee(text)
        self.regressed_gdb_instance.send_input_to_debuggee(text)

    def insert_stdin_single(self, text: str, target: str):
        if target == "base":
            self.base_gdb_instance.send_input_to_debuggee(text)
        if target == "regressed":
            self.regressed_gdb_instance.send_input_to_debuggee(text)

    def terminate(self):
        print("Terminating GDB instances")
        self.base_gdb_instance.terminate()
        self.regressed_gdb_instance.terminate()
