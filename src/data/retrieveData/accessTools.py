import urllib.request, json, subprocess
from datetime import timedelta
import pandas as pd
from datetime import datetime

def accessViaPage(detector, elementId, startDay, endDay):
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
    startDay = datetime.strptime(startDay, "%d-%m-%Y")
    endDay   = datetime.strptime(endDay, "%d-%m-%Y")
    # Adjust endDay if startDay and endDay are on the same date
    if startDay.date() == endDay.date():
        endDay += timedelta(days=1)

    # Construct the URL based on the detector
    if detector.lower() == "np04":
        url = 'https://np04-slow-control.web.cern.ch/np04-slow-control/app/php-db-conn/histogramrange.conn.php?'
        url += 'elemId=' + str(elementId)
        url += '&start=' + startDay.strftime("%d-%m-%Y")
        url += '&end=' + endDay.strftime("%d-%m-%Y")

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

    # Check if the curl command was successful
    if curl_output.returncode == 0:
        # Parse the JSON output
        data = json.loads(curl_output.stdout)
        data = pd.DataFrame(data.items(), columns=['epochTime', 'temp'])
        data['epochTime'] = data["epochTime"].astype("int64")/1000
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
        url = accessViaPage(detector, elementId, startDay, endDay)
        data = retrieveData(url)
    return data
