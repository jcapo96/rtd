import pandas as pd
import numpy as np
import subprocess, json, datetime, tqdm, sys

mapping = pd.read_csv("/afs/cern.ch/work/j/jcapotor/software/rtd/src/data/mapping/baseline.csv")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    date = sys.argv[1]
    dataFrame_data = pd.DataFrame()
    dataFrame_err = pd.DataFrame()
    for index, row in tqdm.tqdm(mapping.iterrows(), total=len(mapping), desc=fr"Processing {date}"):
        curl_command = curl_command = ['curl', f'http://epdtdi-dcs-extract.cern.ch:8080/day/{date}/{row["DCS-ID"]}']
        curl_output = subprocess.run(curl_command, capture_output=True, text=True)
        data = json.loads(curl_output.stdout)
        try:
            df = pd.DataFrame.from_dict(data, orient="index", columns=[str(row["SC-ID"])])
            df.index = pd.to_datetime(pd.to_numeric(df.index), unit='ms') + datetime.timedelta(hours=2)
            df_data = df.resample("1min").mean()
            df_err = df.resample("1min").std()
            dataFrame_data = pd.concat([dataFrame_data, df_data])
            dataFrame_err = pd.concat([dataFrame_err, df_err])
            del df_data
            del df_err
        except:
            continue
    dataFrame_data = dataFrame_data.resample("1min").mean()
    dataFrame_err = dataFrame_err.resample("1min").mean()
    dataFrame_data.to_csv(fr'/eos/user/j/jcapotor/PDHDdata/data/{date}.csv')
    dataFrame_err.to_csv(fr'/eos/user/j/jcapotor/PDHDdata/data/{date}_err.csv')