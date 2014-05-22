#this will parse str to instruct or data classes
class instructionConstructor():
    def __init__(self,instruction):
        self.instruction = instruction
        self.tokenizer()
    def getClass(self):
        return self.typed_instruction
    def tokenizer(self):
        try:
            self.typed_instruction = data(self.instruction)
        except ValueError:

            for i in range(len(self.instruction)):
                if self.instruction[i]!='[':
                    i = i+1
                else:
                    break
            self.typed_instruction = self.construct(instructions.all,self.instruction[:i]) 
    def construct(self,idClasses, builderName):
        targetClass = getattr(idClasses, builderName)
        return targetClass()

class data():
    def __init__(self,str_data):
        self.value = int(str_data)
    
