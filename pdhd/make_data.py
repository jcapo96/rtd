import os
import sys

current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

from rtd.src.data.make_data import MakeData
from datetime import datetime, timedelta
import os

system = "tgrad"
allBool = True
today = datetime.now().strftime('%y-%m-%d')
path = "/eos/user/j/jcapotor/PDHDdata/"
ref = "40525"
configuration = "baseline"

dates = []
today = datetime.now()
start_date = datetime(2024, 9, 19)
end_date = datetime(2024, 9, 21)
while start_date <= end_date:
    dates.append(start_date)
    start_date += timedelta(days=1)

if allBool:
    system = "all"

for date in dates:
    print(date)
    pathToSaveData = f"{path}{system}/{date.strftime('%B')}{date.year}"
    if not os.path.exists(f"{pathToSaveData}"):
        os.makedirs(f"{pathToSaveData}")
        print(f"Created directory {date.strftime('%B')}{date.year} at {path}{system}")
    m = MakeData(detector="np04", all=allBool, system=system,
                    startDay=date.strftime('%Y-%m-%d'),
                    clockTick=60,
                    pathToSaveData=F"/eos/user/j/jcapotor/PDHDdata/{system}/{date.strftime('%B')}{date.year}/",
                    ref=ref, FROM_CERN=True, configuration=configuration)
    m.make()

# date = start_date
# endDate = end_date
# print(date, endDate)
# pathToSaveData = f"{path}{system}/{date.strftime('%B')}{date.year}"
# pathToSaveData = f"{path}{system}/all"
# if not os.path.exists(f"{pathToSaveData}"):
#     os.makedirs(f"{pathToSaveData}")
#     print(f"Created directory all")
# m = MakeData(detector="np04", all=allBool, system=system,
#                 startDay=date.strftime('%Y-%m-%d'), endDay="2024-03-31",
#                 clockTick=60,
#                 pathToSaveData=F"/eos/user/j/jcapotor/PDHDdata/{system}/{date.strftime('%B')}{date.year}/",
#                 ref=ref, FROM_CERN=False)
# m.make()