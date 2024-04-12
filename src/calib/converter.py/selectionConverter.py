import ROOT

class SelectionConverter():
    def __init__(self, selection) -> None:
        self.selection = selection

    def dump(self):
        for index, run in self.selection.runs.items():
            pass