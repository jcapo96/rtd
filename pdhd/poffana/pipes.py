import ROOT
import numpy as np
import matplotlib.pyplot as plt
import datetime
ROOT.gROOT.SetBatch(True)

fileName = "/eos/user/j/jcapotor/PDHDdata/poff/data/np04_all_2024-05-02_07:30:00_2024-05-02_08:41:00_ctick60_calib_R40525cache.root"

tini, tend = datetime.datetime(2024, 5, 1, 15, 2, 0).timestamp() + 0*60*60, datetime.datetime(2024, 5, 1, 17, 0, 0).timestamp() + 0*60*60
print(tini, tend)

inputFile = ROOT.TFile(f"{fileName}", "READ")

tree = inputFile.Get("temp")
t, temp, etemp = {}, {}, {}
# Loop over the entries in the tree and fill the TGraph
for iEntry in range(tree.GetEntries()):
    tree.GetEntry(iEntry)
    for element in range(len(np.array(tree.t))):
        if np.array(tree.temp)[element] < 0:
            continue
        # if np.array(tree.temp)[element] > 90:
        #     continue
        # if (np.array(tree.t)[element] > tend or np.array(tree.t)[element] < tini):
        #     continue
        if element not in t:
            t[element] = [np.array(tree.t)[element]]
            temp[element] = [np.array(tree.temp)[element]]
            etemp[element] = [np.array(tree.etemp)[element]]
        else:
            t[element].append(np.array(tree.t)[element])
            temp[element].append(np.array(tree.temp)[element])
            etemp[element].append(np.array(tree.etemp)[element])

plt.figure(figsize=(10,6))
names = {48:"APA2LAr3", 49:"APA2LAr1", 50:"APA2LAr4", 51:"APA2LAr2", 54:"APA1F2", 55: "APA1LAr1", 56: "APA1LAr4", 57:"APA1F1",
         60:"APA3LAr1", 61:"APA3LAr3", 62:"APA3LAr2", 63:"APA3LAr4", 66:"APA4F2", 67:"APA4LAr1", 68:"APA4LAr4", 69:"APA4F1"}
cnt = 0
n=1
cut = 0
for i in range(49, 71):
    if i not in names:
        continue
    if i != 60:
        continue
    # if cnt != 1:
    #     cnt += 1
    #     continue
        plt.legend(loc="lower left")
        n += 1
        cnt = 0
    # plt.subplot(2,2,n)
    print(datetime.datetime.utcfromtimestamp(t[i][0]))
    print(datetime.datetime.utcfromtimestamp(t[i][-1]))
    plt.axvline(datetime.datetime(2024, 5, 2, 9, 30, 0).timestamp())
    plt.axvline(datetime.datetime(2024, 5, 2, 10, 8, 0).timestamp())
    plt.axvline(datetime.datetime(2024, 5, 2, 10, 41, 0).timestamp())

    plt.errorbar(t[i], temp[i] - temp[i][0], yerr=etemp[i], label=f"{names[i]}")
    cnt += 1

print(datetime.datetime.utcfromtimestamp(tini))
print(datetime.datetime.utcfromtimestamp(tend))
# plt.axvline(tini)
# plt.axvline(tend)
plt.legend(loc="lower left")
plt.savefig("/afs/cern.ch/user/j/jcapotor/software/rtd/pdhd/poffana/graph2.png")