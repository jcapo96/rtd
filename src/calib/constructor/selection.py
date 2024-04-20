import numpy as np
import os
from .run import Run
import matplotlib.pyplot as plt

class Selection:
    """Represents a selection of data for calibration."""

    def __init__(self, log_file, **kwargs):
        """
        Initializes a Selection instance.

        Parameters:
            log_file (LogFile): Instance of LogFile containing the data to be selected.
            **kwargs: Keyword arguments to specify selection criteria.
        """
        self.log_file = log_file
        # Select files based on the provided criteria
        self.selection = log_file.select_files(**kwargs)
        # Create a dictionary of runs from the selected files
        self.runs = {row["N_Run"]: Run(row) for index, row in self.selection.iterrows()}
        # Initialize a container for calibration constants
        self.container = {id: np.zeros(len(self.runs)) for nrun, run in self.runs.items() for id in run.ids}
        self.rcontainer = {id: np.zeros(len(self.runs)) for nrun, run in self.runs.items() for id in run.ids}

    def compute_calconst(self, ref):
        """
        Compute calibration constants for the specified reference.

        Parameters:
            ref (str): The reference for which calibration constants are to be computed.

        Returns:
            Selection: Instance of Selection with updated calibration constants and errors.
        """
        # Iterate over runs
        for nrun, run in enumerate(self.runs.values()):
            # Compute offsets for the reference
            run.compute_offset(ref=ref)
            run.compute_rcal(ref=ref)
            # Iterate over sensor IDs in the run
            for id in run.ids:
                # Store the computed offset in the container
                self.container[id][nrun] = run.offset[id].mean()
                if id in run.roffset.keys():
                    self.rcontainer[id][nrun] = run.roffset[id].mean()

        # Compute mean calibration constants and errors
        self.calconst = {key: np.mean(value) for key, value in self.container.items() if isinstance(value, np.ndarray)}
        self.calerr = {key: np.std(value) for key, value in self.container.items() if isinstance(value, np.ndarray)}
        self.rcalconst = {key: np.mean(value) for key, value in self.rcontainer.items() if isinstance(value, np.ndarray)}
        # Get the sensor IDs for which calibration constants are computed
        self.ids = self.calconst.keys()

        return self

    def draw_selection(self, ref, pathToSaveFolder=None):
        calib_set_number = self.selection['CalibSetNumber'].values[0]
        if not os.path.exists(f"{pathToSaveFolder}/{calib_set_number}"):
            os.makedirs(f"{pathToSaveFolder}/{calib_set_number}")

        for nrun, run in enumerate(self.runs.values()):
            temp_figure = plt.figure(figsize=(10, 10))
            run.compute_offset(ref=ref)
            run.compute_rcal(ref=ref)

            for id in run.ids:
                if id == "timeStamp":
                    continue
                plt.plot(run.offset["timeStamp"].values, run.offset[id].values, label=fr"{id}: $\sigma$={run.offset[id].std():.1f} mK")

            plt.title(f"Reference: {ref}", fontsize=20)
            plt.xlabel("Epoch Time (s)", fontsize=16, fontweight='bold')
            plt.ylabel("Offset (mK)", fontsize=16, fontweight='bold')
            plt.xticks(fontsize=14)
            plt.yticks(fontsize=14)
            plt.grid(True)
            plt.legend(ncol=2, loc="upper right", fontsize=12)

            # Save the figure
            temp_figure.savefig(f"{pathToSaveFolder}/{calib_set_number}/ref={ref}_run=run{nrun}.png")
            plt.close(temp_figure)



