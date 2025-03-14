import pandas as pd
import numpy as np
import datetime, pickle
import utils
import scipy.stats as stats

def line(x, A, B):
    return A + B*x

def apply_current_corr(
        data=None, data_err=None,
        date_ini=None, date_end=None,
        current_corr_path="/eos/user/j/jcapotor/DUNE-IFIC/Experiments/ProtoDUNE-HD/Operation/Data/2024-7-1_2024-7-6_current_correction.csv",
    ):
    if data is None and data_err is None:
        if date_ini is not None and date_end is not None:
            data, data_err = utils.load_data(date_ini, date_end)
        else:
            print("Please provide a date_ini and date_end.")
            return None, None
    elif data is not None and data_err is None:
        date_ini, date_end = min(data.index), max(data.index)
        data, data_err = utils.load_data(date_ini, date_end)
    elif data is None and data_err is not None:
        date_ini, date_end = min(data_err.index), max(data_err.index)
        data, data_err = utils.load_data(date_ini, date_end)
    elif data is not None and data_err is not None:
        date_ini, date_end = min(data.index), max(data.index)

    current_corr = utils.load_current_corr(path=current_corr_path)

    corrected_data, corrected_data_err = data.copy(), data_err.copy()

    for index, row in current_corr.iterrows():
        slope = row["slope"]
        T0 = row["T0"]
        current_channel = row["current_channel"]
        # corrected_data[index] = corrected_data[index] - line(
        #     corrected_data[current_channel], T0, slope
        # )
        corrected_data[index] = corrected_data[index] - slope * (
            corrected_data[current_channel] - corrected_data[current_channel].iloc[0]
        )
        corrected_data_err[index] = np.sqrt(
            corrected_data_err[index] ** 2
            + (slope * corrected_data_err[current_channel]) ** 2)

    return corrected_data, data_err

def apply_calibration(
        data=None, data_err=None,
        date_ini=None, date_end=None,
        path_to_calib="/eos/user/j/jcapotor/RTDdata/calib/TGrad/POFF/poff_2024-12-03 13:25:00_2024-12-03 14:25:00.pkl",
        ref="40525"
    ):
    if data is None and data_err is None:
        if date_ini is not None and date_end is not None:
            data, data_err = utils.load_data(date_ini, date_end)
        else:
            print("Please provide a date_ini and date_end.")
            return None, None
    elif data is not None and data_err is None:
        date_ini, date_end = min(data.index), max(data.index)
        data, data_err = utils.load_data(date_ini, date_end)
    elif data is None and data_err is not None:
        date_ini, date_end = min(data_err.index), max(data_err.index)
        data, data_err = utils.load_data(date_ini, date_end)
    elif data is not None and data_err is not None:
        date_ini, date_end = min(data.index), max(data.index)

    calib = utils.load_calib(path=path_to_calib)[ref]
    mapping_end = utils.load_mapping(date=date_end)
    selection_end = mapping_end.loc[(mapping_end["SYSTEM"]=="TGRAD")]
    mapping_ini = utils.load_mapping(date=date_ini)
    selection_ini = mapping_ini.loc[(mapping_ini["SYSTEM"]=="TGRAD")]
    equal = (selection_end["SC-ID"].to_list() == selection_ini["SC-ID"].to_list())

    corrected_data, corrected_data_err = data.copy(), data_err.copy()

    if equal:
        selection = selection_end["SC-ID"].to_list()
        height = selection_end["Y"].to_numpy()
        sensor_id = selection_end["CAL-ID"].astype(int).astype(str).to_numpy()
        selection_end.loc[:, "CAL-ID"] = selection_end["CAL-ID"].astype(int).astype(str)
        selection_end = selection_end.set_index("CAL-ID")
        corrected_data = corrected_data[selection].sub(1e-3*calib.loc[calib.index.isin(sensor_id)]["cc"], axis=1)
        corrected_data_err = np.sqrt(corrected_data_err[selection].values**2 + (1e-3 * calib.loc[calib.index.isin(sensor_id)]["cc_err"].values)**2)
    else:
        print("Not possible: Not the same sensor available within the time window selected.")
        print(selection_ini["SC-ID"].to_list())
        print(selection_end["SC-ID"].to_list())
    return corrected_data, corrected_data_err

