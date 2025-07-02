from src import baseClasses
import pandas as pd

class MUX():
    def __init__(self, dataset, boardNumber):
        self.dataset = dataset
        self.boardNumber = boardNumber
        self._info()
        self._data()

    def _info(self):
        self.info = pd.read_csv(f"/afs/cern.ch/work/j/jcapotor/software/rtd/pdhd/ana/mapping/baseline.csv", header=0)
        self.info = self.info[["SC-ID", "SYSTEM", "NAME", "CAL-ID"]]
        try:
            self.boardNumber = int(self.boardNumber)
        except:
            self.boardNumber = None
            print(f"ERROR: Board ({self.boardNumber}) not found")
        if self.boardNumber is not None:
            self.info = self.info.loc[(self.info["NAME"]==f"B{self.boardNumber}")&(self.info["SYSTEM"]=="CURRENT")].reset_index(drop=True)
            if len(self.info) > 0:
                self.scid = self.info["SC-ID"].values[0]
                self.id = self.info["CAL-ID"].values[0]
                self.name = self.info["NAME"].values[0]
                self.system = self.info["SYSTEM"].values[0]
            else:
                self.scid = None
                self.id = None
                self.name = None
                self.system = None
                #print(f"ERROR: Board ({self.boardNumber}) not found")
        else:
            self.scid = None
            self.id = None
            self.name = None
            self.system = None
        return self

    def _data(self):
        self.data = None
        if self.scid is not None:
            if self.scid in self.dataset.data.columns:
                self.data = self.dataset.data[self.scid]
            else:
                self.data = None
                print(f"ERROR: Board ({self.scid}) not found")
        return self

    def correct(self):
        if self.boardNumber == 1:
            self.data = self.data
        if self.boardNumber == 2:
            self.data.loc[(self.data.index >= pd.Timestamp("2024-05-03 21:20:00"))&(self.data.index < pd.Timestamp("2024-05-04 12:45:00"))] -= 0.00004
            self.data.loc[self.data.index >= pd.Timestamp("2024-05-10 15:00:00")] -= 0.00012
            self.data.loc[self.data.index >= pd.Timestamp("2024-05-30 11:00:00")] += 0.00003
            self.data.loc[(self.data.index >= pd.Timestamp("2024-05-31 16:35:00"))] -= 0.00005
            self.data.loc[self.data.index >= pd.Timestamp("2024-06-11 17:00:00")] += 0.00007
        return self