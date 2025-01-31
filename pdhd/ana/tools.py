import pandas as pd
import numpy as np
import datetime, pickle
import utils

def make_poff(date_end, integration_time, ref, save_path=None):
    delta_time = datetime.timedelta(hours=integration_time)
    date_ini = date_end - delta_time
    mapping_end = utils.load_mapping(date=date_end)
    selection_end = mapping_end.loc[(mapping_end["SYSTEM"]=="TGRAD")]
    mapping_ini = utils.load_mapping(date=date_ini)
    selection_ini = mapping_ini.loc[(mapping_ini["SYSTEM"]=="TGRAD")]
    equal = (selection_end["SC-ID"].to_list() == selection_ini["SC-ID"].to_list())

    if equal:
        data, data_err = utils.load_data(date_ini, date_end)
        selection = selection_end["SC-ID"].to_list()
        sensor_id = selection_end["CAL-ID"].astype(int).astype(str).to_numpy()
        sample = data.loc[date_ini:date_end][selection]
        sample.columns = sensor_id
        poff_calib = 1e3*(sample.sub(sample[ref], axis=0)).mean(axis=0).to_numpy()
        poff_calib_err = 1e3*(sample.sub(sample[ref], axis=0)).sem(axis=0).to_numpy()
        poff = pd.DataFrame({"cc":poff_calib, "cc_err":poff_calib_err}, index=sensor_id)
        poff = {ref:poff}
        with open(fr"{save_path}/poff_{date_ini}_{date_end}.pkl", "wb") as file:
            pickle.dump(poff, file)
    else:
        print("Not possible: Not the same configuration within the POFF calib window.")
    return poff_calib

def make_tgrad_profile( data=None, data_err=None,
                        date_ini=None, date_end=None,
                        path_to_calib="/eos/user/j/jcapotor/RTDdata/calib/TGrad/POFF/poff_2024-12-03 13:25:00_2024-12-03 14:25:00.pkl",
                        ref="40525", save_path=None
                        ):
    if data is None and data_err is None:
        if date_ini is not None and date_end is not None:
            data, data_err = utils.load_data(date_ini, date_end)
        else:
            print("Please provide a date_ini and date_end.")
    elif (data is not None and data_err is None):
        date_ini, date_end = min(data.index), max(data.index)
        data, data_err = utils.load_data(date_ini, date_end)
    elif (data is None and data_err is not None):
        date_ini, date_end = min(data_err.index), max(data_err.index)
        data, data_err = utils.load_data(date_ini, date_end)
    elif (data is not None and data_err is not None):
        date_ini, date_end = min(data.index), max(data.index)

    calib = utils.load_calib(path=path_to_calib)[ref]
    mapping_end = utils.load_mapping(date=date_end)
    selection_end = mapping_end.loc[(mapping_end["SYSTEM"]=="TGRAD")]
    mapping_ini = utils.load_mapping(date=date_ini)
    selection_ini = mapping_ini.loc[(mapping_ini["SYSTEM"]=="TGRAD")]
    equal = (selection_end["SC-ID"].to_list() == selection_ini["SC-ID"].to_list())

    if equal:
        selection = selection_end["SC-ID"].to_list()
        height = selection_end["Y"].to_numpy()
        sensor_id = selection_end["CAL-ID"].astype(int).astype(str).to_numpy()
        sample = data.loc[date_ini:date_end][selection]
        sample.columns = sensor_id
        selection_end["CAL-ID"] = selection_end["CAL-ID"].astype(int).astype(str)
        selection_end = selection_end.set_index("CAL-ID")
        profile = sample.mean().sub(1e-3*calib.loc[calib.index.isin(sensor_id)]["cc"], axis=0)
        profile_err = np.sqrt(sample.sem()**2 + (1e-3 * calib.loc[calib.index.isin(sensor_id)]["cc_err"])**2)
        #profile_err = sample.sem()

        profile = profile.to_frame(name="temp")
        profile_err = profile_err.to_frame(name="temp_err")

        profile = profile.join(selection_end[["Y"]], how="left")
        profile = profile.join(profile_err[["temp_err"]], how="left")

        if save_path is not None:
            print(f"Profile stored in {save_path}")
            profile.to_csv(save_path)
        elif save_path is None:
            print(f"Profile not saved.")
    else:
        print("Not possible: Not the same sensor available within the timw window selected.")
        print(selection_ini["SC-ID"].to_list())
        print(selection_end["SC-ID"].to_list())
    return profile