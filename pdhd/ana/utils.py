import pandas as pd
import pickle

def load_configurations(path="/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping/configurations.csv"):
    configurations = pd.read_csv(path, header=0)
    configurations["Start"] = pd.to_datetime(configurations["Start"], format="%Y-%m-%d %H:%M:%S")
    configurations["End"] = pd.to_datetime(configurations["End"], format="%Y-%m-%d %H:%M:%S")
    return configurations

def load_logfile(path="/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping/logFile-NP04-IFIC.csv"):
    logfile = pd.read_csv(path, header=0)
    return logfile

def load_mapping(path="/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping/mapping.csv", date=None):
    configurations = load_configurations()
    configuration = configurations.loc[(configurations["Start"]<date)&(configurations["End"]>date)]["Configuration"].values[0]
    print(fr"Configuration: {configuration}")
    path_to_mapping = fr"/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping/{configuration}.csv"
    mapping = pd.read_csv(path_to_mapping, header=0)
    return mapping

def load_calib(path="/eos/user/j/jcapotor/RTDdata/calib/TGrad/LAR2023/lar2023_tree_method_avg_path.pkl"):
    with open(path, "rb") as file:
        calib = pickle.load(file)
    return calib

def load_data(tini, tend):
    data = pd.read_csv("/eos/user/j/jcapotor/PDHDdata/all_data.csv")
    data_err = pd.read_csv("/eos/user/j/jcapotor/PDHDdata/all_data_err.csv")

    data = data.set_index("Unnamed: 0")
    data.index = pd.to_datetime(data.index)

    data_err = data_err.set_index("Unnamed: 0")
    data_err.index = pd.to_datetime(data_err.index)

    data = data.loc[(data.index>tini)&(data.index<tend)]
    data_err = data_err.loc[(data_err.index>tini)&(data_err.index<tend)]
    return data, data_err

def load_current_corr(path="/eos/user/j/jcapotor/DUNE-IFIC/Experiments/ProtoDUNE-HD/Operation/Data/2024-7-1_2024-7-6_current_correction.csv"):
    current_corr = pd.read_csv(path, header=0)
    current_corr = current_corr.set_index("Unnamed: 0")
    return current_corr

def load_cfd_sim(path="/eos/user/j/jcapotor/DUNE-IFIC/Experiments/ProtoDUNE-HD/CFD/ProtoDUNE-II Temperature Profiles Pumps Off CE Off.csv"):
    data = pd.read_csv(path, header=0)
    data.columns = ["Y", "temp", "temp_err"]
    data["Y"] = 1000*data["Y"]
    return data
