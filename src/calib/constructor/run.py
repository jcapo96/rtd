from utils.runFunctions import read_datafile
from utils.tools.makeRCalib import ReadoutCalib
import pandas as pd

class Run:
    """Represents a run of data."""

    def __init__(self, log_file_row):
        """
        Initializes a Run instance.

        Parameters:
            log_file_row (pd.Series): A row of data from the log file representing a run.
        """
        self.log_file_row = log_file_row
        # Read the datafile corresponding to the log file row
        self.data, self.channels = read_datafile(self.log_file_row)
        # Get the IDs of the sensors in the run
        self.ids = self.data.columns
        # Compute the initial timestamp of the run
        self.t0 = self.data.sort_values(by="timeStamp").reset_index(drop=True)["timeStamp"][0]

    def compute_offset(self, ref, t0=1000, tf=2000):
        """
        Compute offsets for the specified reference sensor within a time window.

        Parameters:
            ref (str): The reference sensor for computing offsets.
            t0 (int, optional): Start time of the time window. Default is 1000.
            tf (int, optional): End time of the time window. Default is 2000.

        Returns:
            Run: Instance of Run with computed offsets.
        """
        # Adjust start and end times based on the initial timestamp of the run
        t0 = self.t0 + t0
        tf = self.t0 + tf
        # Select data within the specified time window
        data_cut = self.data.loc[(self.data["timeStamp"] > t0) & (self.data["timeStamp"] < tf)]
        # Compute offsets relative to the reference sensor
        offset = data_cut.drop(columns="timeStamp").sub(data_cut[ref], axis=0) * 1e3
        # Concatenate timestamps and offsets
        self.offset = pd.concat([data_cut["timeStamp"], offset], axis=1)
        return self

    def compute_rcal(self, ref):
        print(f"Computing IFIC readout calib with respect to {ref}")

        readout = ReadoutCalib(readout="IFIC")
        readout.save()
        readout.load()
        print(f"Channels to correct: {self.channels.items()} \n")
        names = [key for key, value in self.channels.items() if value in readout.data.columns]
        print(f"Readout names: {names}")
        print(f"Readout data: {readout.data}")
        readout.data.columns = names
        roffset = readout.data.sub(readout.data[ref], axis=0)
        self.roffset = roffset
        return self
