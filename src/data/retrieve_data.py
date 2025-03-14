import pandas as pd
import numpy as np
import subprocess, json, datetime, tqdm, sys

mapping = pd.read_csv("/afs/cern.ch/work/j/jcapotor/software/rtd/src/data/mapping/baseline.csv")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    date = sys.argv[1]
    dataFrame = pd.DataFrame()
    for index, row in tqdm.tqdm(mapping.iterrows(), total=len(mapping), desc=fr"Processing {date}"):
        # try:
        #     int(row["CAL-ID"])
        # except:
        #     continue
        curl_command = curl_command = ['curl', f'http://epdtdi-dcs-extract.cern.ch:8080/day/{date}/{row["DCS-ID"]}']
        curl_output = subprocess.run(curl_command, capture_output=True, text=True)
        data = json.loads(curl_output.stdout)
        try:
            df = pd.DataFrame.from_dict(data, orient="index", columns=[str(row["SC-ID"])])
            df.index = pd.to_datetime(pd.to_numeric(df.index), unit='ms') + datetime.timedelta(hours=2)
            dataFrame = pd.concat([dataFrame, df])
        except:
            continue
    dataFrame.to_csv(fr'/eos/user/j/jcapotor/PDHDdata/data/{datetime.datetime.strftime(date, "%Y-%m-%d")}.csv')
    dataFrame = dataFrame.set_index("Unnamed: 0")
    dataFrame_data = dataFrame.resample("1min").mean()
    dataFrame_err = dataFrame.resample("1min").std()
    dataFrame_data.to_csv(fr'/eos/user/j/jcapotor/PDHDdata/data_1min/{datetime.datetime.strftime(date, "%Y-%m-%d")}.csv')
    dataFrame_err.to_csv(fr'/eos/user/j/jcapotor/PDHDdata/data_1min/{datetime.datetime.strftime(date, "%Y-%m-%d")}_err.csv')