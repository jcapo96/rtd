import numpy as np
from rtd.src.data.make_data import MakeData

days = np.arange(1, 32, 1)
months = ["03", "04"]
for month in months:
    for day in days:
        if month == "04" and day > 14:
            continue
        if len(str(day)) == 1:
            date = f"2024-{month}-0{day}"
        else:
            date = f"2024-{month}-{day}"
        m = MakeData(detector="np04", all=False, system="apa", startDay=date, clockTick=10, pathToSaveData="/eos/user/j/jcapotor/PDHDdata/apa/")
        m.make()