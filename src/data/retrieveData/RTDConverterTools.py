import os, ROOT
from datetime import datetime, timedelta

def convertDDMMYYYY(date, time):
    datetime_str = f"{date} {time}"
    datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    epochTime = int(datetime_obj.timestamp())
    return epochTime

def prepareTimeStamp(startDate, endDate):
    try:
        startDate = datetime.strptime(startDate, "%d-%m-%Y")
        endDate   = datetime.strptime(endDate, "%d-%m-%Y")
    except:
        try:
            startDate = datetime.strptime(startDate, "%Y-%m-%d")
            endDate   = datetime.strptime(endDate, "%Y-%m-%d")
        except Exception as e:
            raise(e)
    # if endDate == startDate:
    #     endDate += timedelta(days=1)
    return startDate, endDate


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