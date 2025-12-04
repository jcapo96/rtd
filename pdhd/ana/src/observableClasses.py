from . import systemClasses, baseClasses
import pandas as pd
import numpy as np

class Bulk:
    def __init__(self, dataset, tini=None, tend=None):
        self.dataset = dataset

        # Set time range - use dataset range if not provided
        if tini is None:
            self.tini = dataset.data.index.min()
        else:
            self.tini = pd.to_datetime(tini)

        if tend is None:
            self.tend = dataset.data.index.max()
        else:
            self.tend = pd.to_datetime(tend)

        # Define constants
        self.ce_coordinates = (7855, 250, 5750)  # X, Y, Z
        self.gas_liquid_interface = 7600  # Y coordinate in mm
        self.distance_threshold = 1500  # mm
        self.center_coordinates = (4000, 4000, 4000)  # X, Y, Z for weighting

        # Get configurations that overlap with time range
        self.configurations = self._get_configurations()

        # Interactive calibration selection
        self.calib_dict = self._select_calibrations()

        # Load PIPE system to access inlet coordinates
        self.pipe_system = systemClasses.System(self.dataset, "PIPE")
        self.inlet_coordinates = self._get_inlet_coordinates()

        # Initialize bulk dictionary and metadata attributes
        self.bulk = {}
        self.sensors = {}  # Dictionary of all sensors used across configurations
        self.systems = {}  # Dictionary of systems used per configuration

    def _get_configurations(self):
        """Get all configurations that overlap with the dataset time range"""
        logFile = baseClasses.LogFile().configurations
        logFile["Start"] = pd.to_datetime(logFile["Start"])
        logFile["End"] = pd.to_datetime(logFile["End"])

        # Filter configurations that overlap with our time range
        overlapping_configs = logFile.loc[
            (logFile["Start"] <= self.tend) & (logFile["End"] >= self.tini)
        ]

        if len(overlapping_configs) == 0:
            raise ValueError("No configurations found for the selected time range")

        configurations = {}
        for index, config_row in overlapping_configs.iterrows():
            config_name = config_row["Configuration"]

            # Read the configuration mapping file
            mapping = baseClasses.Configuration(config_name).mapping

            # Extract systems with sensors on boards 1-4
            hp_systems = mapping.loc[mapping["BOARD"] <= 4]["SYSTEM"].unique()

            # Store configuration info with adjusted time bounds
            configurations[config_name] = {
                "tini": max(config_row["Start"], self.tini),
                "tend": min(config_row["End"], self.tend),
                "systems": hp_systems,
                "mapping": mapping
            }

        return configurations

    def _select_calibrations(self):
        """Interactive calibration selection for each system in each configuration"""
        calib_dict = {}
        previous_inputs = {}  # Store previous inputs for each system

        print("Configuration-aware bulk temperature setup:")
        print("=" * 50)

        for config_name, config_info in self.configurations.items():
            print(f"\nConfiguration: {config_name}")
            print(f"Time period: {config_info['tini']} to {config_info['tend']}")

            # Get board information for each system in this configuration
            mapping = config_info["mapping"]
            hp_systems_info = mapping.loc[mapping["BOARD"] <= 4].groupby("SYSTEM")["BOARD"].unique()

            calib_dict[config_name] = {}

            for system_name in config_info["systems"]:
                if system_name == "EMPTY":
                    continue

                boards = hp_systems_info.get(system_name, [])
                boards_str = ", ".join(map(str, sorted(boards))) if len(boards) > 0 else "No boards 1-4"

                # Get channels for this system
                system_channels = mapping.loc[mapping["SYSTEM"] == system_name]["SC-ID"].unique()
                channels_str = ", ".join(system_channels[:10])  # Show first 10 channels
                if len(system_channels) > 10:
                    channels_str += f" ... (+{len(system_channels)-10} more)"

                print(f"\n  System: {system_name}")
                print(f"  Boards 1-4: {boards_str}")
                print(f"  Channels: {channels_str}")

                # Determine default value
                if system_name not in previous_inputs:
                    default_calib = "FIRST_POFF_PRECISION"
                else:
                    default_calib = previous_inputs[system_name]

                while True:
                    calib_name = input(f"  Enter calibration name for {system_name} [{default_calib}]: ").strip()
                    if not calib_name:  # Use default if empty input
                        calib_name = default_calib

                    if calib_name:
                        calib_dict[config_name][system_name] = calib_name
                        previous_inputs[system_name] = calib_name  # Store for next time
                        break
                    else:
                        print("  Please enter a valid calibration name.")

        return calib_dict

    def _get_inlet_coordinates(self):
        """Extract coordinates of inlet sensors (1-I, 2-I, 3-I, 4-I) from PIPE system"""
        inlet_coords = {}
        inlet_names = ["1-I", "2-I", "3-I", "4-I"]

        for sensor_id, sensor in self.pipe_system.sensors.items():
            if sensor.name in inlet_names:
                inlet_coords[sensor.name] = (sensor.X, sensor.Y, sensor.Z)

        return inlet_coords

    def _calculate_distance(self, x1, y1, z1, x2, y2, z2):
        """Calculate 3D Euclidean distance between two points"""
        return np.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)

    def _is_high_precision(self, sensor):
        """Check if sensor is high-precision by excluding low-precision sensors"""
        # Debug: print sensor info for first few sensors
        if hasattr(self, '_debug_count'):
            self._debug_count += 1
        else:
            self._debug_count = 1

        if self._debug_count <= 5:  # Print details for first 5 sensors
            print(f"      Debug sensor {sensor.id}: name='{sensor.name}', system='{sensor.system}', board={sensor.board}, calibrated={sensor.is_calib_corrected}")

        # Exclude sensors with "F" in name (low-precision APA sensors)
        if "F" in sensor.name:
            return False

        # Exclude WALL system sensors
        if sensor.system == "WALL":
            return False

        # Exclude FLOOR system sensors
        if sensor.system == "FLOOR":
            return False

        # Only include sensors from boards 1-4
        if not (1 <= sensor.board <= 4):
            return False

        # Only include sensors that have been calibrated
        if not sensor.is_calib_corrected:
            return False

        return True

    def _is_far_from_inlets(self, sensor):
        """Check if sensor is >1500mm from all 4 inlets"""
        for inlet_name, (ix, iy, iz) in self.inlet_coordinates.items():
            distance = self._calculate_distance(sensor.X, sensor.Y, sensor.Z, ix, iy, iz)
            if distance <= self.distance_threshold:
                return False
        return True

    def _is_far_from_ce(self, sensor):
        """Check if sensor is >1500mm from CE using 3D distance"""
        ce_x, ce_y, ce_z = self.ce_coordinates
        distance = self._calculate_distance(sensor.X, sensor.Y, sensor.Z, ce_x, ce_y, ce_z)
        return distance > self.distance_threshold

    def _is_below_interface(self, sensor):
        """Check if sensor Y < 6100 (7600 - 1500)"""
        return sensor.Y < (self.gas_liquid_interface - self.distance_threshold)

    def _calculate_gaussian_weights(self, bulk_sensors):
        """Calculate Gaussian weights for sensors based on distance from center coordinates"""
        if len(bulk_sensors) == 0:
            return {}

        # Calculate distances from center for all sensors
        distances = {}
        for sensor_id, sensor in bulk_sensors.items():
            distance = self._calculate_distance(
                sensor.X, sensor.Y, sensor.Z,
                self.center_coordinates[0], self.center_coordinates[1], self.center_coordinates[2]
            )
            distances[sensor_id] = distance

        # Find the minimum distance (closest sensor to center)
        min_distance = min(distances.values())

        # Calculate Gaussian weights
        # Using sigma = min_distance/2 to create a reasonable spread
        sigma = max(min_distance / 2, 100)  # Minimum sigma of 100mm to avoid division by zero

        weights = {}
        for sensor_id, distance in distances.items():
            # Gaussian weight: exp(-((distance - min_distance)^2) / (2 * sigma^2))
            weight = np.exp(-((distance - min_distance)**2) / (2 * sigma**2))
            weights[sensor_id] = weight

        # Normalize weights so their sum equals 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {sensor_id: weight / total_weight for sensor_id, weight in weights.items()}

        return weights


    def define(self):
        """Define bulk temperature for each configuration using high-precision sensors that meet spatial criteria"""
        print("\nProcessing configurations for bulk temperature calculation...")

        for config_name, config_info in self.configurations.items():
            print(f"\nProcessing configuration: {config_name}")

            # Initialize bulk sensors for this configuration
            bulk_sensors = {}

            # Load only the systems relevant to this configuration
            for system_name in config_info["systems"]:
                if system_name == "EMPTY":
                    continue

                # Get calibration name for this specific system
                calib_name = self.calib_dict[config_name][system_name]

                try:
                    system = systemClasses.System(self.dataset, system_name)
                    system.calibrate(calibName=calib_name)

                    if system.sensors is None or len(system.sensors) == 0:
                        continue

                    # Apply filtering criteria to sensors in this system
                    system_sensors_count = 0
                    high_precision_count = 0
                    far_from_inlets_count = 0
                    far_from_ce_count = 0
                    below_interface_count = 0
                    final_count = 0

                    for sensor_id, sensor in system.sensors.items():
                        system_sensors_count += 1

                        if self._is_high_precision(sensor):
                            high_precision_count += 1

                            if self._is_far_from_inlets(sensor):
                                far_from_inlets_count += 1

                                if self._is_far_from_ce(sensor):
                                    far_from_ce_count += 1

                                    if self._is_below_interface(sensor):
                                        below_interface_count += 1
                                        bulk_sensors[sensor_id] = sensor
                                        final_count += 1

                    print(f"    {system_name}: {system_sensors_count} total sensors")
                    print(f"      High precision (boards 1-4, calibrated): {high_precision_count}")
                    print(f"      Far from inlets (>1500mm): {far_from_inlets_count}")
                    print(f"      Far from CE (>1500mm): {far_from_ce_count}")
                    print(f"      Below interface (Y<6100mm): {below_interface_count}")
                    print(f"      Final qualifying sensors: {final_count}")

                except Exception as e:
                    print(f"Warning: Could not process system {system_name} for configuration {config_name}: {e}")

            if len(bulk_sensors) == 0:
                print(f"Warning: No sensors meet the bulk temperature criteria for configuration {config_name}")
                # Get list of systems used in this configuration
                systems_used = list(config_info["systems"])
                if "EMPTY" in systems_used:
                    systems_used.remove("EMPTY")

                # Store empty sensors and systems as class attributes
                self.sensors[config_name] = {}
                self.systems[config_name] = systems_used

                self.bulk[config_name] = {
                    'data': pd.DataFrame(columns=["temp", "err"]),
                    'weights': {}
                }
                continue

            # Create DataFrame with sensor data for this configuration
            config_df = pd.DataFrame()
            for sensor_id, sensor in bulk_sensors.items():
                sensor_df = sensor.data.squeeze()
                config_df[sensor_id] = sensor_df

            # Calculate Gaussian weights based on distance from center
            weights = self._calculate_gaussian_weights(bulk_sensors)

            # Calculate weighted mean and error
            config_df['temp'] = 0.0
            config_df['err'] = 0.0

            for sensor_id in bulk_sensors.keys():
                if sensor_id in config_df.columns:
                    weight = weights.get(sensor_id, 0)
                    config_df['temp'] += weight * config_df[sensor_id]

            # Calculate weighted standard deviation
            # For weighted std: sqrt(sum(w_i * (x_i - weighted_mean)^2) / sum(w_i))
            for sensor_id in bulk_sensors.keys():
                if sensor_id in config_df.columns:
                    weight = weights.get(sensor_id, 0)
                    config_df['err'] += weight * (config_df[sensor_id] - config_df['temp'])**2

            config_df['err'] = np.sqrt(config_df['err'])

            # Get list of systems used in this configuration
            systems_used = list(config_info["systems"])
            if "EMPTY" in systems_used:
                systems_used.remove("EMPTY")

            # Store sensors and systems as class attributes
            self.sensors[config_name] = bulk_sensors
            self.systems[config_name] = systems_used

            # Store bulk data with weights
            self.bulk[config_name] = {
                'data': config_df[['temp', 'err']],
                'weights': weights
            }

            print(f"Configuration {config_name}: {len(bulk_sensors)} sensors included from systems {systems_used}")

        return self