def make_tgrad_profile(
        data=None, data_err=None,
        date_ini=None, date_end=None,
        path_to_calib="/eos/user/j/jcapotor/RTDdata/calib/TGrad/POFF/poff_2024-12-03 13:25:00_2024-12-03 14:25:00.pkl",
        ref="40525", save_path=None,
        system="TGRAD"
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
        if date_ini is None and date_end is None:
            date_ini, date_end = min(data.index), max(data.index)
        elif date_ini is not None and date_end is None:
            date_end = max(data.index)
        elif date_ini is None and date_end is not None:
            date_ini = min(data.index)
        elif date_ini is not None and date_end is not None:
            if date_ini < min(data.index):
                print(f"date_ini: {date_ini} is lower than the minimum date available in the data: {min(data.index)}")
                date_ini = min(data.index)
            if date_end > max(data.index):
                print(f"date_end: {date_end} is higher than the maximum date available in the data: {max(data.index)}")
                date_end = max(data.index)
            else:
                date_ini, date_end = date_ini, date_end

    calib = utils.load_calib(path=path_to_calib)[ref]
    baseline_mapping = utils.load_mapping(date=datetime.datetime(2024, 4, 15, 0, 0, 0))
    mapping_end = utils.load_mapping(date=date_end)
    mapping_end = mapping_end.loc[(baseline_mapping["CAL-ID"].notna())]
    mapping_end = mapping_end.loc[(mapping_end["CAL-ID"].notna())]
    if system is not None:
        selection_end = mapping_end.loc[(mapping_end["SYSTEM"]==system)]
    else:
        selection_end = mapping_end
    mapping_ini = utils.load_mapping(date=date_ini)
    mapping_ini = mapping_ini.loc[(baseline_mapping["CAL-ID"].notna())]
    mapping_ini = mapping_ini.loc[(mapping_ini["CAL-ID"].notna())]
    if system is not None:
        selection_ini = mapping_ini.loc[(mapping_ini["SYSTEM"]==system)]
    else:
        selection_ini = mapping_ini
    equal = (selection_end["SC-ID"].to_list() == selection_ini["SC-ID"].to_list())

    if equal:
        selection = selection_end["SC-ID"].to_list()
        print(selection_end["CAL-ID"].to_list())
        sensor_id = selection_end["CAL-ID"].astype(int).astype(str).to_numpy()
        sample = data.loc[date_ini:date_end][selection]
        sample.columns = sensor_id
        selection_end.loc[:, "CAL-ID"] = selection_end["CAL-ID"].astype(int).astype(str)
        selection_end = selection_end.set_index("CAL-ID")
        profile = sample.mean().sub(1e-3*calib.loc[calib.index.isin(sensor_id)]["cc"], axis=0)
        profile_err = np.sqrt(sample.sem()**2 + (1e-3 * calib.loc[calib.index.isin(sensor_id)]["cc_err"])**2)

        profile = profile.to_frame(name="temp")
        profile_err = profile_err.to_frame(name="temp_err")

        profile = profile.join(selection_end, how="left")
        profile = profile.join(profile_err[["temp_err"]], how="left")

        if save_path is not None:
            print(f"Profile stored in {save_path}")
            profile.to_csv(save_path)
        elif save_path is None:
            pass
            #print(f"Profile not saved.")
    else:
        print("Not possible: Not the same sensor available within the time window selected.")
        print(selection_ini["SC-ID"].to_list())
        print(selection_end["SC-ID"].to_list())
    return profile

def make_poff(
        date_end, integration_time, ref, save_path=None,
        system="TGRAD"
    ):
    delta_time = datetime.timedelta(minutes=integration_time)
    date_ini = date_end - delta_time
    baseline_mapping = utils.load_mapping(date=datetime.datetime(2024, 4, 15, 0, 0, 0))
    mapping_end = utils.load_mapping(date=date_end)
    mapping_end = mapping_end.loc[(baseline_mapping["CAL-ID"].notna())]
    mapping_end = mapping_end.loc[(mapping_end["CAL-ID"].notna())]
    if system is not None:
        selection_end = mapping_end.loc[(mapping_end["SYSTEM"]==system)]
    else:
        selection_end = mapping_end
    mapping_ini = utils.load_mapping(date=date_ini)
    mapping_ini = mapping_ini.loc[(baseline_mapping["CAL-ID"].notna())]
    mapping_ini = mapping_ini.loc[(mapping_ini["CAL-ID"].notna())]
    if system is not None:
        selection_ini = mapping_ini.loc[(mapping_ini["SYSTEM"]==system)]
    else:
        selection_ini = mapping_ini
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

def tprofile(data, xCol=None, yCol=None, num_bins=50, mean="mean", error="std"):
    """
    Bins data and computes statistics for a specified column.

    Parameters:
    - data (DataFrame): The dataset containing the data.
    - xCol (str, optional): Column name to use for binning. Defaults to index.
    - yCol (str, required): Column name to compute statistics on.
    - num_bins (int): Number of bins for binning.
    - mean (str or function): Statistic for mean values (e.g., "mean", "median", custom function).
    - error (str or function): Statistic for error values (e.g., "std", custom function).

    Returns:
    - bin_centers (ndarray): Centers of the bins (as datetime objects if applicable).
    - bin_means (ndarray): Computed mean values for each bin.
    - bin_stds (ndarray): Computed error values for each bin.
    """

    if yCol is None:
        raise ValueError("yCol must be specified.")

    # Determine x_data source
    if xCol is None:
        x_data = data.index
    else:
        x_data = data[xCol]

    # Check if x_data is datetime and convert if necessary
    datetime_conversion = False
    if np.issubdtype(x_data.dtype, np.datetime64):
        x_data = x_data.astype("int64") / 1e9  # Convert to seconds
        datetime_conversion = True  # Mark for reconversion later

    y_data = data[yCol].to_numpy()

    # Compute statistics
    bin_means, bin_edges, _ = stats.binned_statistic(x_data, y_data, statistic=mean, bins=num_bins)
    bin_stds, _, _ = stats.binned_statistic(x_data, y_data, statistic=error, bins=num_bins)

    # Compute bin centers
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Convert bin_centers back to datetime if needed
    if datetime_conversion:
        bin_centers = pd.to_datetime(bin_centers, unit="s")

    return bin_centers, bin_means, bin_stds

#make_poff(datetime.datetime(2024, 5, 2, 10, 5), 30, "40525", "/eos/user/j/jcapotor/RTDdata/calib/TGrad/POFF")
