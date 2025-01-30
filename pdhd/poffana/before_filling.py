import ROOT
import numpy as np
import matplotlib.pyplot as plt
import datetime
ROOT.gROOT.SetBatch(True)

fileName = "/eos/user/j/jcapotor/PDHDdata/poff/data/np04_all_2024-05-06_12:00:00_2024-05-06_18:00:00_ctick60_calib_R40525cache.root"

tini, tend = datetime.datetime(2024, 5, 1, 8, 24, 0).timestamp() - 2*60*60, datetime.datetime(2024, 5, 1, 9, 43, 0).timestamp() - 2*60*60
print(tini, tend)

inputFile = ROOT.TFile(f"{fileName}", "READ")

tree = inputFile.Get("temp")
t, temp = {}, {}
# Loop over the entries in the tree and fill the TGraph
for iEntry in range(tree.GetEntries()):
    tree.GetEntry(iEntry)
    for element in range(len(np.array(tree.t))):
        # if np.array(tree.temp)[element] < 0:
        #     continue
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
names = {72:"APA2LAr3", 73:"APA2LAr1", 74:"APA2LAr4", 75:"APA2LAr2", 78:"APA1F2", 79: "APA1LAr1", 80: "APA1LAr4", 81:"APA1F1",
         84:"APA3LAr1", 85:"APA3LAr3", 86:"APA3LAr2", 87:"APA3LAr4", 90:"APA4F2", 91:"APA4LAr1", 92:"APA4LAr4", 93:"APA4F1"}
cnt = 0
n=1
cut = 0
for i in range(72, 94):
    try:
        if cnt > 3:
            plt.legend(loc="lower left")
            n += 1
            cnt = 0
        plt.subplot(2,2,n)
        print(datetime.datetime.utcfromtimestamp(t[i][51]))
        plt.axvline(t[i][51])
        plt.plot(t[i], temp[i] - temp[i][0], label=f"{names[i]}")
        cnt += 1
    except:
        continue
plt.legend(loc="lower left")
plt.savefig("/afs/cern.ch/user/j/jcapotor/software/rtd/pdhd/poffana/graph2.png")