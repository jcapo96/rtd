from src.data.make_data import MakeData
from datetime import datetime, timedelta
import time, json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

system = "tgrad"
allBool = False
today = datetime.now().strftime('%y-%m-%d')
path = "/eos/user/j/jcapotor/PDHDdata/"
ref = "40525"

integrationTime = 60 #seconds

with open(f"/eos/user/j/jcapotor/RTDdata/calib/LARTGRAD_TREE.json") as f:
    caldata = json.load(f)[ref]

with open(f"/eos/user/j/jcapotor/RTDdata/calib/LARTGRAD_TREE_rcal.json") as f:
    rcaldata = json.load(f)[ref]

with open(f"/eos/user/j/jcapotor/RTDdata/calib/CERNRCalib.json") as f:
    crcaldata = json.load(f)

mapping = pd.read_csv(f"/afs/cern.ch/user/j/jcapotor/software/rtd/src/data/mapping/pdhd_mapping.csv",
                            sep=";", decimal=",", header=0)

while True:
    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()*1e3
    endTimeStamp = (today).timestamp()*1e3
    m = MakeData(detector="np04", all=allBool, system=system,
                    startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                    clockTick=60,
                    ref=ref, FROM_CERN=False)
    m.getData()
    plt.figure()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])
        if id not in caldata.keys():
            continue
        cal = caldata[id][2]*1e-3
        rcal = rcaldata[id][2]*1e-3
        crcal = np.mean(crcaldata[f"s{int(name.split('TE')[1])}"])*1e-3
        if int(name.split("TE")[1]) < 20:
            continue
        y.append(dict["Y"])
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        temp.append(df["temp"].mean() - cal - rcal - crcal)
        etemp.append(df["temp"].std())

    plt.errorbar(y, temp, yerr=etemp, fmt="o", capsize=10)
    plt.title(f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    # plt.ylim(min(temp)-max(etemp), max(temp)+max(etemp))
    plt.xlabel("Height (m)")
    plt.ylabel("Temperature (K)")
    plt.ylim(87.45, 87.51)
    plt.savefig("onlinePlots/tgrad.png")
