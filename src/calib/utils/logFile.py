import pandas as pd
import gspread, os
from oauth2client.service_account import ServiceAccountCredentials

class LogFile:
    def __init__(self,
                 spreadsheet_name='Calibration-LogFile',
                 sheetname="ProtoDUNE-HD_LogFile") -> None:
        self.keyfile_path = f"{os.path.dirname(__file__)}/logs/"
        self.spreadsheet_name = spreadsheet_name
        self.sheetname = sheetname
        self.log_file = self.download_logfile()

    def download_logfile(self):
        """
        Function to download data from a Google Sheets document.

        Parameters:
            sheetname (str): The name of the worksheet to download from the Google Sheets document.

        Returns:
            pandas.DataFrame: DataFrame containing the data from the specified worksheet.
        """
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(self.keyfile_path, 'keys.json'), scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open(self.spreadsheet_name)
            worksheet = next(ws for ws in spreadsheet.worksheets() if ws.title == self.sheetname)
            data = worksheet.get_all_values()
            return pd.DataFrame(data[1:], columns=data[0])
        except Exception as e:
            raise RuntimeError(f"An error occurred while downloading log file: {e}")

    def select_files(self, **kwargs):
            """
            Select files from a log file DataFrame based on given conditions.

            Parameters:
                kwargs (dict): Dictionary of column-value pairs specifying conditions for selection.
                    Values can be a single value or a list of values.

            Returns:
                pandas.DataFrame: DataFrame containing selected files based on the conditions.
            """
            try:
                selection = self.log_file.copy()
                for column, value in kwargs.items():
                    # Check if the value is a list
                    if isinstance(value, list):
                        # Use isin() to filter rows where the value of the column is in the list
                        selection = selection.loc[selection[column].isin(value)]
                    else:
                        # If the value is not a list, filter rows where the value of the column matches the single value
                        selection = selection.loc[selection[column] == value]
                return selection
            except Exception as e:
                raise RuntimeError(f"An error occurred while selecting files: {e}")
