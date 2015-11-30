from instructions import statements, instructionConstructor, abstractExecute

class BytecodeContainer(object):
    """ Represents bytecode-related global data for a TrueType font. """
    def __init__(self, tt):
        # tag id -> Program
        self.tag_to_programs = {}
        self.IRs = {}
        # function_table: function label -> Function
        self.function_table = {}
        #preprocess the static value to construct cvt table
        self.constructCVTTable(tt)
        #extract instructions from font file
        self.extractProgram(tt)

    def constructCVTTable(self, tt):
        self.cvt_table = {}
        values = tt['cvt '].values
        key = 0
        for value in values:
            self.cvt_table[key] = value
            key = key + 1
    
    def extractProgram(self, tt):
        '''
        a dictionary maps tag->Program to extract all the bytecodes
        in a single font file
        '''
        def constructInstructions(program_tag, instructions):
            thisinstruction = None
            instructions_list = []
            def combineInstructionData(instruction,data):
                instruction.add_data(data)
            number = 0
            for instruction in instructions:
                instructionCons = instructionConstructor.instructionConstructor(instruction)
                instruction = instructionCons.getClass()
        
                if isinstance(instruction, instructionConstructor.Data):
                    combineInstructionData(thisinstruction,instruction)
                else:
                    if thisinstruction is not None:
                        thisinstruction.id = program_tag + '.' + str(number)
                        instructions_list.append(thisinstruction)
                        number = number+1
                    thisinstruction = instruction

            instructions_list.append(thisinstruction)
            return instructions_list
        
        def add_tags_with_bytecode(tt,tag):
            for key in tt.keys():
                if hasattr(tt[key], 'program'):
                    if len(tag) != 0:
                        program_tag = tag+"."+key
                    else:
                        program_tag = key
                    self.tag_to_programs[program_tag] = constructInstructions(program_tag, tt[key].program.getAssembly())
                if hasattr(tt[key], 'keys'):
                    add_tags_with_bytecode(tt[key],tag+key)

        # preprocess the function definition instructions between <fpgm></fpgm>
        def extract_functions():
            if('fpgm' in self.tag_to_programs.keys()):
                instructions = self.tag_to_programs['fpgm']
                functionsLabels = []
                skip = False
                function_ptr = None
                for instruction in instructions:
                    if not skip:
                        if isinstance(instruction, statements.all.PUSH_Statement):
                            functionsLabels.extend(instruction.data)
                        if isinstance(instruction, statements.all.FDEF_Statement):
                            skip = True
                            function_ptr = Function()
                    else:
                        if isinstance(instruction, statements.all.ENDF_Statement):
                            skip = False
                            function_label = functionsLabels[-1]
                            functionsLabels.pop()
                            self.function_table[function_label] = function_ptr
                        else:
                            function_ptr.instructions.append(instruction)

                for key, value in self.function_table.items():
                    value.constructBody()

        # transform list of instructions -> Program
        def setup_programs():
            for key, instr in self.tag_to_programs.items():
                if key is not 'fpgm':
                    self.tag_to_programs[key] = Program(instr)

        add_tags_with_bytecode(tt,"")
        extract_functions()
        setup_programs()

    #remove functionsToRemove from the function table
    def removeFunctions(self, functionsToRemove=[]):
        for label in functionsToRemove:
            try:
                del self.function_table[label]
            except:
                pass

    # param label_mapping is a dict for each table with a list of 
    # tuples (label, pos)  where label is the old function label 
    # and pos is the position of this label on the data array (of the root PUSH instruction)
    def relabelFunctions(self, label_mapping):
        relabelled_function_table = {}
        self.label_mapping = {}
        new_label = 0
        for old_label in self.function_table.keys():
            relabelled_function_table[new_label] = self.function_table[old_label]
            self.label_mapping[old_label] = new_label
            new_label += 1

        self.function_table = relabelled_function_table
        self.relabelTables(label_mapping)

    def relabelTables(self, function_calls):
        for table in function_calls.keys():
            #First instruction, contains the first PUSH with
            #the function labels called during execution
            root = self.tag_to_programs[table].body.statement_root

            for old_label, line in function_calls[table]:
                root.data[line-1] = self.label_mapping[old_label]

    #update the TTFont object passed with contets of current BytecodeContainer
    def updateTTFont(self, ttFont):
        self.replaceCVTTable(ttFont)
        self.replaceFpgm(ttFont)
        self.replaceOtherTables(ttFont)
 
    def replaceCVTTable(self, ttFont):
        for i in range(len(self.cvt_table)):
            ttFont['cvt '].values[i] = self.cvt_table[i]

    def instrToAssembly(self, instr):
        assembly = []
        if(instr.mnemonic == 'PUSH'):
            assembly.append('PUSH[ ]')
            if(len(instr.data) > 1):
                assembly[-1] += "  /* %s values pushed */" % len(instr.data)

            for data in instr.data:
                assembly.append(str(data))
        else:
            if(len(instr.data) > 0):
                instr_append = instr.mnemonic+'['
                for data in instr.data:
                    instr_append += str(data)
                instr_append += ']'
                assembly.append(instr_append)
            else:
                assembly.append(instr.mnemonic+'[ ]')
        return assembly

    # replaces the Fpgm in ttFont with contents of this;
    # rebuilds the function number mass-PUSH and includes FDEFs
    def replaceFpgm(self, ttFont):
        assembly = []
        skip = False

        if len(self.function_table) > 0:
            assembly.append("PUSH[ ]")
            if(len(self.function_table) > 1):
                assembly[-1] += "  /* %s values pushed */" % len(self.function_table)

            for label in reversed(self.function_table.keys()):
                assembly.append(str(label))

            for function in self.function_table.values():
                assembly.append('FDEF[ ]')
                for instr in function.instructions:
                    assembly.extend(self.instrToAssembly(instr))

                assembly.append('ENDF[ ]')
            ttFont['fpgm'].program.fromAssembly(assembly)

    def replaceOtherTables(self, ttFont):
        for table in self.tag_to_programs.keys():
            assembly = []
            if table != 'fpgm':
                root = self.tag_to_programs[table].body.statement_root
                if root is not None:
                    
                    stack = []
                    stack.append(root)

                    while len(stack) > 0:
                        top_instr = stack[-1]
                        assembly.extend(self.instrToAssembly(top_instr))
                        stack.pop()

                        if len(top_instr.successors) > 1:
                            reverse_successor = top_instr.successors[::-1]
                            stack.extend(reverse_successor)
                        else:
                            stack.extend(top_instr.successors)

                try:
                    ttFont[table].program.fromAssembly(assembly)
                except:
                    ttFont['glyf'].glyphs[table[5:]].program.fromAssembly(assembly)

    def print_IR(self, IR):
        for line in IR:
            print line

