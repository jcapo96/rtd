import urllib.request, json, subprocess
from datetime import timedelta
import pandas as pd
import datetime

def convert_date_format(date_string):
    # Split the date string by '-'
    # print(date_string)
    parts = date_string.split('-')

    # Reorder the parts
    new_date_string = parts[2] + '-' + parts[1] + '-' + parts[0]

    return new_date_string

def accessViaPage(detector, elementId, startDay, endDay, startTime, endTime):
    """Generates a URL to access data via a web page.

    This function generates a URL to access data from the specified detector and element ID
    within the given time range via a web page.

    Parameters:
        detector (str): The name of the detector.
        elementId (str): The Slow Control ID of the sensor.
        startDay (datetime): The start day of the data retrieval.
        endDay (datetime): The end day of the data retrieval.

    Returns:
        str: The URL to access the data via a web page.
    """
    if endDay is None:
        endDay = startDay
    startDay = convert_date_format(startDay)
    endDay   = convert_date_format(endDay)
    # Adjust endDay if startDay and endDay are on the same date
    if (startDay == endDay) and (startTime is None or endTime is None):
        endDay = datetime.strptime(endDay, '%d-%m-%Y')
        endDay += timedelta(days=1)
        endDay = endDay.strftime('%d-%m-%Y')
    # Construct the URL based on the detector
    if detector.lower() == "np04":
        url = 'https://np04-slow-control.web.cern.ch/np04-slow-control/app/php-db-conn/histogramrange.conn.php?'
        url += 'elemId=' + str(elementId)
        if (startTime is not None) and (endTime is not None):
            url += '&start=' + startDay + "T" + startTime
            url += '&end=' + endDay + "T" + endTime
        else:
            url += '&start=' + startDay
            url += '&end=' + endDay
    return url

def accessViaCache(elementId, startDay, endDay, startTime, endTime):
    """
    Accesses data via cache from a specified endpoint.

    Parameters:
    - elementId (str): The identifier of the element.
    - startDay (str): The start date (YYYY-MM-DD) for retrieving data.
    - endDay (str): The end date (YYYY-MM-DD) for retrieving data.
    - startTime (str): The start time (HH:MM:SS) for retrieving data.
    - endTime (str): The end time (HH:MM:SS) for retrieving data.

    Returns:
    - data (dict): The retrieved data in pandas format.
    """
    if startDay is None:
        print("Error: You should provide a valid start date")
        return None
    startDateTime = (datetime.datetime.strptime(f"{startDay} {startTime}", "%Y-%m-%d %H:%M:%S")).strftime("%Y-%m-%d %H:%M:%S")
    endDateTime = (datetime.datetime.strptime(f"{endDay} {endTime}", "%Y-%m-%d %H:%M:%S")).strftime("%Y-%m-%d %H:%M:%S")
    # startDateTime = (datetime.datetime.strptime(f"{startDay} {startTime}", "%Y-%m-%d %H:%M:%S")).strftime("%Y-%m-%d %H:%M:%S")
    # endDateTime = (datetime.datetime.strptime(f"{endDay} {endTime}", "%Y-%m-%d %H:%M:%S")).strftime("%Y-%m-%d %H:%M:%S")
    startDay, startTime = startDateTime.split(" ")
    endDay, endTime = endDateTime.split(" ")

    if endDay is None:
        # If only startDay is provided, retrieve data for that day only
        curl_command = ['curl', f'http://vm-01.cern.ch:8080/day/{startDay}/{elementId}']
    elif startTime is None or endTime is None:
        # If both startDay and endDay are provided but not startTime or endTime, retrieve data for the specified date range
        curl_command = ['curl', f'http://vm-01.cern.ch:8080/range/{startDay}T00:00:00/{endDay}T23:59:59/{elementId}']
    else:
        # If all parameters are provided, retrieve data for the specified date range and time range
        curl_command = ['curl', f'http://vm-01.cern.ch:8080/range/{startDay}T{startTime}/{endDay}T{endTime}/{elementId}']

    # Execute the curl command
    curl_output = subprocess.run(curl_command, capture_output=True, text=True)
    print(curl_output)

    # Check if the curl command was successful
    if curl_output.returncode == 0:
        # Parse the JSON output
        data = json.loads(curl_output.stdout)
        data = pd.DataFrame(data.items(), columns=['epochTime', 'temp'])
        data['epochTime'] = data["epochTime"].astype("int64")/1000
        # print(data["epochTime"][0])
        # print(datetime.datetime.utcfromtimestamp(data["epochTime"][0]))
        return data
    else:
        print("Error: curl command failed")
        return None

def retrieveData(url):
    """Retrieves data from a specified URL and returns it as a DataFrame.

    This function retrieves data from the specified URL and converts it into a Pandas DataFrame.
    The URL is expected to return JSON-formatted data containing records with two fields: 'epochTime'
    and 'temp'. The function retrieves the data from the URL, parses it into JSON format, converts it
    into a DataFrame, and renames the columns as 'epochTime' and 'temp'. The resulting DataFrame is
    then returned.

    Parameters:
        url (str): The URL to retrieve data from.

    Returns:
        pandas.DataFrame: A DataFrame containing the retrieved data with columns 'epochTime' and 'temp'.
    """
    # Open the URL and read the response
    rr = urllib.request.urlopen(url)
    r = rr.read()
    # Parse the response as JSON
    res = json.loads(r)
    print(res)

    # Convert JSON data to a DataFrame
    data = pd.DataFrame(res['records'])
    data.columns = ["epochTime", "temp"]

    return data

def getSlowControlData(detector, elementId, startDay, endDay, startTime, endTime, FROM_CERN):
    """Retrieves slow control data for a specified detector and element ID within a given time range.

    This function retrieves slow control data for a specified detector and element ID within the
    given time range. The data retrieval method (either via cache or via a web page) depends on the
    value of the FROM_CERN parameter. If FROM_CERN is True, the function retrieves data via cache;
    otherwise, it retrieves data via a web page. The data is then retrieved using the appropriate
    method and returned as a DataFrame.

    Parameters:
        detector (str): The name of the detector.
        elementId (str): The Slow Control ID of the sensor.
        startDay (datetime): The start day of the data retrieval.
        endDay (datetime): The end day of the data retrieval.
        FROM_CERN (bool): Indicates whether the retrieval should be done from CERN.

    Returns:
        pandas.DataFrame: A DataFrame containing the retrieved slow control data with columns
        'epochTime' and 'temp'.
    """
    if FROM_CERN:
        data = accessViaCache(elementId, startDay, endDay, startTime, endTime)
    else:
        url = accessViaPage(detector, elementId, startDay, endDay, startTime, endTime)
        data = retrieveData(url)
        data["epochTime"] = data["epochTime"].apply(lambda x: x/1e3)
    return data

# data = getSlowControlData(detector="np04", elementId="47890328191258", startDay="2024-04-16", endDay="2024-04-16", startTime="00:00:00", endTime="00:01:00", FROM_CERN=False)
# data = getSlowControlData(detector="np04", elementId="47890328191258", startDay="2024-04-16", endDay="2024-04-16", startTime=None, endTime=None, FROM_CERN=False)
# data["epochTime"] = data["epochTime"].apply(lambda x: datetime.utcfromtimestamp(x/1000).strftime('%Y-%m-%d %H:%M:%S'))
# print(data)