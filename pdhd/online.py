from rtd.src.data.make_data import MakeData
from datetime import datetime, timedelta
import time, json
import matplotlib.pyplot as plt
import pandas as pd

system = "tgrad"
allBool = False
today = datetime.now().strftime('%y-%m-%d')
path = "/eos/user/j/jcapotor/PDHDdata/"
ref = "40525"

with open(f"/eos/user/j/jcapotor/RTDdata/calib/LARTGRAD_TREE.json") as f:
    data = json.load(f)[ref]

mapping = pd.read_csv(f"/afs/cern.ch/user/j/jcapotor/software/rtd/src/data/mapping/pdhd_mapping.csv",
                            sep=";", decimal=",", header=0)

while True:
    today = datetime.now()
    startTimeStamp = (today - timedelta(minutes=1)).timestamp()*1e3
    endTimeStamp = (today - timedelta(minutes=0)).timestamp()*1e3
    m = MakeData(detector="np04", all=allBool, system=system,
                    startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                    clockTick=60,
                    ref=ref, FROM_CERN=False)
    m.getData()
    plt.figure()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])
        if id not in data.keys():
            continue
        cal = data[id][0]*1e-3
        if int(name.split("TE")[1]) < 20:
            continue
        y.append(dict["Y"])
        df = dict["access"].data
        df = df.loc[(df["epochTime"]>startTimeStamp)&(df["epochTime"]<endTimeStamp)]
        temp.append(df["temp"].mean() - cal)
        etemp.append(df["temp"].std())

    plt.errorbar(y, temp, yerr=etemp, fmt="o", capsize=10)
    plt.title(f"{today.strftime('%Y-%m-%d %H:%M:%S')}")
    plt.ylim(min(temp)-max(etemp), max(temp)+max(etemp))
    plt.savefig("test.png")
