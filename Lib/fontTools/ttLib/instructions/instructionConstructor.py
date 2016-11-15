from . import statements

#this will parse str to instruct or data classes
class instructionConstructor():
    WORD_SUFFIX = "/* word */ "
    def __init__(self,instruction):
        self.instruction = instruction
        self.tokenizer()
    def getClass(self):
        return self.typed_instruction
    def tokenizer(self):
        try:
            is_word = False
            if self.instruction.endswith(self.WORD_SUFFIX):
                is_word = True
                self.instruction = self.instruction[:-len(self.WORD_SUFFIX)]
            data = int(self.instruction)
            self.typed_instruction = Data(data, is_word)
        except ValueError:
            data = ''
            flag = False
            has_data = False
            for i in range(len(self.instruction)):
                #print(self.instruction[i], self.instruction[i].isdigit())
                if self.instruction[i]=='[':
                    flag = True
                    self.typed_instruction = self.construct(statements.all,self.instruction[:i]+"_Statement")
                elif self.instruction[i].isdigit() and flag:
                    has_data = True
                    data += str(self.instruction[i])
                if self.instruction[i:i+2] == '/*':
                    break
            if has_data:
                self.typed_instruction.add_data(Data(data))
    def construct(self,idClasses, builderName):
        targetClass = getattr(idClasses, builderName)
        return targetClass()

class Data():
    def __init__(self, data, is_word = False):
        self.is_word = is_word
        if type(data)==str:
            self.value = data
        if type(data)==int:
            self.value = data

