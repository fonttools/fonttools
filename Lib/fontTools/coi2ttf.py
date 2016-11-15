#! /usr/bin/env python
"""
usage: coi2ttf input [fontfile]

    input: a text file containing COI code for some font
    fontfile: original TTF font file for given COI code. If
              passed, an updated version of the font will
              be generated using the COI code to build tables
"""

import sys
import re
import os
import copy
from fontTools.ttLib import TTFont
from fontTools.ttLib.bytecodeContainer import BytecodeContainer, Program
from fontTools.ttLib.instructions import instructionConstructor

def usage():
    print(__doc__)
    sys.exit(1)

class CallInstruction(object):
    def __init__(self, function, args):
        self.params = args
        self.function = self.get_name(function) 

    def __str__(self):
        return self.function

    def get_name(self, function):
        if function is "}":
            if 'else' in self.params:
                return "ELSE"
            else:
                return "EIF"
        else:
            return function.upper() 

class AssignInstruction(object):

    def __init__(self, addr1, addr2, op="", addr3=""):
        self.addr1 = addr1
        self.addr2 = addr2
        self.op = op
        self.addr3 = addr3

    def __str__(self):
        return self.addr1+" := "+self.addr2+self.op+self.addr3

    def is_simple_assignment(self):
        if self.op is "" and self.addr3 is "":
            return True
        else:
            return False

    def is_assigning_var(self):
        pattern = re.compile('\$..*')
        return pattern.match(self.addr2)

    def is_function(self):
        pattern = re.compile(r'.*\(.*\)')
        return pattern.match(self.addr2 + self.op + self.addr3)

    def is_unary(self):
        return self.op != "" and self.addr3 == ""
        

class Function(object):
    def __init__(self, instr, function = "", param = ""):
        self.function = function
        self.param = param
        self.instr = instr
    def __repr__(self):
        return("{0}({1})", self.function, self.param)

class Instruction(object):

    def __init__(self, mnemonic, data, line):
        self.mnemonic = mnemonic
        self.data = data
        self.line = line
    def __repr__(self):
        return("{0}[{1}], line {2}".format(self.mnemonic, self.data, self.line))

