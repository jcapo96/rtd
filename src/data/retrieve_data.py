import pandas as pd
import numpy as np
import subprocess, json, datetime, tqdm

mapping = pd.read_csv("/afs/cern.ch/work/j/jcapotor/software/rtd/src/data/mapping/baseline.csv")

dates = []
start_date = datetime.datetime(2024, 3, 1)
#end_date = datetime.datetime(2024, 3, 3)
end_date = datetime.datetime(2025, 1, 1)
while start_date <= end_date:
    dates.append(start_date)
    start_date += datetime.timedelta(days=1)

for date in dates:
    dataFrame = pd.DataFrame()
    for index, row in tqdm.tqdm(mapping.iterrows(), total=len(mapping), desc=fr"Processing {date}"):
        try:
            int(row["CAL-ID"])
        except:
            continue
        curl_command = curl_command = ['curl', f'http://epdtdi-dcs-extract.cern.ch:8080/day/{datetime.datetime.strftime(date, "%Y-%m-%d")}/{row["DCS-ID"]}']
        curl_output = subprocess.run(curl_command, capture_output=True, text=True)
        data = json.loads(curl_output.stdout)
        try:
            df = pd.DataFrame.from_dict(data, orient="index", columns=[str(row["SC-ID"])])
            df.index = pd.to_datetime(pd.to_numeric(df.index), unit='ms') + datetime.timedelta(hours=2)
            dataFrame = pd.concat([dataFrame, df])
        except:
            continue
    dataFrame.to_csv(fr'/eos/user/j/jcapotor/PDHDdata/data/{datetime.datetime.strftime(date, "%Y-%m-%d")}.csv')