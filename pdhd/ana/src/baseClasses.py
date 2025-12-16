import pandas as pd

class LogFile():
    def __init__(self, path="mapping/configurations.csv"):
        self.path = path
        self._read()

    def _read(self):
        self.configurations = pd.read_csv(self.path, header=0)
        return self

class Configuration():
    def __init__(self, name, path="mapping"):
        self.name = name
        self.path = path
        self._read()

    def _read(self):
        self.mapping = pd.read_csv(f"{self.path}/{self.name}.csv", header=0)
        return self

class Data():
    def __init__(self, path="/Users/jcapo/cernbox/PDHDdata"):
        self.path = path
        self._read()

    def _read(self):
        self.data = pd.read_csv(f"{self.path}/all_data_new.csv", header=0)
        self.data = self.data.set_index("Unnamed: 0")
        self.data.index = pd.to_datetime(self.data.index)

        self.err = pd.read_csv(f"{self.path}/all_data_err_new.csv", header=0)
        self.err = self.err.set_index("Unnamed: 0")
        self.err.index = pd.to_datetime(self.err.index)
        return self

class Channel():
    def __init__(self, dataset, name):
        self.dataset = dataset
        self.name = name
        try:
            self.channelNumber = int(name.split("TE")[-1])
        except:
            self.channelNumber = name
        if self.name not in self.dataset.data.columns:
            self.data = None
            self.err = None
            # print(f"ERROR: Channel ({self.name}) not found")
        else:
            self.data = self.dataset.data[self.name]
            self.err = self.dataset.err[self.name]