# InstructionInterpreter will translate 
class InstructionInterpreter(object):
    bytecodeInstructions = [] # contains the translated TTF so far
    push_template = "PUSH[%s]"

    pattern_markers = [
        ("scan_control",         "SCANCTRL[ ]"),
        ("scan_type",            "SCANTYPE[ ]"),
        ("freedom_vector",       "SFVTCA[{0}]"),
        ("projection_vector",    "SPVTCA[{0}]"),
        ("single_width_cutin",   "SCVTCI[ ]"),
        ("single_width_value",   "SSW[ ]"),
        (":= cvt_table",         "RCVT[ ]"),
        ("cvt_table",            "WCVTP[ ]"),
        (":= storage_area",      "RS[ ]"),
        ("storage_area",         "WS[ ]"),
        ("instruction_control",  "INSTCTRL[ ]"),
        ("RoundState_G",         "RTG[ ]"),
        ("RoundState_HG",        "RTHG[ ]"),
        ("RoundState_UG",        "RUTG[ ]"),
        ("RoundState_DG",        "RTDG[ ]"),
        ("RoundState_DTG",       "RDTG[ ]"),
        ("Super45(",             "S45ROUND[ ]"),
        ("Super(",               "SROUND[ ]"),
        ("PPEM",                 "MPPEM[ ]"),
        ("PointSize",            "MPS[ ]"),
        ("GS[auto_flip] := true","FLIPON[ ]"),
        ("GS[auto_flip] := false","FLIPOFF[ ]"),
        ("GS[rp0]",              "SRP0[ ]"),
        ("GS[rp1]",              "SRP1[ ]"),
        ("GS[rp2]",              "SRP2[ ]"),
        ("max(",                 "MAX[ ]"),
        ("min(",                 "MIN[ ]")
    ]

    operators = {
        "+": "ADD",
        "-": "SUB",
        "*": "MUL",
        "/": "DIV",
        "GE": "GTEQ",
        "LE": "LTEQ",
        "NE": "NEQ",
    }
    
    def print_bytecode(self):
        for line in self.bytecodeInstructions: 
            print line
        print("")

    def get_binary_op(self, op):
        return self.operators.get(op, op)

    def clear(self):
        del self.bytecodeInstructions[:]

    def parse_function(self, f):
        ff = f.split("(")
        function_name = ff[0]
        if "_" in function_name:
            fn = function_name.split("_")[0]
            p = function_name.split("_")[1]
            return Function(function = fn,
                     param = p,
                     instr = fn + "["+p+"]")
        else:
            if (len(ff) > 1):
                return Function(instr = function_name+"[ ]",
                                param = ff[1][:-1])
            else:
                return Function(instr = function_name+"[ ]")

    def parse_assignment(self, line):
        instr = line
        for pattern, instruction in self.pattern_markers:
            if pattern in line:
                instr = instruction.format(line.split()[-1])
                break
        return instr

    def split_line(self, line):
        parts = line.split()
        try:
            parts.remove(':=')
            if len(parts) > 3:
                assignInstr = AssignInstruction(parts[0], parts[1], parts[2], parts[3])
            elif len(parts) > 2:
                assignInstr = AssignInstruction(parts[0], parts[1], parts[2])
            else:
                assignInstr = AssignInstruction(parts[0], parts[1])
            return assignInstr;
        except:
            callInstr = CallInstruction(parts[0], parts[1:])
            return callInstr

    def parseInstruction(self, instruction_line):
        instruction = self.split_line(instruction_line)

        if type(instruction) is AssignInstruction:
            if instruction.addr1.startswith("$"):
                if instruction.is_simple_assignment():
                    if instruction.is_function():
                        instr = [self.parse_function(instruction.addr2)]
                    else:
                        if instruction.is_assigning_var():
                            instr = [instruction.__str__()]
                        else:
                            instr = ["PUSH["+instruction.addr2+"]"]
                        if instruction_line != self.parse_assignment(instruction_line):
                            instr = [self.parse_assignment(instruction_line)]
                else:
                    if instruction.is_function():
                         # assume binary op
                         fn = self.parse_function(instruction.addr2)
                         op1 = fn.param
                         op2 = instruction.op[:-1]
                         # TODO we may not have the right things on the stack
                         instr = [self.push_template % op1, self.push_template % op2,
                                  fn.instr.upper()]
                    elif instruction.is_unary():
                        instr = [instruction.addr2+"[ ]"]
                    else:
                        operator = self.get_binary_op(instruction.op)
                        instr = [operator+"[ ]"]
            else:
                instr = [self.parse_assignment(instruction_line)]

        elif type(instruction) is CallInstruction:
            instr = [self.parse_function(instruction.function).instr]

        self.bytecodeInstructions.extend(instr)
           
    def merge(self):

        def find_instructions(mnemonic):
            instructions = []
            for index, instr in enumerate(self.bytecodeInstructions):
                if instr.startswith(mnemonic):
                    data = instr[instr.index("[") + 1:instr.index("]")]
                    instructions.append(Instruction(mnemonic, data, index))
            return instructions

        def find_assignments():
            pattern = re.compile('\$..*\$..*')
            instructions = []
            sequence = []
            first_index = -1
            for index, instr in enumerate(self.bytecodeInstructions):
                if pattern.match(instr):
                    addrs = instr.split(" := ")
                    addr1 = addrs[0].split("_")[-1]
                    addr2 = addrs[1].split("_")[-1]
                    sequence.append(int(addr2)-int(addr1))
                    if first_index < 0:
                        first_index = index
                elif sequence:
                    instructions.append((list(sequence), first_index))
                    del sequence[:]
                    first_index = -1
            return instructions

        def merge_PUSH():
            instructions = find_instructions("PUSH")
            if len(instructions) == 0:
                return
            data = []
            last_line = instructions[-1].line
            for instr in reversed(instructions):
                if last_line - instr.line > 1:
                    update_stack("PUSH[ ]", last_line, data)
                    del data[:]
                del self.bytecodeInstructions[instr.line]
                data.append(instr.data)
                last_line = instr.line
            update_stack("PUSH[ ]", last_line, data)

        def merge_SFVTCA():
            sfvInstructions = find_instructions("SFVTCA")
            spvInstructions = find_instructions("SPVTCA")
            for fv in reversed(sfvInstructions):
                for pv in reversed(spvInstructions):
                    if fv.line == pv.line-1 and fv.data == pv.data:
                        del self.bytecodeInstructions[fv.line:pv.line+1]
                        update_stack("SVTCA[{0}]".format(fv.data), fv.line, [])
                        break

        # Merge instructions that push or pop values from the stack.
        # Each COI instruction is represented by the assigning variable
        # label number minus the assigned variable label number
        # e.g. $prep275 = $prep272   ( = -3 )
        # each instruction generates a different sequence of intengers
        # which we will find and merge here
        def merge_OTHER():
            instructions_groups = find_assignments()
            for instr_list, index in reversed(instructions_groups):
                currentInstrs = []
                
                for instr in reversed(instr_list):
                    if not currentInstrs:
                        # DUP check
                        if instr == -1:
                            update_stack("DUP[ ]", index, [])
                        # CINDEX check
                        elif instr < -1:
                            update_stack("CINDEX[ ]", index, [])
                        else:
                            currentInstrs.append(instr)
                    else:
                        currentInstrs.insert(0, instr)
                        length = len(currentInstrs)
                        # MINDEX check
                        # conditions for MINDEX:
                        # [1, -X, {X times 1 value}, 2]
                        # where X = len - 2
                        if (
                            currentInstrs[0] == 1 and currentInstrs[-1] == 2 and
                            currentInstrs[1] == (length-2)*(-1) and
                            currentInstrs[2:-1] == [1] * (length-3)
                            ):
                            # SWAP check (SWAP = MINDEX[] with 2 at top of stack)
                            if length == 3:
                                update_stack("SWAP[ ]", index, [])
                            # ROLL check (ROLL = MINDEX[] with 3 at top of stack)
                            elif length == 4:
                                update_stack("ROLL[ ]", index, [])
                            # MINDEX[] with  x > 3 at top of stack
                            else:
                                update_stack("MINDEX[ ]", index, [])
                            currentInstrs = []

                if currentInstrs:
                    raise ValueError("Unkown or malformed instruction")
                # remove the instructions left after merge
                del self.bytecodeInstructions[index+1:index+1+length]
                        
        def update_stack(mnemonic, index, data):
            for d in data:
                self.bytecodeInstructions.insert(index, d)
            if len(data) > 1:
                mnemonic += "  /* %s values pushed */" % len(data)
            self.bytecodeInstructions.insert(index, mnemonic)

        merge_PUSH()
        merge_SFVTCA()
        merge_OTHER()

