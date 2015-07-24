from fontTools import ttLib
from fontTools.ttLib.bytecodeContainer import BytecodeContainer
from fontTools.ttLib.instructions import abstractExecute
import sys
import copy

def main(args):

    if len(args) < 1:
        print("usage: treeshake font-file")
        sys.exit(1)

    fontfile = args[0]
    font = ttLib.TTFont(fontfile)

    bytecodeContainer = BytecodeContainer(font)
    absExecutor = abstractExecute.Executor(bytecodeContainer)

    called_functions = set()
    try:
        absExecutor.execute('prep')
        called_functions.update(list(set(absExecutor.program.call_function_set)))
    except:
        pass
    environment = copy.deepcopy(absExecutor.environment)
    tables_to_execute = bytecodeContainer.programs.keys()
    for table in tables_to_execute:
        try:
            absExecutor.execute(table)
            called_functions.update(list(set(absExecutor.program.call_function_set)))
            absExecutor.environment = copy.deepcopy(environment)
        except:
            absExecutor.environment = copy.deepcopy(environment)
    function_set = absExecutor.environment.function_table.keys()
    unused_functions = [item for item in function_set if item not in called_functions]

    bytecodeContainer.removeFunctions(unused_functions)
    bytecodeContainer.updateTTFont(font)

    outfile = "Reduced"+fontfile
    font.save(outfile)
    font.close()

if __name__ == '__main__':
  main(sys.argv[1:])
                          
