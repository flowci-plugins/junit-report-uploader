import os
from xml.dom import minidom

def findRootPom(projectDir):
    dirs = []

    for i in os.listdir(projectDir):
        fullPath = os.path.join(projectDir, i)

        if os.path.isdir(fullPath) and not i.startswith("."):
            dirs.append(fullPath)
            continue

        if os.path.isfile(fullPath) and i == "pom.xml":
            return fullPath

    for i in dirs:
        pomFile = findRootPom(i)
        if pomFile != None:
            return pomFile

    return None

def getNodeText(node):
    nodelist = node.childNodes
    result = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            result.append(node.data)
    return ''.join(result)

def hasModule(pomFile):
    if pomFile == None:
        return False

    dom = minidom.parse(pomFile)
    modules = dom.getElementsByTagName("modules")
    
    names = []
    if len(modules) == 1:
        for node in modules[0].childNodes:
            text = getNodeText(node)
            if text != "":
                names.append(text)

    return len(names) > 0


pom = findRootPom(os.getcwd())
print(hasModule(pom))