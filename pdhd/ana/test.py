import pandas as pd
import datetime

start_date = datetime.datetime(2024, 3, 1)
end_date = datetime.datetime(2025, 1, 1)
container = pd.DataFrame()
while start_date <= end_date:
    print(datetime.datetime.strftime(start_date, "%Y-%m-%d"))
    filename = fr'/eos/user/j/jcapotor/PDHDdata/data_1min/{datetime.datetime.strftime(start_date, "%Y-%m-%d")}_err.csv'
    start_date += datetime.timedelta(days=1)
    try:
        data = pd.read_csv(filename)
        data = data.set_index("Unnamed: 0")
        data.index = pd.to_datetime(data.index)
        container = pd.concat([container, data])
    except:
        continue

container.to_csv(fr'/eos/user/j/jcapotor/PDHDdata/all_data_err.csv')
