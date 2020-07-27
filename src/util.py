import os
from flowci import domain

def GetOutputDir():
    outputDir = os.path.join(domain.AgentJobDir, ".output")
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
    return outputDir