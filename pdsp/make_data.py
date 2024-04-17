import numpy as np
from rtd.src.data.make_data import MakeData
from datetime import datetime, timedelta
import os

system = "tgrad"
allBool = False
today = datetime.now().strftime('%y-%m-%d')
path = "/eos/user/j/jcapotor/PDSPdata/"
ref = "40525"

dates = []
today = datetime.now()
start_date = datetime(2018, 9, 1)
end_date = datetime(2020, 3, 1)
while start_date <= end_date:
    dates.append(start_date)
    start_date += timedelta(days=1)

if allBool:
    system = "all"

for date in dates:
    pathToSaveData = f"{path}{system}/{date.strftime('%B')}{date.year}"
    if not os.path.exists(f"{pathToSaveData}"):
        os.makedirs(f"{pathToSaveData}")
        print(f"Created directory {date.strftime('%B')}{date.year} at {path}{system}")
    m = MakeData(detector="np04", all=allBool, system=system,
                    startDay=date.strftime('%Y-%m-%d'),
                    clockTick=60,
                    pathToSaveData=F"/eos/user/j/jcapotor/PDHDdata/{system}/{date.strftime('%B')}{date.year}/",
                    ref=ref)
    m.make()