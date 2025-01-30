    import datetime

    def time_to_seconds(timestamp):
        """
        Convert a timestamp string to seconds since epoch.

        Parameters:
            timestamp (str): Timestamp string in the format "MM/DD/YYYY-HH:MM:SS AM/PM" or "DD/MM/YYYY-HH:MM:SS".

        Returns:
            int: Seconds since epoch.
        """
        try:
            # Try parsing timestamp with AM/PM designation
            dt = datetime.datetime.strptime(timestamp, "%m/%d/%Y-%I:%M:%S %p")
        except ValueError:
            try:
                # Try parsing timestamp without AM/PM designation
                dt = datetime.datetime.strptime(timestamp, "%d/%m/%Y-%H:%M:%S")
            except ValueError:
                raise ValueError("Invalid timestamp format")

        # Convert to seconds since epoch
        return int(dt.timestamp())