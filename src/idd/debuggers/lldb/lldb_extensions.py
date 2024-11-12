def get_current_stack_frame_from_target(target):
    process = target.GetProcess()
    thread = process.GetSelectedThread()

    result = []
    for frame in thread:
        function = frame.GetFunction()
        addr = frame.GetPCAddress()
        load_addr = addr.GetLoadAddress(target)
        function = frame.GetFunction()
        mod_name = frame.GetModule().GetFileSpec().GetFilename()

        if not function:
            # No debug info for 'function'.
            symbol = frame.GetSymbol()
            if not symbol:
                continue
            file_addr = addr.GetFileAddress()
            start_addr = symbol.GetStartAddress().GetFileAddress()
            symbol_name = symbol.GetName()
            symbol_offset = file_addr - start_addr
            result.append('  frame #{num}: {addr:#016x} {mod}`{symbol} + {offset}'.format(
                num=frame.GetFrameID(), addr=load_addr, mod=mod_name, symbol=symbol_name, offset=symbol_offset))
        else:
            # Debug info is available for 'function'.
            func_name = frame.GetFunctionName()
            file_name = frame.GetLineEntry().GetFileSpec().GetFilename()
            line_num = frame.GetLineEntry().GetLine()
            result.append('  frame #{num}: {addr:#016x} {mod}`{func} at {file}:{line} {args}'.format(
                num=frame.GetFrameID(), addr=load_addr, mod=mod_name,
                func='%s [inlined]' % func_name if frame.IsInlined() else func_name,
                file=file_name, line=line_num, args=get_args_as_string(target)))
        # result.append(str(frame))

    return result

def get_args_as_list(target):
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    args = []

    for frame in thread:
        if frame.GetFrameID() == 0:
            vars = frame.GetVariables(True, False, False, True)
            for var in vars:
                args.append("(%s)%s=%s" % (var.GetTypeName(),
                                        var.GetName(),
                                        var.GetValue()))

    return args

def get_args_as_string(target):
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    args = []

    for frame in thread:
        if frame.GetFrameID() == 0:
            vars = frame.GetVariables(True, False, False, True)
            for var in vars:
                args.append("(%s)%s=%s" % (var.GetTypeName(),
                                        var.GetName(),
                                        var.GetValue()))

    return ' '.join(str(x) for x in args)

def get_local_vars_as_list(target):
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    locals = []

    for frame in thread:
        if frame.GetFrameID() == 0:
            vars = frame.GetVariables(False, True, False, True)
            for var in vars:
                locals.append("(%s)%s=%s" % (var.GetTypeName(),
                                        var.GetName(),
                                        var.GetValue()))

    return locals

def get_instructions_as_list(target):
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    instructions = []
    for frame in thread:
        if frame.GetFrameID() == 0:
            symbol = frame.GetSymbol()
            if symbol.GetName() == "_class_initialize":
                return
            start_address = symbol.GetStartAddress().GetLoadAddress(target)
            end_address = symbol.GetEndAddress().GetLoadAddress(target)
            instruction_list = symbol.GetInstructions(target)
            previous_breakpoint_address = 0
            current_instruction_address = frame.GetPC()
            for i in instruction_list:
                address = i.GetAddress()
                load_address = address.GetLoadAddress(target)
                mnemonic = i.GetMnemonic(target)
                operand = i.GetOperands(target)
                if current_instruction_address == address:
                    instructions.append("---> %s %s" % (mnemonic, operand))
                else:
                    instructions.append("%s %s" % (mnemonic, operand))

    return instructions

def get_registers_as_list(target):
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    registers = []
    for frame in thread:
        if frame.GetFrameID() == 0:
            regs = frame.GetRegisters()[0]
            for reg in regs:
                registers.append('%s => %s' % (reg.GetName(), reg.GetValue()))

    return registers

def get_call_instructions(target):
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    call_instructions = {}
    for frame in thread:
        if frame.GetFrameID() == 0:
            symbol = frame.GetSymbol()
            instruction_list = symbol.GetInstructions(target)
            for i in instruction_list:
                address = i.GetAddress().GetLoadAddress(target)
                mnemonic = i.GetMnemonic(target)
                if mnemonic is not None and mnemonic.startswith('call'):
                    jmp_destination = int(i.GetOperands(target), 16)
                    call_instructions[address] = jmp_destination

    return call_instructions