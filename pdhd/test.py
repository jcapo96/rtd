import ROOT
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

pathToSaveData = "/eos/user/j/jcapotor/PDSPdata/tgrad/"

dates = []
days = np.arange(1, 32, 1)
year = "2019"
months = ["03"]
for month in months:
    for day in days:
        if day != 3:
            continue
        if month == "04" and day > 10:
            continue
        if len(str(day)) == 1:
            date = f"{year}-{month}-0{day}"
        else:
            date = f"{year}-{month}-{day}"
        dates.append(date)

plt.figure(figsize=(10,6))
for i in range(0,9):
    # if i != 3:
    #     continue
    df = {}
    time = []
    height = {}
    for date in dates:
        outputRootFileName = f"{pathToSaveData}np04_tgrad_{date}_ctick60_calib_R39609cache.root"
        outputFile = ROOT.TFile(f"{outputRootFileName}", "READ")
        # print(outputFile.Map())
        data = outputFile.Get("temp")
        cal = outputFile.Get("LARTGRAD_TREE")
        rcal = outputFile.Get("rLARTGRAD_TREE")
        crcal = outputFile.Get("rCERNRCalib")
        data.GetEntry(0)
        t0 = getattr(data, "t")[0]
        for entry in data:
            # if entry.t[0] > t0 + 60*60*3:
            #     break
            for index in range(len(data.temp)):
                sensor = index + 1
                try:
                    cal.GetEntry(i)
                    rcal.GetEntry(i)
                    crcal.GetEntry(0)
                    cc = getattr(cal, f"cal{entry.name[index]}")*1e-3
                    rcc = getattr(rcal, f"cal{entry.name[index]}")*1e-3
                    crcc = getattr(crcal, f"cal{entry.name[index]}")*1e-3
                    if sensor not in df.keys():
                        df[sensor] = [entry.temp[index] - cc - rcc + crcc]
                    elif sensor in df.keys():
                        df[sensor].append(entry.temp[index] - cc - rcc + crcc)
                    if sensor not in height.keys():
                        height[sensor] = [entry.y[index]]
                    elif sensor in height.keys():
                        height[sensor].append(entry.y[index])
                except Exception as e:
                    continue

        outputFile.Close()

    df = pd.DataFrame.from_dict(df, orient="columns")
    df = df.loc[(df >= 0).all(axis=1)]
    df = df.loc[:, df.mean() <= 88]
    # df = df.loc[:, df.mean() >= 87.680]
    height = pd.DataFrame.from_dict(height, orient="columns")
    height = height.filter(items=df.columns)

    plt.errorbar(height.mean(axis=0).values, df.mean(axis=0).values, yerr=df.std(axis=0).values, fmt=".",
                 label=fr"Path {i}: $\mu$={np.mean(df.mean(axis=0).values):.3f} K; $\sigma$={1e3*np.std(df.mean(axis=0).values):.1f} mK")
    # plt.ylim(87.5, 87.75)
plt.legend(ncol=3)
plt.savefig("test.png")
