import lldb
import sys
import os
import time
from six import StringIO as SixStringIO
import six
import lldb_utils
import json

special_commands = ["pframe", "plocals", "pargs", "plist"]

def get_stacktrace(debugger, args, result, internal_dict):
    debugger.SetAsync(False)

    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    
    result = lldb_utils.print_stacktrace(thread)
    
    print(result)

def get_locals(debugger, args, result, internal_dict):
    debugger.SetAsync(False)

    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    

    print(args)
    #args = lldb_utils.get_locals_as_string(frame)
    #print(args)

def get_args(debugger, args, result, internal_dict):
    debugger.SetAsync(False)

    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    
    args = lldb_utils.get_args_as_string(frame)
    print(args)

def print_list(debugger, args, result, internal_dict):
    try:
        f_result = lldb.SBCommandReturnObject()
        debugger.GetCommandInterpreter().HandleCommand("f", f_result)
        f_result = f_result.__str__().split("\n")

        current_line = f_result[6]
        current_line_num = current_line[3:]
        current_line_num = current_line_num.partition(" ")[0]
        
        raw_listing = lldb.SBCommandReturnObject()
        debugger.GetCommandInterpreter().HandleCommand("list " + current_line_num, raw_listing)

        listing = raw_listing.__str__().split("\n")
        
        for i in range(0, len(listing)):
            if listing[i].startswith("   " + current_line_num):
                listing[i] = "--> " + listing[i]

        listing = '\n'.join(str(x) for x in listing)

        result = { "line_num" : current_line_num, "entries" : listing }
        result = json.dumps(result)

        print(result)
        print("end_command")
    except:
        print("exception")
        print("end_command")

def run_wrapper(debugger, args, result, internal_dict):
    debugger.SetAsync(False)

    try:
        command_result = lldb.SBCommandReturnObject()
        debugger.GetCommandInterpreter().HandleCommand(''.join(str(x) for x in args), command_result)

        print(command_result)
        print("end_command")
    except:
        print("exception")
        print("end_command")

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f lldb_commands.get_locals plocals')
    debugger.HandleCommand('command script add -f lldb_commands.get_args pargs')
    debugger.HandleCommand('command script add -f lldb_commands.get_stacktrace pframe')
    debugger.HandleCommand('command script add -f lldb_commands.print_list plist')
    debugger.HandleCommand('command script add -f lldb_commands.run_wrapper run-wrapper')