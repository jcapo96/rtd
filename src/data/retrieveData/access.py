from src.data.retrieveData import accessTools

class Access():
    """Connects to the database and retrieves data for the specified element.

    Parameters:
        detector (str): The name of the detector.
        elementId (str): The Slow Control ID of the sensor.
        startDay (str): The start date of the data retrieval. Format: DD-MM-YYYY.
        endDay (str): The end date of the data retrieval. Format: DD-MM-YYYY.
        startTime (str, optional): The start time of the data retrieval (HH:MM:SS). Default is None.
        endTime (str, optional): The end time of the data retrieval (HH:MM:SS). Default is None.
        FROM_CERN (bool, optional): Whether you are at CERN's network. Default is False.
    """

    def __init__(self, detector, elementId, startDay, endDay, startTime, endTime, FROM_CERN):
        self.detector = detector
        self.FROM_CERN = FROM_CERN
        self.elementId = elementId
        self.startDay = startDay
        self.endDay = endDay
        self.startTime = startTime
        self.endTime = endTime
        self.readData()

    def readData(self):
        """Read the data from the Slow Control and returns it as a pandas dataframe"""
        self.data = accessTools.getSlowControlData(self.detector, self.elementId, self.startDay, self.endDay, self.startTime, self.endTime, self.FROM_CERN)
        return self

# a = Access("np04", "47890412077338", "2024-04-01", "2024-04-01", "00:00:00", "00:01:00", FROM_CERN=True)
# print(a.data)