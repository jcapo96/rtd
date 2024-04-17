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

try:
    with open(f"/eos/user/j/jcapotor/RTDdata/calib/LARTGRAD_TREE.json") as f:
        caldata = json.load(f)[ref]

    with open(f"/eos/user/j/jcapotor/RTDdata/calib/LARTGRAD_TREE_rcal.json") as f:
        rcaldata = json.load(f)[ref]

    with open(f"/eos/user/j/jcapotor/RTDdata/calib/CERNRCalib.json") as f:
        crcaldata = json.load(f)
except:
    print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
    print(f"Your data will not be corrected")
    caldata, rcaldata, crcaldata = None, None, None

mapping = pd.read_csv(f"src/data/mapping/pdhd_mapping.csv",
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
        if caldata is not None:
            cal = caldata[id][2]*1e-3
        elif caldata is None:
            cal = 0
        if rcaldata is not None:
            rcal = rcaldata[id][2]*1e-3
        elif rcaldata is None:
            rcal = 0
        if crcaldata is not None:
            crcal = np.mean(crcaldata[f"s{int(name.split('TE')[1])}"])*1e-3
        elif crcaldata is None:
            crcal = 0
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        if (df["temp"].mean() - cal - rcal - crcal) > 88:
            continue

        y.append(dict["Y"])
        temp.append(df["temp"].mean() - cal - rcal - crcal)
        etemp.append(df["temp"].std())

    plt.errorbar(y, temp, yerr=etemp, fmt="o", capsize=10)
    plt.title(f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    # plt.ylim(min(temp)-max(etemp), max(temp)+max(etemp))
    plt.xlabel("Height (m)")
    plt.ylabel("Temperature (K)")
    plt.ylim(87.45, 87.51)
    plt.savefig("onlinePlots/tgrad.png")
