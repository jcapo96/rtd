import numpy as np
from rtd.src.data.make_data import MakeData

days = np.arange(1, 32, 1)
months = ["10", "11", "12"]
for month in months:
    for day in days:
        if month == "11" and day > 30:
            continue
        if len(str(day)) == 1:
            date = f"2018-{month}-0{day}"
        else:
            date = f"2018-{month}-{day}"
        m = MakeData(detector="np04", all=False, system="tgrad", startDay=date, clockTick=60, pathToSaveData="/eos/user/j/jcapotor/PDSPdata/tgrad/")
        m.make()