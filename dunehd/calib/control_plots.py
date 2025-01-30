import os, sys
current_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(current_directory)
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

from rtd.src.calib.constructor import selection
from src.calib.utils.logFile import LogFile

pathToPlots = "/eos/user/j/jcapotor/RTDdata/ControlPlots/DUNE-HD"

log_file = LogFile(sheetname="DUNE-HD_LogFile")
conditions = {"CalibSetNumber":"1", "Type":"Cal", "Selection":"GOOD"}

selection = selection.Selection(log_file=log_file, **conditions)
for nrun, run in selection.runs.items():
    print(run.data, run.channels)