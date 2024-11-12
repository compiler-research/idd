import gdb
import traceback
import sys
import json

def stop_handler (event):
  plocals_result = gdb.execute("plocals", to_string=True)
  pargs_result = gdb.execute("pargs", to_string=True)
  pframe_result = gdb.execute("pframe", to_string=True)
  pasm_result = gdb.execute("pasm", to_string=True)
  pregisters_result = gdb.execute("pregisters", to_string=True)

  #print("begin_special_command")
  #print(json.dumps({ "plocals" : plocals_result, "pargs" : pargs_result, "pframe" : pframe_result, "pasm" : pasm_result, "pregisters" : pregisters_result }))
  #print("end_special_command")

# gdb.events.stop.connect(stop_handler)
# gdb.events.exited.connect (exit_handler)

class PrintState (gdb.Command):
  def __init__ (self):
    super (PrintState, self).__init__ ("pstate", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    result = {}

    locals = []
    args = []
    instructions = []
    registers = []

    length_per_ins = 4

    # get stack frame
    command_result = gdb.execute("bt", to_string=True)
    stack_frames = command_result.split('\n')
    result['stack_frames'] = stack_frames

    frame = gdb.selected_frame()
    block = frame.block()
    names = set()
    while block:
        for symbol in block:
            # get locals
            if (symbol.is_variable):
                name = symbol.name
                if not name in names:
                    locals.append('{} = {}'.format(name, symbol.value(frame)))

            # get args
            if (symbol.is_argument):
                name = symbol.name
                if not name in names:
                    args.append('{} = {}\n'.format(name, symbol.value(frame)))
        block = block.superblock

    # get instructions
    raw_instructions = frame.architecture().disassemble(frame.pc() - 4 * length_per_ins, count=10)
    for ins in raw_instructions:
      instructions.append("%s %s" % (ins['addr'], ins['asm']))

    # get registers
    arch = frame.architecture()
    for rd in arch.registers('general'):
      value = gdb.parse_and_eval(f"${rd}")
      try:
        #value = gdb.parse_and_eval("%s" % rd)
        type = value.type
        if type.code != gdb.TYPE_CODE_PTR:
            if type.code == gdb.TYPE_CODE_VOID:
                type = gdb.lookup_type('int').pointer()
            else:
                type = type.pointer()
        elif (type.target().code == gdb.TYPE_CODE_VOID
              or type.target().code == gdb.TYPE_CODE_FUNC):
            type = gdb.lookup_type('int').pointer()
        string = "%-10s" % str(rd)
        try:
            value = value.cast(type)
            value = value.dereference()
            string += value.format_string(format='x')
        except Exception as e:
            registers.append(str(e))
        finally:
            registers.append(string)
      except Exception as e:
        registers.append(str(e))

    result['locals'] = locals
    result['args'] = args
    result['instructions'] = instructions
    result['registers'] = registers

    json_result = json.dumps(result)

    print(json_result)

class PrintFrame (gdb.Command):
  def __init__ (self):
    super (PrintFrame, self).__init__ ("pframe", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    result = gdb.execute("bt", to_string=True)
    print(result)

class PrintLocals (gdb.Command):
  def __init__ (self):
    super (PrintLocals, self).__init__ ("plocals", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    frame = gdb.selected_frame()
    block = frame.block()
    names = set()
    while block:
        for symbol in block:
            if (symbol.is_variable):
                name = symbol.name
                if not name in names:
                    print('{} = {}'.format(name, symbol.value(frame)))
                    names.add(name)
        block = block.superblock

class PrintArgs (gdb.Command):
  def __init__ (self):
    super (PrintArgs, self).__init__ ("pargs", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    frame = gdb.selected_frame()
    block = frame.block()
    names = set()
    while block:
        for symbol in block:
            if (symbol.is_argument):
                name = symbol.name
                if not name in names:
                    print('{} = {}\n'.format(name, symbol.value(frame)))
                    names.add(name)
        block = block.superblock
class PrintAsm (gdb.Command):
  def __init__ (self):
    super (PrintAsm, self).__init__ ("pasm", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    str = ""
    length_per_ins = 4

    frame = gdb.selected_frame()
    instructions = frame.architecture().disassemble(frame.pc() - 4 * length_per_ins, count=10)

    for ins in instructions:
      str += "%s %s \n" % (ins['addr'], ins['asm'])

    print(str)

class PrintRegisters (gdb.Command):
  def __init__ (self):
    super (PrintRegisters, self).__init__ ("pregisters", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    string = ""
    frame = gdb.selected_frame()
    arch = frame.architecture()
    for rd in arch.registers('general'):
      value = gdb.parse_and_eval(f"${rd}")
      try:
        #value = gdb.parse_and_eval("%s" % rd)
        type = value.type
        if type.code != gdb.TYPE_CODE_PTR:
            if type.code == gdb.TYPE_CODE_VOID:
                type = gdb.lookup_type('int').pointer()
            else:
                type = type.pointer()
        elif (type.target().code == gdb.TYPE_CODE_VOID
              or type.target().code == gdb.TYPE_CODE_FUNC):
            type = gdb.lookup_type('int').pointer()
        string = "%-10s" % str(rd)
        try:
            value = value.cast(type)
            value = value.dereference()
            string += value.format_string(format='x')
        except Exception as e:
            string += str(e)
        finally:
            print(string)
      except Exception as e:
        string += str(e)

class RunWrapper (gdb.Command):
  """Greet the whole world."""

  def __init__ (self):
    super (RunWrapper, self).__init__ ("run-wrapper", gdb.COMMAND_USER)

  def invoke (self, arg, from_tty):
    try:
      result = gdb.execute(arg, to_string=True)
      print(result)
    except Exception as ex:
      ex_type, ex_value, ex_traceback = sys.exc_info()
      # Extract unformatter stack traces as tuples
      trace_back = traceback.extract_tb(ex_traceback)

      # Format stacktrace
      stack_trace = list()

      for trace in trace_back:
          stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))

      print("Exception type : %s " % ex_type.__name__)
      print("Exception message : %s" % ex_value)
      print("stack trace : %s" % stack_trace)

PrintFrame()
RunWrapper()
PrintLocals()
PrintArgs()
PrintAsm()
PrintRegisters()
PrintState()