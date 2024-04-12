import subprocess
import json
import pandas as pd

# Construct the curl command with the entire command as a single string
curl_command = 'curl http://vm-01.cern.ch:8080/sensor-dict | json_pp '

# Run the curl command
curl_output = subprocess.run(curl_command, capture_output=True, text=True, shell=True)

# Check if the command ran successfully
if curl_output.returncode == 0:
    # Print the output to see what's returned
    print("Curl command output:")
    data = curl_output.stdout
    data = json.loads(data)
    data = pd.DataFrame(data.items())
    filtered_rows = data[data[1].str.contains("TE0")]
    filtered_rows[1] = filtered_rows[1].apply(lambda x: x.split(":")[1].split(".")[0])
    filtered_rows.to_csv("name.csv", sep=";")
else:
    # Print an error message if the command failed
    print("Error: Curl command failed")
