import os
import json

from idd.debuggers.gdb.idd_gdb_controller import create_IDDGdbController, terminate_all_IDDGdbController
from idd.driver import Driver

from idd.debuggers.gdb.utils import parse_gdb_line

base_response = []
regressed_response = []

class GDBMiDebugger(Driver):
    base_gdb_instance = None

    regressed_gdb_instance = None

    gdb_instances = None

    def __init__(self, base_args, base_script_file_path, regression_args, regression_script_file_path,
                 base_pid=None, regression_pid=None):
        self.base_gdb_instance = create_IDDGdbController(base_script_file_path)
        self.regressed_gdb_instance = create_IDDGdbController(regression_script_file_path)

        self.gdb_instances = { 'base': self.base_gdb_instance, 'regressed': self.regressed_gdb_instance }

        if base_pid is None:
            self.run_single_raw_command('file ' + base_args, 'base')
        else:
            self.run_single_raw_command('attach ' + base_pid, 'base')
        
        if regression_pid is None:
            self.run_single_raw_command('file ' + regression_args, 'regressed')
        else:
            self.run_single_raw_command('attach ' + regression_pid, 'regressed')

        dirname = os.path.dirname(__file__)
        self.run_parallel_raw_command("source " + os.path.join(dirname, "gdb_commands.py"))

    def run_parallel_command(self, command):
        # start both execution in parallel
        self.base_gdb_instance.send(((" {command}\n".format(command = command),), {"timeout_sec": 60}))
        self.regressed_gdb_instance.send(((" {command}\n".format(command = command),), {"timeout_sec": 60}))
        
        # wait till base is done
        raw_result = self.base_gdb_instance.recv()
        # parse output (base)
        base_response = self.parse_command_output(raw_result)
        
        # wait till regression is done
        raw_result = self.regressed_gdb_instance.recv()
        # parse output regression
        regressed_response = self.parse_command_output(raw_result)

        return { "base": base_response, "regressed": regressed_response }

    def parse_command_output(self, raw_result):
        response = []
        for item in raw_result:
            if item['type'] == 'console':
                input_string = str(item['payload'])
                processed_output = parse_gdb_line(input_string)
                response.append(processed_output)
        return response
    
    def run_single_command(self, command, version):
        global base_response
        global regressed_response
        
        self.gdb_instances[version].send(((" {command}\n".format(command = command),), {"timeout_sec": 60}))
        raw_result = self.gdb_instances[version].recv()

        return self.parse_command_output(raw_result)

    def run_single_special_command(self, command, version):
        global base_response
        global regressed_response

        self.gdb_instances[version].send(((" {command}\n".format(command = command),), {"timeout_sec": 60}))
        raw_result = self.gdb_instances[version].recv()

        return self.parse_special_command_output(raw_result)

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
    
    def get_state(self, version=None):
        if version is not None:
            return self.run_single_special_command("pstate", version)
        
        # get base and regression state
        self.base_gdb_instance.send(((" {command}\n".format(command = "pstate"),), {"timeout_sec": 60}))
        self.regressed_gdb_instance.send(((" {command}\n".format(command = "pstate"),), {"timeout_sec": 60}))

        # wait till base is done
        raw_result = self.base_gdb_instance.recv()
        base_state = self.parse_special_command_output(raw_result)
        
        # wait till regression is done
        raw_result = self.regressed_gdb_instance.recv()
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
        self.base_gdb_instance.send((("{command}\n".format(command = command),), {"timeout_sec": 60}))
        self.regressed_gdb_instance.send((("{command}\n".format(command = command),), {"timeout_sec": 60}))

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
        self.gdb_instances[version].send((("{command}\n".format(command = command),), {"timeout_sec": 60}))
        raw_result = self.gdb_instances[version].recv()
        return self.parse_raw_command_output(raw_result)

    def terminate(self):
        terminate_all_IDDGdbController()
