import sys, os
current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

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
FROM_CERN = False

pathToCalib = "/eos/user/j/jcapotor/RTDdata/calib"

integrationTime = 60 #seconds

try:
    with open(f"{pathToCalib}/LARTGRAD_TREE.json") as f:
        caldata = json.load(f)[ref]

    with open(f"{pathToCalib}/LARTGRAD_TREE_rcal.json") as f:
        rcaldata = json.load(f)[ref]

    with open(f"{pathToCalib}/CERNRCalib.json") as f:
        crcaldata = json.load(f)
except:
    print(f"You don't have the access rights to the calibration data: /eos/user/j/jcapotor/RTDdata/calib")
    print(f"Your data will not be corrected, but STILL DISPLAYED in rtd/onlinePlots")
    print(f"Ask access to Jordi Capó (jcapo@ific.uv.es) to data and change in line 14 on rtd/pdhd/online.py -> pathToCalib='path/to/your/calib/data' ")
    print(f"Calib data should be accessible from: https://cernbox.cern.ch/s/vg1yENbIdbxhOFH -> Download the calib folder and add path to pathToCalib")
    caldata, rcaldata, crcaldata = None, None, None

mapping = pd.read_csv(f"{current_directory}/src/data/mapping/pdhd_mapping.csv",
                            sep=";", decimal=",", header=0)

while True:
    today = datetime.now()
    startTimeStamp = (today - timedelta(seconds=integrationTime)).timestamp()
    endTimeStamp = (today).timestamp()
    if FROM_CERN is False:
        startTimeStamp = startTimeStamp*1e3
        endTimeStamp = endTimeStamp*1e3
    m = MakeData(detector="np04", all=allBool, system=system,
                    startDay=f"{today.strftime('%Y-%m-%d')}", endDay=f"{today.strftime('%Y-%m-%d')}",
                    clockTick=60,
                    ref=ref, FROM_CERN=FROM_CERN)
    m.getData()
    plt.figure()
    y, temp, etemp = [], [], []
    for name, dict in m.container.items():
        id = str(mapping.loc[(mapping["SC-ID"]==name)]["CAL-ID"].values[0])

        if caldata is not None:
            if id not in caldata.keys():
                continue
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
    plt.ylim(min(temp) - max(etemp), max(temp) + max(etemp))
    plt.savefig(f"{current_directory}/onlinePlots/tgrad.png")
