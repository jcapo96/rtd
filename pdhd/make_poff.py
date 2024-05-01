import os
import sys

current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

from rtd.src.data.make_data import MakeData
from datetime import datetime, timedelta
import json

allBool = True
system = "apa"
start_date = datetime(2024, 5, 1, 12, 0, 0) #write here the start datetime
end_date = datetime(2024, 5, 1, 15, 0, 0) #write here the end datetime


path = f"/eos/user/j/jcapotor/RTDdata/calib/POFF_{start_date.strftime('%Y-%m-%d')}T{start_date.strftime('%H:%M:%S')}_{end_date.strftime('%Y-%m-%d')}T{end_date.strftime('%H:%M:%S')}"
ref = "40525"

m = MakeData(detector="np04", all=allBool,
                    startDay=start_date.strftime('%Y-%m-%d'),
                    startTime=start_date.strftime("%H:%M:%S"),
                    endDay=end_date.strftime("%Y-%m-%d"),
                    endTime=end_date.strftime("%H:%M:%S"),
                    clockTick=120,
                    pathToSaveData=F"/eos/user/j/jcapotor/PDHDdata/poff/",
                    ref=ref, configuration="precision", FROM_CERN=True)
m.getData()

container = m.container

calib = {}
for refkey in container.keys():
    refid = container[refkey]["id"]
    calib[refid] = {}
    refdict = container[refkey]
    data_ref = container[refkey]["access"].data
    data_ref = data_ref.loc[(data_ref["temp"]>0)]

    for key in container.keys():
        sensid = container[key]["id"]
        data_sens = container[key]["access"].data
        data_sens = data_sens.loc[(data_sens["temp"]>0)]
        if (data_sens["temp"].mean() > 88 or data_sens["temp"].mean() < 0):
            calib[refid][sensid] = [0 for i in range(9)]
        else:
            # if refid == 40192:
            #     print((data_sens["temp"].mean() - data_ref["temp"].mean())*1e3, sensid)
            calib[refid][sensid] = [(data_sens["temp"].mean() - data_ref["temp"].mean())*1e3 for _ in range(9)]

with open(f"{path}.json", "w") as json_file:
    json.dump(calib, json_file, indent=4)