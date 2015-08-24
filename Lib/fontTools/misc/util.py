import os

def makeArgs(*params):
    args = []
    for param in params:
        args.append(param)
    return args


def makeOutputFileName(input, extension):
    dirName, fileName = os.path.split(input)
    fileName, ext = os.path.splitext(fileName)
    output = os.path.join(dirName, fileName + extension)
    n = 1
    while os.path.exists(output):
        output = os.path.join(dirName, fileName + "#" + repr(n) + extension)
        n = n + 1
    return output