# Function and Program are suspiciously similar; should probably be refactored.
# per-glyph instructions
class Program(object):
    def __init__(self, input):
        self.body = Body(instructions = input)
        self.call_function_set = [] # set of functions called in the tag program
    def pretty_print(self):
        self.body.pretty_print()
    def start(self):
        return self.body.statement_root

class Function(object):
    def __init__(self, instructions=None):
        self.instructions = []
    def pretty_print(self):
        self.body.pretty_print()
    def constructBody(self):
        self.body = Body(instructions = self.instructions)
    def start(self):
        return self.body.statement_root

class Body(object):
    '''
    Encapsulates a list of statements.
    '''
    def __init__(self,*args, **kwargs):
        self.statement_root = None
        if kwargs.get('statement_root') is not None:
            self.statement_root = kwargs.get('statement_root')
        if kwargs.get('instructions') is not None:
            self.instructions = kwargs.get('instructions')
            if len(self.instructions) > 0:
                self.statement_root = self.constructSuccessorAndPredecessor()

    # CFG construction
    def constructSuccessorAndPredecessor(self):
        def is_branch(instruction):
            if isinstance(instruction,statements.all.EIF_Statement):
                return True
            elif isinstance(instruction,statements.all.ELSE_Statement):
                return True
            else:
                return False
        pending_if_stack = []
        for index in range(len(self.instructions)):
            this_instruction = self.instructions[index]

            # Jump instructions are sporadically used.
            # We'll just treat them like normal statements now and fix up the
            # CFG during symbolic execution, since we need to read the dest off the stack.

            #if isinstance(this_instruction,statements.all.JMPR_Statement):
            #    raise NotImplementedError
            #elif isinstance(this_instruction,statements.all.JROT_Statement):
            #    raise NotImplementedError
            #elif isinstance(this_instruction,statements.all.JROF_Statement):
            #    raise NotImplementedError

            #other statements should have at least 
            #the next instruction in stream as a successor
            if index < len(self.instructions)-1 and not is_branch(self.instructions[index+1]):
                this_instruction.add_successor(self.instructions[index+1])
                self.instructions[index+1].set_predecessor(this_instruction)
            # An IF statement should have two successors:
            #  one already added (index+1); one at the ELSE/ENDIF.
            if isinstance(this_instruction,statements.all.IF_Statement):
                pending_if_stack.append(this_instruction)
            elif isinstance(this_instruction,statements.all.ELSE_Statement):
                this_if = pending_if_stack[-1]
                this_if.add_successor(this_instruction)
                this_instruction.set_predecessor(this_if)
            elif isinstance(this_instruction,statements.all.EIF_Statement):
                this_if = pending_if_stack[-1]
                this_if.add_successor(this_instruction)
                this_instruction.set_predecessor(this_if)
                pending_if_stack.pop()
        return self.instructions[0]

    def pretty_print(self):
        if self.statement_root is None:
            return

        level = 1
        instruction = self.statement_root
        instruction_stack = []
        instruction_stack.append(instruction)

        def printHelper(instruction,level):
            print level*"   " + str(instruction)

        level = 0
        while len(instruction_stack)>0:
            top_instruction = instruction_stack[-1]
            printHelper(top_instruction,level)
            if isinstance(top_instruction, statements.all.IF_Statement) or isinstance(top_instruction, statements.all.ELSE_Statement):
                level = level + 1
            instruction_stack.pop()
            if len(top_instruction.successors) == 0:
                level = level - 1
            elif len(top_instruction.successors) > 1:
                reverse_successor = top_instruction.successors[::-1]
                instruction_stack.extend(reverse_successor)
            else:
                instruction_stack.extend(top_instruction.successors)
