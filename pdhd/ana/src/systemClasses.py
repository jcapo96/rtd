from src import sensorClasses
import pandas as pd
from tqdm import tqdm
import datetime

class System():
    def __init__(self, dataset, name=None, sensor_ids=None, sensor_names=None):
        self.dataset = dataset
        self.name = name
        self.sensor_ids = sensor_ids
        self.sensor_names = sensor_names
        self.is_single_profile = False
        self.is_multiple_profiles = False
        self._info()
        self._data()

    def _info(self):
        self.system = pd.read_csv(f"mapping/baseline.csv", header=0)

        if self.name is not None:
            # Original behavior: filter by system name
            self.system = self.system.loc[self.system["SYSTEM"]==self.name].reset_index(drop=True)
        elif self.sensor_ids is not None:
            # Filter by sensor IDs
            self.system = self.system.loc[self.system["CAL-ID"].isin(self.sensor_ids)].reset_index(drop=True)
        elif self.sensor_names is not None:
            # Filter by sensor names
            self.system = self.system.loc[self.system["NAME"].isin(self.sensor_names)].reset_index(drop=True)
        else:
            # If no criteria provided, use all sensors
            print("WARNING: No system name, sensor IDs, or sensor names provided. Using all sensors.")

        if len(self.system) == 0:
            self.system = None
            if self.name is not None:
                print(f"ERROR: System ({self.name}) not found")
            elif self.sensor_ids is not None:
                print(f"ERROR: Sensor IDs {self.sensor_ids} not found")
            elif self.sensor_names is not None:
                print(f"ERROR: Sensor names {self.sensor_names} not found")
        return self

    def _data(self):
        self.sensors = {}
        if self.system is not None:
            # Determine system name for progress bar
            system_name = self.name if self.name is not None else "Custom"
            for index, row in tqdm(self.system.iterrows(), desc=f"Initializing {system_name} Sensors", total=len(self.system), unit="sensor"):
                self.sensors[int(row["CAL-ID"])] = sensorClasses.Sensor(self.dataset, row["CAL-ID"])
        if len(self.sensors) > 0:
            self.ids = self.sensors.keys()
        return self

    def muxEqualization(self, equalizationName="LAST_SUM", equalizationSumName="LAST_SUM"):
        if len(self.sensors) > 0:
            system_name = self.name if self.name is not None else "Custom"
            for index, value in tqdm(self.sensors.items(), desc=f"Equalizing {system_name} Sensors", unit="sensor"):
                self.sensors[index] = value.muxEqualization(equalizationName=equalizationName, equalizationSumName=equalizationSumName)
        return self

    def muxContinuity(self, equalizationName="FIRST_POFF_39644_39619_39614_40200_39607_39669", equalizationSumName="HP-OFFSETS"):
        if len(self.sensors) > 0:
            system_name = self.name if self.name is not None else "Custom"
            for index, value in tqdm(self.sensors.items(), desc=f"Continuity {system_name} Sensors", unit="sensor"):
                self.sensors[index] = value.muxContinuity(equalizationName=equalizationName, equalizationSumName=equalizationSumName)
        return self

    def tempCalibration(self, calibName="LAR2023_TREE_AVG", ref="40525"):
        if len(self.sensors)>0:
            system_name = self.name if self.name is not None else "Custom"
            for index, value in tqdm(self.sensors.items(), desc=f"Calibrating {system_name} Sensors - Calibration Name: {calibName}", unit="sensor"):
                self.sensors[index] = value.tempCalibration(calibName=calibName, ref=ref)
        return self

    def calibrate(self, calibName="LAR2023_TREE_AVG", ref="40525", equalizationName="LAST_SUM", equalizationSumName="LAST_SUM"):
        self.muxEqualization(equalizationName=equalizationName, equalizationSumName=equalizationSumName)
        self.tempCalibration(calibName=calibName, ref=ref)
        return self

    def makeProfiles(self, tini=None, tend=None, deltat=30):
        if tini is not None and tend is not None and len(self.sensors) > 0:
            profiles_data = []
            for index, sensor in self.sensors.items():
                temperature = sensor.data.loc[(sensor.data.index >= tini) & (sensor.data.index <= tend)]
                if not temperature.empty:
                    profiles_data.append({
                        "X": sensor.X,
                        "Y": sensor.Y,
                        "Z": sensor.Z,
                        "name": sensor.name,
                        "temp": temperature.mean(),
                        "err": temperature.sem()
                    })
            self.profiles = pd.DataFrame.from_records(profiles_data)
            self.is_single_profile = True

        elif tini is None or tend is None:
            profiles_data = {}
            t = min(sensor.data.index.min() for sensor in self.sensors.values())
            max_t = max(sensor.data.index.max() for sensor in self.sensors.values())

            num_steps = (max_t - t).total_seconds() // (deltat * 60)
            system_name = self.name if self.name is not None else "Custom"
            progress = tqdm(total=int(num_steps), desc=f"Calculating {system_name} temperature profiles every {deltat} minutes: ", unit="step")

            while t < max_t:
                profiles_data[t] = []
                for index, sensor in self.sensors.items():
                    temperature = sensor.data.loc[
                        (sensor.data.index >= t) & (sensor.data.index < t + datetime.timedelta(minutes=deltat))
                    ]
                    if not temperature.empty:
                        profiles_data[t].append({
                            "X": sensor.X,
                            "Y": sensor.Y,
                            "Z": sensor.Z,
                            "temp": temperature.mean(),
                            "err": temperature.sem()
                        })

                profiles_data[t] = pd.DataFrame.from_records(profiles_data[t])
                t += datetime.timedelta(minutes=deltat)
                progress.update(1)

            progress.close()
            self.profiles = profiles_data
            self.is_multiple_profiles = True

        return self

    def profile_rms_vs_reference(self, tini=None, tend=None, deltat=30, ref_idx=0):
        """
        Generates profiles (multiple, over time), selects one as reference (by order, default first),
        computes the chi-squared between each profile and the reference for coordinate-matched sensors.
        Only considers shape differences: each profile (including reference) is normalized by subtracting its mean temperature.
        Uses variance per point as err_prof^2 + err_ref^2, skipping points with zero/NaN variance.
        Stores the resulting DataFrame in self.stability and also returns it.
        Returns:
            DataFrame: index=datetime/timestamps, columns=['chi2', 'ndof', 'chi2_ndof']
        """
        self.makeProfiles(tini=tini, tend=tend, deltat=deltat)  # handles both modes; focus on multiple

        if not getattr(self, 'is_multiple_profiles', False):
            raise ValueError('No multiple profiles generated. Ensure tini/tend are not both provided, or remove them.')

        # List of time keys (profile steps)
        times = list(self.profiles.keys())
        if len(times) == 0:
            raise ValueError('No profiles generated.')
        ref_time = times[ref_idx]
        ref_df = self.profiles[ref_time].set_index(['X','Y','Z'])
        # Normalize reference profile to its mean (shape only)
        if not ref_df.empty:
            ref_mean = ref_df['temp'].mean()
            ref_df_normalized = ref_df.copy()
            ref_df_normalized['temp'] = ref_df['temp'] - ref_mean
        else:
            ref_df_normalized = ref_df.copy()

        chi2_rows = []
        for t, prof in self.profiles.items():
            if prof.empty or ref_df_normalized.empty:
                chi2 = float('nan')
                ndof = 0
            else:
                prof_df = prof.set_index(['X','Y','Z'])
                # Normalize current profile to its mean (shape only)
                prof_mean = prof_df['temp'].mean()
                prof_df_normalized = prof_df.copy()
                prof_df_normalized['temp'] = prof_df['temp'] - prof_mean

                common_idx = prof_df_normalized.index.intersection(ref_df_normalized.index)
                if len(common_idx) == 0:
                    chi2 = float('nan')
                    ndof = 0
                else:
                    # Extract aligned series (normalized temperatures)
                    dtemp = prof_df_normalized.loc[common_idx, 'temp'] - ref_df_normalized.loc[common_idx, 'temp']
                    # Variance from both profiles (err columns exist in makeProfiles output)
                    var_prof = prof_df_normalized.loc[common_idx, 'err'] ** 2 if 'err' in prof_df_normalized.columns else pd.Series(0.0, index=common_idx)
                    var_ref = ref_df_normalized.loc[common_idx, 'err'] ** 2 if 'err' in ref_df_normalized.columns else pd.Series(0.0, index=common_idx)
                    var = var_prof.add(var_ref, fill_value=0.0)
                    # Valid points: positive, finite variance
                    valid = var.replace([float('inf'), -float('inf')], float('nan')).dropna()
                    valid_idx = valid[valid > 0].index
                    if len(valid_idx) == 0:
                        chi2 = float('nan')
                        ndof = 0
                    else:
                        chi2 = ((dtemp.loc[valid_idx] ** 2) / valid.loc[valid_idx]).sum()
                        ndof = len(valid_idx)
            chi2_ndof = (chi2 / ndof) if (ndof and chi2 == chi2) else float('nan')
            chi2_rows.append({'timestamp': t, 'chi2': chi2, 'ndof': ndof, 'chi2_ndof': chi2_ndof})
        df = pd.DataFrame(chi2_rows).set_index('timestamp')
        self.stability = df
        return df

