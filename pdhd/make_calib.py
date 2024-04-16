from rtd.src.calib.constructor import system
from rtd.src.calib.utils.tools import makeRCalib

systems = ["lartgrad", "ln22tgrad", "ln23tgrad"]
readouts = ["ific", "cern"]

system = system.System(system_name="ln22tgrad")
system.save()

# readout = makeRCalib.ReadoutCalib(readout="ific")
# readout.save()

# readout = makeRCalib.ReadoutCalib(readout="cern")
# readout.save()