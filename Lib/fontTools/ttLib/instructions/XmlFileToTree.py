import xml.etree.ElementTree as ElementTree
import os
import sys
import instructions
import copy 
from collections import deque
import ClassConstructor
import string
import re
import pe
import pstates.States as states
program_env = pe.ProgramEnvironment()
#helper function to display the structure of the xml
def printXml(root,level):
    queue = deque([root,0])

    while len(queue)!=0: 
        top = queue.popleft()
        level = queue.popleft()
        child_tag_dict = {}
        space = ''
        level = level+1
        for i in range(level):
            space = space + '-'
        for child in top:
        #deduplicate the child
            if child.tag not in child_tag_dict:
                child_tag_dict[child.tag] = 1
                queue.append(child)
                queue.append(level)
            else:
                child_tag_dict[child.tag] = child_tag_dict[child.tag] + 1
        for k in child_tag_dict:
            print space, k, child_tag_dict[k]

#access the current top of current data stack
def top(data_stack):
    return data_stack[len(data_stack)-1]

#process the cvt table
def ConstructCVTTable(cvt_node):
    for child in cvt_node:
        program_env.cvt_table[child.attrib['index']] = child.attrib['value']
    
#function definition only in fpgm and prep table
#process fpgm and prep to get all function label

def ProcessFPGMOrPrep(fgpm_or_prep_node):
    for child in fgpm_or_prep_node:
        processInstruction(child.text)

def parseXMLGetRoot(xmlFilePath):
    if not xmlFilePath:
        xmlFilePath = "resource/NotoSans-Bold.ttx"
    baseDir = os.path.dirname(os.path.realpath(__file__))
    xmlFullPath = os.path.join(os.sep,baseDir,xmlFilePath)

    tree = ElementTree.parse(xmlFullPath)
    root = tree.getroot()
    processRoot(root)
def processRoot(root):
    
    assembly_num = 0
    for child in root:
    
        if child.tag == "cvt":
                ConstructCVTTable(child);
        if child.tag == "fpgm" or child.tag == "prep" :
                ProcessFPGMOrPrep(child)
def parseSingleInstruction(line):
        line = line.split("/")[0]
        line = line.strip()
        instruction = None
        #print line
        if len(line.split("["))>1:
            instruction = line.split("[")[0]
            #print instruction
          
        data = re.findall(r'\d+',line)
        
        if len(data)!=0 and instruction is None:
            return ('data_only',data)
        
        if instruction is not None and len(data) == 0:
            return ('instruction_only',instruction)
        
        if len(data)!=0 and instruction is not None:
            return ('instruction_and_data',instruction,data)
        return None;
def processInstruction(lines):
        #program_env = pe.ProgramEnvironment()
        line_pr = 0
        new_lines = lines.splitlines()
        for line in new_lines:
            parseSingleInstruction(line)
        #lines = lines.split('\n')
        current_instruction = None
        for line in new_lines:
            
            result = parseSingleInstruction(line)
            
            if result is not None:
                if result[0] == 'instruction_only':
                        program_env.state = states.normal
                        print result[1]
                        current_instruction = ClassConstructor.construct(instructions.all,result[1],program_env)
                        #current_instruction.initProgame(program_env)
                        current_instruction.action()

                if result[0] == 'data_only' and program_env.state == states.push_data:
                        print result[1]
                        current_instruction.action(result[1])
            
if __name__ =="__main__":
    try:
        parseXMLGetRoot(sys.argv[1])
    except:
        parseXMLGetRoot(None)
