import os
import json

from debuggers.gdb.idd_gdb_controller import IDDGdbController
from driver import Driver

from debuggers.gdb.utils import parse_gdb_line

base_response = []
regressed_response = []

class GDBMiDebugger(Driver):
    base_gdb_instance = None

    regressed_gdb_instance = None

    gdb_instances = None

    def __init__(self, base_args, regression_args):
        self.base_gdb_instance = IDDGdbController()
        self.regressed_gdb_instance = IDDGdbController()

        self.gdb_instances = { 'base': self.base_gdb_instance, 'regressed': self.regressed_gdb_instance }

        self.run_single_raw_command('file ' + base_args, 'base')
        self.run_single_raw_command('file ' + regression_args, 'regressed')

        dirname = os.path.dirname(__file__)
        self.run_parallel_raw_command("source " + os.path.join(dirname, "gdb_commands.py"))

    def run_parallel_command(self, command):
        base_response = self.run_single_command(command, "base")
        regressed_response = self.run_single_command(command, "regressed")

        return { "base": base_response, "regressed": regressed_response }

    def run_single_command(self, command, version):
        global base_response
        global regressed_response
        
        result = []
        raw_result = self.gdb_instances[version].write(" {command}\n".format(command = command), 2)
        
        # make sure all output is flushed
        # time.sleep(.005)
        flushed_results = self.gdb_instances[version].write("".format(command = command))
        raw_result = raw_result + flushed_results
        
        for item in raw_result:
            if item['type'] == 'console':
                input_string = str(item['payload'])
                processed_output = parse_gdb_line(input_string)

                result.append(processed_output)
        
        return result

    def run_single_special_command(self, command, version):
        global base_response
        global regressed_response

        raw_result = self.gdb_instances[version].write(" {command}\n".format(command = command), 2)
        flushed_results = self.gdb_instances[version].write("".format(command = command))
        raw_result = raw_result + flushed_results

        for item in raw_result:
            if item['type'] == 'console':
                input_string = str(item['payload'])
                processed_output = parse_gdb_line(input_string)
                parsed_dict = json.loads(processed_output)

                if parsed_dict:
                    return parsed_dict

    def get_state(self):
        base_state = self.run_single_special_command('pstate', 'base')
        regression_state = self.run_single_special_command('pstate', 'regressed')

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
        base_result = str(self.run_single_raw_command(command, "base"))
        regression_result = str(self.run_single_raw_command(command, "regressed"))

        return { "base": base_result, "regressed": regression_result }

    def run_single_raw_command(self, command, version):
        result = []
        raw_result = self.gdb_instances[version].write("{command}\n".format(command = command))

        for item in raw_result:
            result.append(str(item))

        return result