def save_font(bytecode, fontfile):
    
    font_roundtrip = TTFont(fontfile)
    bytecodeContainer = BytecodeContainer(font_roundtrip)
    for key in bytecode.keys():
        # we don't want GS initialize instructions
        if key == 'prep':
            del bytecode[key][:17]
        program_tag = key
        instruction = bytecodeContainer.constructInstructions(program_tag, bytecode[key])
        bytecodeContainer.tag_to_programs[program_tag] = Program(instruction)
    bytecodeContainer.updateTTFont(font_roundtrip)
    roundtrip_filename = "{0}_roundtrip.ttf".format(fontfile.split(".ttf")[0])
    font_roundtrip.save(roundtrip_filename)
    font_roundtrip.close()

def process_tables(tables):
    bytecode = {} 
    interpreter = InstructionInterpreter()
    for tag in tables:
        print("{0}:".format(tag))
        for line in tables[tag]:
            interpreter.parseInstruction(line.lstrip())
        interpreter.merge()
        bytecode[tag] = copy.deepcopy(interpreter.bytecodeInstructions)
        interpreter.print_bytecode()
        interpreter.clear()
    return bytecode

def main(args):

    tags = {} 
    current_tag = ""
    font_file = None
    if len(args) <= 0 or os.path.isfile(args[0]) == False:
        usage()
    if len(args) > 1:
        font_file = args[1]

    with open(args[0], "r") as file:
        
        for nl, line in enumerate(file):
            if line.isspace():
                current_tag = ""
            elif line.startswith('PREP:'):
                current_tag = 'prep'
                tags['prep'] = []
            elif line.startswith('Function'):
                current_tag = line[:-2]
                tags[current_tag] = []
            elif line.startswith('glyf'):
                current_tag = line[:-2]
                tags[current_tag] = [] 
            elif current_tag != "":
                tags[current_tag].append(line[:-1])

        bytecode = process_tables(tags)
        if font_file:
            save_font(bytecode, font_file)
        return bytecode

if __name__ == '__main__':
  main(sys.argv[1:])

