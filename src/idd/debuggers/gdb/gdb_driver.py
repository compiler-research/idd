from pygdbmi.gdbcontroller import GdbController
from pprint import pprint
from idd.driver import Driver

import io
import time
import subprocess
import selectors
import sys
import os, fcntl
import select, time
import threading, queue

base_response = ""
regressed_response = ""

base_err_response = ""
regressed_err_response = ""

class GDBDebugger(Driver):
    base_gdb_instance = None
    regressed_gdb_instance = None
    gdb_instances = None

    _base_response = ""
    _regression_response = ""
    _base_observers = []
    _regression_observers = []

    def __init__(self):
        self._base_observers = ""
        self._regression_observers = ""
        self._regression_response = ""
        self._observers = []

    @property
    def base_response(self):
        return self._base_response

    @base_response.setter
    def base_response(self, value):
        self._base_response = value
        if self._base_response != '':
            for callback in self._base_observers:
                callback(self._base_response)

    @property
    def regression_response(self):
        return self._regression_response

    @regression_response.setter
    def regression_response(self, value):
        self._regression_response = value
        if self._regression_response != '':
            for callback in self._regression_observers:
                callback(self._regression_response)

    def add_base_observer(self, callback):
        self._base_observers.append(callback)

    def add_regression_observer(self, callback):
        self._regression_observers.append(callback)

    def subprocess_readlines(self, out):
        while True:
            line = out.readline()
            if not line:
                return
            yield line

    def handle_base_err_output(self, stream, mask):
        global base_err_response

        if stream.closed:
            base_err_response = "stream is closed"

        if stream.readable():
            temp = []
            for line in self.subprocess_readlines(stream):
                temp.append(str(line.decode('utf-8')))

            base_err_response = ''.join(str(x) for x in temp)
        else:
            base_err_response = "stream not readable"

    def handle_base_output(self, stream, mask):
        global base_response

        if stream.closed:
            base_response = "stream is closed"

        if stream.readable():
            temp = []
            for line in self.subprocess_readlines(stream):
                temp.append(line.decode('utf-8'))

            # base_response =  #''.join(str(x) for x in temp)

            self.base_response = temp
        else:
            self.base_response = "stream not readable"

    def handle_regression_output(self, stream, mask):
        global regressed_response

        if stream.closed:
            regressed_response = "stream is closed"

        if stream.readable():
            temp = []
            for line in self.subprocess_readlines(stream):
                temp.append(line.decode('utf-8'))

            # regressed_response = temp #''.join(str(x) for x in temp)

            self.regression_response = temp
        else:
            self.regression_response = "stream not readable"

    def handle_regression_err_output(self, stream, mask):
        global regressed_err_response

        if stream.closed:
            regressed_err_response = "stream is closed"

        if stream.readable():
            temp = []
            stderr_response = stream.readlines()
            for item in stderr_response:
                temp.append(str(item.decode('utf-8')))

            regressed_err_response = ''.join(str(x) for x in temp)
        else:
            regressed_err_response = "stream not readable"

    def listen_base_stdout(self, gdb_instance):
        selector = selectors.DefaultSelector()
        selector.register(gdb_instance.stdout, selectors.EVENT_READ, self.handle_base_output)
        selector.register(gdb_instance.stderr, selectors.EVENT_READ, self.handle_base_err_output)

        while gdb_instance.poll() is None:
            # Wait for events and handle them with their registered callbacks
            events = selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

        return True

    def listen_regression_stdout(self, gdb_instance):
        selector = selectors.DefaultSelector()
        selector.register(gdb_instance.stdout, selectors.EVENT_READ, self.handle_regression_output)
        selector.register(gdb_instance.stderr, selectors.EVENT_READ, self.handle_regression_err_output)

        while gdb_instance.poll() is None:
            events = selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

        return True

    def process_response(self, base_response, regression_response):
        if len(regression_response) > 2 and len(base_response) > 2:
            if regression_response[len(regression_response) - 2] == "end_command\n" and base_response[len(base_response) - 2] == "end_command\n":
                return { 'base': base_response, 'regressed': regression_response }

        return None

    def __init__(self, base_args, regression_args):
        ba = ["gdb", "--args", base_args]
        self.base_gdb_instance = subprocess.Popen(ba, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

        ra = ["gdb", "--args", regression_args]
        self.regressed_gdb_instance = subprocess.Popen(ra, stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

        fcntl.fcntl(self.base_gdb_instance.stdout, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.regressed_gdb_instance.stdout, fcntl.F_SETFL, os.O_NONBLOCK)

        fcntl.fcntl(self.base_gdb_instance.stderr, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.regressed_gdb_instance.stderr, fcntl.F_SETFL, os.O_NONBLOCK)

        fcntl.fcntl(self.base_gdb_instance.stdin, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.regressed_gdb_instance.stdin, fcntl.F_SETFL, os.O_NONBLOCK)

        self.gdb_instances = { 'base': self.base_gdb_instance, 'regressed': self.regressed_gdb_instance }

        thread_base = threading.Thread(target=self.listen_base_stdout, args=(self.base_gdb_instance,))
        thread_base.start()
        thread_regressed = threading.Thread(target=self.listen_regression_stdout, args=(self.regressed_gdb_instance,))
        thread_regressed.start()

        dirname = os.path.dirname(__file__)
        self.run_parallel_raw_command("source " + os.path.join(dirname, "gdb_commands.py"))

    async def run_parallel_command(self, command):
        # self.base_response = ""
        # self.regression_response = ""

        

        await self.run_single_command(command, "base")
        await self.run_single_command(command, "regressed")

    async def run_single_command(self, command, version):
        global base_response
        global regressed_response
        
        #try:
        #raise Exception("3: " + command)
        self.gdb_instances[version].stdin.write("run-wrapper {command}\n".format(command = command).encode())
        self.gdb_instances[version].stdin.flush()
        #except Exception as ex:
        #    import traceback
        #    ex_type, ex_value, ex_traceback = sys.exc_info()
        #    # Extract unformatter stack traces as tuples
        #    trace_back = traceback.extract_tb(ex_traceback)

            # Format stacktrace
        #    stack_trace = list()

        #    for trace in trace_back:
        #        stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))

        #    print("Exception type : %s " % ex_type.__name__)
        #    print("Exception message : %s" % ex_value)
        #    print("stack trace : %s" % stack_trace)

        # temp = None

        # timeout = time.time() + 5

        # if version == "base":
        #     while True:
        #         if base_response != None and ("end_command" in base_response) or time.time() > timeout:
        #             temp = base_response
        #             temp = temp.replace("end_command\n(gdb) ", "")
        #             base_response = ""
        #             break

        # if version == "regressed":
        #     while True:
        #         if regressed_response != None and ("end_command" in regressed_response) or time.time() > timeout:
        #             temp = regressed_response
        #             temp = temp.replace("end_command\n(gdb) ", "")
        #             regressed_response = ""
        #             break

        # return temp
        #raise Exception("4: " + command)

    def run_parallel_raw_command(self, command):
        base_result = self.run_single_raw_command(command, "base")
        regression_result = self.run_single_raw_command(command, "regressed")

        return { "base": base_result, "regressed": regression_result }

    def run_single_raw_command(self, command, version):
        global base_response
        global regressed_response

        self.gdb_instances[version].stdin.write("{command}\n".format(command = command).encode())
        self.gdb_instances[version].stdin.flush()

        temp = None

        if version == "base":
            while True:
                if base_response != None:
                    temp = base_response
                    base_response = ""
                    break

        if version == "regressed":
            while True:
                if regressed_response != None:
                    temp = regressed_response
                    regressed_response = ""
                    break

        return temp
