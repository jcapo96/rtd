from src.calib.constructor.selection import Selection
from src.calib.utils.logFile import LogFile
import numpy as np
from tqdm import tqdm

class RefMethod:
    """Represents a reference method for calibration."""

    def __init__(self, info):
        """
        Initializes a RefMethod instance.

        Parameters:
            info (dict): Information about the reference method.
        """
        self.info = info
        self.refs = self.info["absolute_references"]
        self.calresults = {ref: {} for ref in self.refs}
        self.calerrors = {ref: {} for ref in self.refs}
        self.rcalresults = {ref: {} for ref in self.refs}

    def make(self):
        """
        Performs calibration computations and generates results.

        Returns:
            RefMethod: Instance of RefMethod with updated calibration results and errors.
        """
        # Create a LogFile instance for logging
        log_file = LogFile()

        # Iterate over calibration sets and conditions
        for calset, conditions in self.info["sets"].items():
            # Create a Selection instance for each set of conditions
            selection = Selection(log_file=log_file, **conditions)
            # Iterate over reference IDs
            for ref in self.refs:
                # Compute calibration constants for each reference
                selection.compute_calconst(ref=ref)
                # Iterate over sensor IDs in the current calibration set
                for id in self.info["ids"][calset]:
                    # Update calibration results and errors for each reference and sensor ID
                    if id not in self.calresults[ref].keys():
                        self.calresults[ref][id] = [selection.calconst[id]]
                        self.calerrors[ref][id] = [selection.calerr[id]]
                    else:
                        self.calresults[ref][id].append(selection.calconst[id])
                        self.calerrors[ref][id].append(selection.calerr[id])

        # Compute mean calibration results and errors
        for ref in self.refs:
            for id in self.calresults[ref].keys():
                self.calresults[ref][id] = np.mean(self.calresults[ref][id])
                if np.mean(self.calerrors[ref][id]) > np.std(self.calresults[ref][id]):
                    self.calerrors[ref][id] = np.mean(self.calerrors[ref][id])
                else:
                    self.calerrors[ref][id] = np.std(self.calresults[ref][id])

        return self

class TreeMethod:
    """Represents a tree method for calibration."""

    def __init__(self, info):
        """
        Initializes a TreeMethod instance.

        Parameters:
            info (dict): Information about the tree method.
        """
        self.info = info
        self.calresults = {}
        self.calerrors = {}
        self.rcalresults = {}

    def make(self):
        """
        Performs calibration computations and generates results using the tree method.

        Returns:
            TreeMethod: Instance of TreeMethod with updated calibration results and errors.
        """
        # Create a LogFile instance for logging
        log_file = LogFile()

        # Create a Selection instance for the second round sensors
        second_round_sens = Selection(log_file=log_file, **self.info["sets"]["second_round"])

        # Iterate over calibration sets and reference IDs from the first round
        for calset_ref, refs in self.info["ids"]["first_round"].items():
            # Create a Selection instance for the first round reference
            first_round_ref = Selection(log_file=log_file, **self.info["sets"]["first_round"][calset_ref])
            # Iterate over reference IDs
            with tqdm(total=len(refs)) as pbar:
                for ref in refs:
                    self.calresults[ref] = {}
                    self.calerrors[ref] = {}
                    self.rcalresults[ref] = {}
                    # Compute calibration constants for the first round reference
                    first_round_ref.compute_calconst(ref=ref)
                    # Iterate over calibration sets and sensor IDs from the first round
                    for calset_sens, sensors in self.info["ids"]["first_round"].items():
                        # if calset_sens == calset_ref:
                        #     # Use calibration constants of the first round reference for the same calibration set
                        #     for id in sensors:
                        #         self.calresults[ref][id] = [first_round_ref.calconst[id]]
                        #         self.calerrors[ref][id] = [first_round_ref.calerr[id]]

                        #         self.rcalresults[ref][id] = [first_round_ref.rcalconst[id]]
                        # elif calset_sens != calset_ref:
                            # Create a Selection instance for the first round sensors in a different calibration set
                        first_round_sens = Selection(log_file=log_file, **self.info["sets"]["first_round"][calset_sens])
                        # Iterate over raised sensors in the current calibration set
                        for raised_sens in self.info["raised_sensors"][calset_sens]:
                            # Compute calibration constants for the raised sensors
                            first_round_sens.compute_calconst(ref=raised_sens)
                            # Iterate over raised reference sensors in the reference calibration set
                            for raised_ref in self.info["raised_sensors"][calset_ref]:
                                # Compute calibration constants for the second round sensors
                                second_round_sens.compute_calconst(ref=raised_ref)
                                # Iterate over sensor IDs from the current calibration set
                                for id in sensors:
                                    # Calculate offsets and errors for the current sensor ID
                                    off3, off3_err = first_round_sens.calconst[id], first_round_sens.calerr[id]
                                    off2, off2_err = second_round_sens.calconst[raised_sens], second_round_sens.calerr[raised_sens]
                                    off1, off1_err = first_round_ref.calconst[raised_ref], first_round_ref.calerr[raised_ref]

                                    roff3 = first_round_sens.rcalconst[id]
                                    roff2 = second_round_sens.rcalconst[raised_sens]
                                    roff1 = first_round_ref.rcalconst[raised_ref]
                                    if id not in self.calresults[ref]:
                                        # Initialize calibration results and errors for the current sensor ID
                                        self.calresults[ref][id] = [off1 + off2 + off3]
                                        self.calerrors[ref][id] = [np.sqrt(off1_err**2 + off2_err**2 + off3_err**2)]

                                        self.rcalresults[ref][id] = [roff1 + roff2 + roff3]
                                    else:
                                        # Update calibration results and errors for the current sensor ID
                                        self.calresults[ref][id].append(off1 + off2 + off3)
                                        self.calerrors[ref][id].append(np.sqrt(off1_err**2 + off2_err**2 + off3_err**2))

                                        self.rcalresults[ref][id].append(roff1 + roff2 + roff3)
                    pbar.update(1)

        return self
