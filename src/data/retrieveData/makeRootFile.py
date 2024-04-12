from RTDConverter import RTDConverter
import pandas as pd
import ROOT, ctypes, array, os

outputRootFileName = "test.root"

slowControlWebMapping = pd.read_csv(f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/mapping/pdhd_mapping.csv",
                           sep=";", header=0)

listOfDays = ["01-04-2024", "02-03-2024", "03-03-2024", "04-03-2024", "05-03-2024",
              "05-03-2024", "06-03-2024", "07-03-2024", "08-03-2024", "09-03-2024",
              "09-03-2024", "10-03-2024", "11-03-2024", "12-03-2024", "13-03-2024",
              "14-03-2024", "15-03-2024", "16-03-2024", "17-03-2024", "18-03-2024"]

listOfDays = ["31-03-2024", "01-04-2024"]

for index, row in slowControlWebMapping.iterrows():
    if int(row["SC-ID"].split("TE")[1]) > 2:
        break
    RTDConverter(detector="np04", elementId=row["DCS-ID"], startDay="2024-04-01", endDay="2024-04-01", startTime="00:05:00", endTime="00:05:20", outputRootFileName=outputRootFileName).fillRootFile()



outputFile = ROOT.TFile(f"{outputRootFileName}", "UPDATE")
outputTree = outputFile.Get("data")
branchNames = [branch.GetName() for branch in outputTree.GetListOfBranches()]
print(branchNames)
cnt = 0
for branchName in branchNames:
    if ("t" in branchName) & (cnt == 0):
        outputTree.GetBranch(branchName).SetName("t")
        cnt += 1
    elif ("t" in branchName) and (cnt != 0):
        outputTree.GetListOfBranches().Remove(outputTree.GetBranch(branchName))
        outputTree.SetBranchStatus(f"{branchName}", 0)
        outputTree.Write("", ROOT.TObject.kOverwrite)
        cnt += 1
outputFile.Close()