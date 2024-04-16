import ROOT
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

pathToSaveData = "/eos/user/j/jcapotor/PDHDdata/tgrad/"

dates = []
days = np.arange(1, 32, 1)
months = ["04"]
for month in months:
    for day in days:
        if month == "04" and day > 14:
            continue
        if len(str(day)) == 1:
            date = f"2024-{month}-0{day}"
        else:
            date = f"2024-{month}-{day}"
        dates.append(date)
df = {}
time = []
for date in dates:
    outputRootFileName = f"{pathToSaveData}np04_tgrad_{date}_ctick60_calib_LARTGRAD_TREER40525cache.root"
    outputFile = ROOT.TFile(f"{outputRootFileName}", "READ")
    # print(outputFile.Map())
    data = outputFile.Get("temp")
    cal = outputFile.Get("LARTGRAD_TREE")
    rcal = outputFile.Get("rLARTGRAD_TREE")
    crcal = outputFile.Get("rCERNRCalib")

    for entry in data:
        time.append(entry.t[0])
        for index in range(len(data.temp)):
            sensor = index + 1
            try:
                cal.GetEntry(0)
                rcal.GetEntry(0)
                crcal.GetEntry(0)
                cc = getattr(cal, f"cal{entry.name[sensor]}")*1e-3
                rcc = getattr(rcal, f"cal{entry.name[sensor]}")*1e-3
                crcc = getattr(crcal, f"cal{entry.name[sensor]}")*1e-3
                if entry.name[index] not in df.keys():
                    df[sensor] = [entry.temp[index] + cc + rcc + crcc]
                elif entry.name[index] in df.keys():
                    df[sensor].append(entry.temp[index] + cc + rcc + crcc)
            except Exception as e:
                continue

    outputFile.Close()

df = pd.DataFrame.from_dict(df, orient="columns")
time = np.array(time)
df["t"] = time
df = df.loc[(df >= 0).all(axis=1)].sort_values(by="t")
print(df.columns)
# df["t"] = np.array(time)

plt.figure()
plt.plot(df["t"].values, df[46].values)
plt.plot(df["t"].values, df[47].values)
plt.savefig("test.png")
