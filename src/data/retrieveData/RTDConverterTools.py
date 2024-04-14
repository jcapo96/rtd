import os, ROOT
from datetime import datetime, timedelta

def convertDDMMYYYY(datetime_obj):
    epochTime = datetime_obj.timestamp() + 3600
    changeDate = datetime.strptime(f"{date.split('-')[0]}-03-31 02:00:00", "%Y-%m-%d %H:%M:%S")
    if epochTime > changeDate.timestamp():
        epochTime += 3600
    return epochTime

def checkFileExists(outputRootFileName):
    """
    Check if the specified ROOT file exists.

    Args:
        outputRootFileName (str): The path to the ROOT file.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    return os.path.isfile(outputRootFileName)

def checkTreeExists(outputRootFileName, currentTreeName):
    """
    Check if a specific TTree exists in the specified ROOT file.

    Args:
        outputRootFileName (str): The path to the ROOT file.
        currentTreeName (str): The name of the TTree to check for.

    Returns:
        bool: True if the TTree exists, False otherwise.
    """
    outputFile = ROOT.TFile(f"{outputRootFileName}", "READ")
    treeList = outputFile.GetListOfKeys()
    names = []
    if len(treeList) == 0:
        outputFile.Close()
        return False
    else:
        for index, treeName in enumerate(treeList):
            treeName = treeName.ReadObj()
            names.append(str(treeName.GetName()))
        if currentTreeName in names:
            outputFile.Close()
            return True
        else:
            outputFile.Close()
            return False

def checkBranchExists(outputRootFileName, treeName, branchName):
    outputFile = ROOT.TFile(f"{outputRootFileName}", "READ")
    outputTree = outputFile.Get(treeName)
    branchList = [branch.GetName() for branch in outputTree.GetListOfBranches()]
    if len(branchList) == 0:
        outputFile.Close()
        return False
    else:
        if branchName in branchList:
            outputFile.Close()
            return True
        else:
            outputFile.Close()
            return False