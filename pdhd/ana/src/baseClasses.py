import pandas as pd

class LogFile():
    def __init__(self, path="/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping/configurations.csv"):
        self.path = path
        self.__read__()

    def __read__(self):
        self.configurations = pd.read_csv(self.path, header=0)
        return self

class Configuration():
    def __init__(self, name, path="/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping"):
        self.name = name
        self.path = path
        self.__read__()

    def __read__(self):
        self.mapping = pd.read_csv(f"{self.path}/{self.name}.csv", header=0)
        return self

class Data():
    def __init__(self, path="/eos/user/j/jcapotor/PDHDdata"):
        self.path = path

    def __read__(self):
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
        self.data = self.dataset.data[self.name]
        self.err = self.dataset.err[self.name]

class Sensor():
    def __init__(self, dataset, id):
        self.id = id
        self.dataset = dataset
        self.__info__()

    def __info__(self):
        self.info = {}
        for index, configurationRow in LogFile().configurations.iterrows():
            mapping = Configuration(configurationRow["Configuration"]).mapping
            sensorConfig = mapping[mapping["CAL-ID"] == self.id]
            if len(sensorConfig) == 0:
                continue
            self.info[index] = {"sensorInfo":sensorConfig, "configInfo":configurationRow.T}
        if len(self.info) == 0:
            self.info = None
            print(f"ERROR: SensorID ({self.id}) not found")
        return self.info


logfile = LogFile()
print(logfile.configurations)

configuration = Configuration("baseline")
print(configuration.mapping)

sensor = Sensor(Data(), 405)
print(sensor.info[0]["configInfo"]["Start"])
