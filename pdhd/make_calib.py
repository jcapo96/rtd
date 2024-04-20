import os, sys
current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

from rtd.src.calib.constructor import system
from rtd.src.calib.utils.tools import makeRCalib

systems = ["lartgrad", "ln22tgrad", "ln23tgrad"]
readouts = ["ific", "cern"]

# for name in systems:
#     s = system.System(system_name=name)
#     s.save()

s = system.System(system_name="lartgrad")
s.save()

# readout = makeRCalib.ReadoutCalib(readout="ific")
# readout.save()

# readout = makeRCalib.ReadoutCalib(readout="cern")
# readout.save()