import os
import json
from .methods import RefMethod, TreeMethod

class System:
    """Represents a system with associated methods for loading, processing, and saving data."""

    def __init__(self, system_name):
        """
        Initializes a System instance.

        Parameters:
            system_name (str): The name of the system. -> Valid system names under ../calib/utils/logs/systems.json
        """
        # Set the path to the systems.json file
        self.pathToInfo = f"{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/utils/logs/systems.json"
        # Convert system name to uppercase
        self.systemName = system_name.upper()
        # Load information about the system
        self.info = self._load_info()
        # Initialize RefMethod and TreeMethod instances
        self.ref = RefMethod(info=self.info)
        self.tree = TreeMethod(info=self.info)

    def _load_info(self):
        """
        Loads system information from the systems.json file.

        Returns:
            dict: Information about the system.
        """
        with open(self.pathToInfo, 'r') as file:
            info = json.load(file)[self.systemName]
        return info

    def save(self, method="TREE"):
        """
        Saves system data to a JSON file.

        Parameters:
            method (str, optional): The method to use for saving data ('REF' or 'TREE'). Default is 'TREE'.
        """
        # Define the path for saving the JSON file
        path = f"/eos/user/j/jcapotor/RTDdata/calib/{self.systemName}_{method}"

        # Determine the data to save based on the specified method
        if method.upper() == "REF":
            # Generate calibration results using the RefMethod
            self.ref.make()
            data = self.ref.calresults
            rdata = self.ref.rcalresults
        elif method.upper() == "TREE":
            # Generate calibration results using the TreeMethod
            self.tree.make()
            data = self.tree.calresults
            rdata = self.tree.rcalresults

        # Write the data to the JSON file
        with open(f"{path}.json", "w") as json_file:
            json.dump(data, json_file, indent=4)

        with open(f"{path}_rcal.json", "w") as json_file:
            json.dump(rdata, json_file, indent=4)

        # Print a message indicating successful file write
        print(f"Dictionary has been written to {path}")
