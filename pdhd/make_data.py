import numpy as np
from rtd.src.data.make_data import MakeData

days = np.arange(3, 32, 1)
months = ["03"]
for month in months:
    for day in days:
        if len(str(day)) == 1:
            date = f"2019-{month}-0{day}"
        else:
            date = f"2019-{month}-{day}"
        m = MakeData(detector="np04", all=False, system="tgrad",
                     startDay=date,
                     clockTick=60,
                     pathToSaveData="/eos/user/j/jcapotor/PDSPdata/tgrad/",
                     ref="39609")
        m.make()