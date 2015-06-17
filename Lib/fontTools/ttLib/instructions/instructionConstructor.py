from . import statements

#this will parse str to instruct or data classes
class instructionConstructor():
    def __init__(self,instruction):
        self.instruction = instruction
        self.tokenizer()
    def getClass(self):
        return self.typed_instruction
    def tokenizer(self):
        try:
            data = int(self.instruction)
            self.typed_instruction = Data(data)
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
                if self.instruction[i]=='/' and self.instruction[i+1] == "*":
                    break
            if has_data:
                self.typed_instruction.add_data(Data(data))
    def construct(self,idClasses, builderName):
        targetClass = getattr(idClasses, builderName)
        return targetClass()

class Data():
    def __init__(self, data):
        if type(data)==str:
            self.value = data
        if type(data)==int:
             self.value = data
    
