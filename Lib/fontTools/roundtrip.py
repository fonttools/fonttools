#! /usr/bin/env python
"""
usage: roundtrip input

    Expected input is a text file containing COI code
    for some font 
"""

import sys
import re
import os
import copy

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

    def is_function(self):
        pattern = re.compile('..*\(..*\)')
        return pattern.match(self.addr2)

class Instruction(object):

    def __init__(self, mnemonic, data, line):
        self.mnemonic = mnemonic
        self.data = data
        self.line = line
    def __repr__(self):
        return("{0}[{1}], line {2}".format(self.mnemonic, self.data, self.line))

class InstructionInterpreter(object):
    bytecodeInstructions = [] # contains the translated TTF so far

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
        ("Super45(",             "S45ROUND[ ]"),
        ("Super(",               "SROUND[ ]"),
        ("PPEM",                 "MPPEM[ ]"),
        ("PointSize",            "MPS[ ]"),
        ("GS[auto_flip] := true","FLIPON[ ]"),
        ("GS[auto_flip] := false","FLIPOFF[ ]"),
        ("GS[rp0]",              "SRP0[ ]"),
        ("GS[rp1]",              "SRP1[ ]"),
        ("GS[rp2]",              "SRP2[ ]")
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
        function_name = f.split("(")[0]
        if "_" in function_name:
            function = function_name.split("_")[0]
            param = function_name.split("_")[1]
            instr = function+"["+param+"]"
        else:
            instr = function_name+"[ ]"
        return instr

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
                        instr = self.parse_function(instruction.addr2)
                    else:
                        instr = "PUSH["+instruction.addr2+"]"
                        if instruction_line != self.parse_assignment(instruction_line):
                            instr = self.parse_assignment(instruction_line)

                else:
                    operator = self.get_binary_op(instruction.op)
                    instr = operator+"[ ]"
            else:

                instr = self.parse_assignment(instruction_line)

        elif type(instruction) is CallInstruction:
            instr = self.parse_function(instruction.function)

        self.bytecodeInstructions.append(instr)
           
    def merge(self):

        def find_instructions(mnemonic):
            instructions = []
            for index, instr in enumerate(self.bytecodeInstructions):
                if instr.startswith(mnemonic):
                    data = instr[instr.index("[") + 1:instr.index("]")]
                    instructions.append(Instruction(mnemonic, data, index))
            return instructions

        def merge_PUSH():
            instructions = find_instructions("PUSH")
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

        def update_stack(mnemonic, index, data):
            for d in data:
                self.bytecodeInstructions.insert(index, d)
            if len(data) > 1:
                mnemonic += "  /* %s values pushed */" % len(data)
            self.bytecodeInstructions.insert(index, mnemonic)

        merge_PUSH()
        merge_SFVTCA()

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

    if len(args) < 0 or !os.path.isfile(args[0]):
        usage()

    with open(args[0], "r") as file:
        
        for nl, line in enumerate(file):
            if line.isspace():
                current_tag = ""
            elif line.startswith('PREP:'):
                current_tag = 'prep'
                tags['prep'] = []
            # we ignore function defs for now
            #elif line.startswith('Function'):
            #    current_tag = line[:-2] 
            #    tags[current_tag] = []
            elif line.startswith('glyf'):
                current_tag = line[:-2]
                tags[current_tag] = [] 
            elif current_tag != "":
                tags[current_tag].append(line[:-1])

        bytecode = process_tables(tags)
        return bytecode

if __name__ == '__main__':
  main(sys.argv[1:])

