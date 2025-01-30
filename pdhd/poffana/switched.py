import ROOT
import numpy as np
import matplotlib.pyplot as plt
import datetime
ROOT.gROOT.SetBatch(True)

fileName = "/eos/user/j/jcapotor/PDHDdata/poff/data/np04_all_2024-05-01_07:44:00_2024-05-01_08:54:00_ctick60_calib_R40525cache.root"

tini, tend = datetime.datetime(2024, 5, 1, 8, 51, 0).timestamp() + 2*60*60, datetime.datetime(2024, 5, 1, 8, 54, 0).timestamp() + 2*60*60
print(tini, tend)

inputFile = ROOT.TFile(f"{fileName}", "READ")

tree = inputFile.Get("temp")
t, temp = {}, {}
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
        else:
            t[element].append(np.array(tree.t)[element])
            temp[element].append(np.array(tree.temp)[element])

plt.figure(figsize=(10,6))
cnt = 0
n=1
cut = 0
for i in range(78, 84):
    try:
        print(datetime.datetime.utcfromtimestamp(t[i][0]))
        print(datetime.datetime.utcfromtimestamp(t[i][-1]))
        plt.plot(t[i], temp[i] - temp[i][0])
        cnt += 1
    except:
        continue

print(datetime.datetime.utcfromtimestamp(tini))
print(datetime.datetime.utcfromtimestamp(tend))
plt.axvline(tini)
plt.axvline(tend)
plt.legend(loc="lower left")
plt.savefig("/afs/cern.ch/user/j/jcapotor/software/rtd/pdhd/poffana/graph2.png")