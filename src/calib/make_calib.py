import os, sys, json
current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

from utils import LogFile
from constructor import Selection

pathToInfo = f"/afs/cern.ch/work/j/jcapotor/software/rtd/src/calib/utils/logs/systems.json"

with open(pathToInfo, 'r') as file:
    info = json.load(file)
log_file = LogFile()
s1 = Selection(log_file=log_file, **info["LN23TGRAD"]["sets"]["first_round"]["TGrad-1"])
s1.compute_calconst(ref="40525")

s2 = Selection(log_file=log_file, **info["LN23TGRAD"]["sets"]["first_round"]["TGrad-2"])
s2.compute_calconst(ref="39629")

s3 = Selection(log_file=log_file, **info["LN23TGRAD"]["sets"]["first_round"]["TGrad-3"])
s3.compute_calconst(ref="40533")

s4 = Selection(log_file=log_file, **info["LN23TGRAD"]["sets"]["first_round"]["TGrad-4"])
s4.compute_calconst(ref="39666")

s5 = Selection(log_file=log_file, **info["LN23TGRAD"]["sets"]["second_round"])
s5.compute_calconst(ref="39666")


path_to_save = "/eos/user/j/jcapotor/RTDdata/ProcessedData/TGrad/calib_test/"
with open(f"{path_to_save}LN23TGrad-1.json", "w") as outfile:
    json.dump(s1.calconst, outfile)

with open(f"{path_to_save}LN23TGrad-2.json", "w") as outfile:
    json.dump(s2.calconst, outfile)

with open(f"{path_to_save}LN23TGrad-3.json", "w") as outfile:
    json.dump(s3.calconst, outfile)

with open(f"{path_to_save}LN23TGrad-4.json", "w") as outfile:
    json.dump(s4.calconst, outfile)

with open(f"{path_to_save}LN23TGrad-21.json", "w") as outfile:
    json.dump(s5.calconst, outfile)