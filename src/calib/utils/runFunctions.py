from rtd.src.calib.utils.tools.dataTools import time_to_seconds
import pandas as pd
import os, glob

def read_datafile(row):
    """
    Read data from a text file and perform data processing.

    Parameters:
        row (pandas.Series): A row from a DataFrame containing file information.

    Returns:
        pandas.DataFrame: DataFrame containing the processed data.
    """
    try:
        path = "/eos/user/j/jcapotor/RTDdata"
        text_file = glob.glob(os.path.join(path, "**", row["Filename"] + ".txt"), recursive=True)
        path_to_file = text_file[0]
        data = pd.read_csv(path_to_file, sep='\t', header=None)
        names = get_file_header(row)
        data.columns = names.keys()
        data["timeStamp"] = (data["Date"] + "-" + data["Time"]).apply(time_to_seconds)
        del data["Date"]
        del data["Time"]
        return data, names
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

def get_file_header(row):
    """
    Extracts column names from a row dictionary to create a file header.

    Parameters:
        row (dict): A dictionary representing a row of data where keys are column names.

    Returns:
        list: A list of column names extracted from the row dictionary.
    """
    # Generate column names based on the number of columns in the row
    columns = [f"S{i}" for i in range(7, 21)]

    # Initialize list to store column names
    names = {"Date":"Date", "Time":"Time"}

    # Iterate over columns and add column names to the list
    for col in columns:
        # Check if the value of the column is a string (i.e., it represents a column name)
        if isinstance(row[col], str):
            names[row[col]] = col.lower()

    return names