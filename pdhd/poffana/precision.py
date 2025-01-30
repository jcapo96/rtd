import ROOT
import numpy as np
import matplotlib.pyplot as plt
import datetime
import pandas as pd
ROOT.gROOT.SetBatch(True)

fileName = "/eos/user/j/jcapotor/PDHDdata/poff/data/np04_all_2024-05-01_09:32:00_2024-05-02_06:21:00_ctick60_calib_R40525cache.root"

inputFile = ROOT.TFile(f"{fileName}", "READ")

tree = inputFile.Get("temp")
t, temp, etemp = {}, {}, {}
# Loop over the entries in the tree and fill the TGraph
for iEntry in range(tree.GetEntries()):
    tree.GetEntry(iEntry)
    for element in range(len(np.array(tree.t))):
        if element not in t:
            t[element] = [np.array(tree.t)[element]]
            temp[element] = [np.array(tree.temp)[element]]
            etemp[element] = [np.array(tree.etemp)[element]]
        else:
            t[element].append(np.array(tree.t)[element])
            temp[element].append(np.array(tree.temp)[element])
            etemp[element].append(np.array(tree.etemp)[element])

mapping = pd.read_csv("/afs/cern.ch/user/j/jcapotor/software/rtd/src/data/mapping/precision_pdhd_mapping.csv", header=0)
names = mapping["NAME"].values
sens, ref = 84, 71

for i in range(96):
    plt.figure(figsize=(10,6))
    sens = i
    plt.axvline(datetime.datetime(2024, 5, 1, 11, 33, 0).timestamp(), color="red")
    plt.axvline(datetime.datetime(2024, 5, 1, 12, 1, 0).timestamp(), color="red")
    plt.axvline(datetime.datetime(2024, 5, 1, 13, 1, 0).timestamp(), color="red")
    plt.axvline(datetime.datetime(2024, 5, 1, 14, 1, 0).timestamp(), color="red")
    plt.axvline(datetime.datetime(2024, 5, 1, 14, 59, 0).timestamp(), color="red")
    plt.axvline(datetime.datetime(2024, 5, 1, 17, 0, 0).timestamp(), color="red")
    plt.axvline(datetime.datetime(2024, 5, 1, 19, 5, 0).timestamp(), color="red")

    plt.errorbar(t[sens], np.array(temp[sens]) - np.array(temp[ref]), fmt=".", yerr=etemp[ref], label=f"{names[sens]} - {names[ref]}")
    #plt.errorbar(t[sens], np.array(temp[sens]) - np.array(temp[sens])[0], fmt=".", yerr=etemp[ref], label=f"{names[sens]} - {names[ref]}")

    plt.ylim(np.mean((temp[sens]) - np.array(temp[ref])) -0.02, np.mean((temp[sens]) - np.array(temp[ref])) + 0.02)
    #plt.ylim(-0.1, 0.1)
    plt.legend(loc="best")
    plt.savefig(f"/afs/cern.ch/user/j/jcapotor/software/rtd/pdhd/poffana/plots/graph{i}.png")