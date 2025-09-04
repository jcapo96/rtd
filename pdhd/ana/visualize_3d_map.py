import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import datetime
import matplotlib.pyplot as plt
import pandas as pd
from src import baseClasses, systemClasses, sensorClasses, muxClasses
import datetime
import numpy as np
from tqdm import tqdm
import pickle
import warnings
from scipy.interpolate import RegularGridInterpolator
warnings.filterwarnings("ignore", category=FutureWarning)
plt.style.use("style.mplstyle")

dataset = baseClasses.Data()
mask = (
    ((dataset.data.index > datetime.datetime(2024, 4, 30)) & (dataset.data.index < datetime.datetime(2024, 5, 15))) |
    ((dataset.data.index > datetime.datetime(2024, 11, 20)) & (dataset.data.index < datetime.datetime(2024, 12, 10)))
)

dataset.data = dataset.data.loc[mask]
dataset.err = dataset.err.loc[mask]

tgrad = systemClasses.System(dataset=dataset, name="TGRAD")
apa = systemClasses.System(dataset=dataset, name="APA")
prm = systemClasses.System(dataset=dataset, name="PRM")
pipe = systemClasses.System(dataset=dataset, name="PIPE")
pp = systemClasses.System(dataset=dataset, name="PP")
hawai = systemClasses.System(dataset=dataset, name="HAWAI")

tgrad.calibrate(calibName="SECOND_POFF_OCTOBER")
apa.calibrate(calibName="SECOND_POFF_OCTOBER")
prm.calibrate(calibName="SECOND_POFF_OCTOBER")
pipe.calibrate(calibName="SECOND_POFF_OCTOBER")
pp.calibrate(calibName="SECOND_POFF_OCTOBER")
hawai.calibrate(calibName="SECOND_POFF_EMPTY")

# 1. Make Profiles (Assuming the profiles are already generated with .makeProfiles)
# Example: Replace with actual profile data
tgrad.makeProfiles(tini=datetime.datetime(2024, 11, 29, 12, 0, 0), tend=datetime.datetime(2024, 11, 29, 12, 30, 0))
hawai.makeProfiles(tini=datetime.datetime(2024, 12, 6, 10, 0, 0), tend=datetime.datetime(2024, 12, 6, 10, 30, 0))
apa.makeProfiles(tini=datetime.datetime(2024, 11, 29, 12, 0, 0), tend=datetime.datetime(2024, 11, 29, 12, 30, 0))
pipe.makeProfiles(tini=datetime.datetime(2024, 11, 29, 12, 0, 0), tend=datetime.datetime(2024, 11, 29, 12, 30, 0))
prm.makeProfiles(tini=datetime.datetime(2024, 11, 29, 12, 0, 0), tend=datetime.datetime(2024, 11, 29, 12, 30, 0))
pp.makeProfiles(tini=datetime.datetime(2024, 11, 29, 12, 0, 0), tend=datetime.datetime(2024, 11, 29, 12, 30, 0))

# 2. Masks for APA1, APA2, APA3, APA4, PIPE (same as the original plot)
mask1 = apa.profiles["name"].str.contains("APA1", na=False) & ~apa.profiles["name"].str.contains("F", na=False)
mask2 = apa.profiles["name"].str.contains("APA2", na=False) & ~apa.profiles["name"].str.contains("F", na=False)
mask3 = apa.profiles["name"].str.contains("APA3", na=False) & ~apa.profiles["name"].str.contains("F", na=False)
mask4 = apa.profiles["name"].str.contains("APA4", na=False) & ~apa.profiles["name"].str.contains("F", na=False)
mask5 = pipe.profiles["name"].str.contains("-", na=False) & ~pipe.profiles["name"].str.contains("I", na=False)

# 3. Collect the profiles' data (applying the same masks)
all_profiles = []

# Function to collect data for each profile
def collect_profile_data(profile, mask=None, label="", color=""):
    if mask is not None:
        profile = profile[mask]
    X = profile["X"].values
    Y = profile["Y"].values
    Z = profile["Z"].values
    temp = profile["temp"].values
    all_profiles.append((X, Y, Z, temp, label, color))

# Collecting data for each profile (with the masks)
collect_profile_data(tgrad.profiles, None, "TGRAD", 'tab:blue')
collect_profile_data(hawai.profiles, None, "HAWAI", 'tab:brown')
collect_profile_data(apa.profiles, mask1, "APA1", 'tab:green')
collect_profile_data(apa.profiles, mask2, "APA2", 'tab:red')
collect_profile_data(apa.profiles, mask3, "APA3", 'tab:purple')
collect_profile_data(apa.profiles, mask4, "APA4", 'tab:orange')
collect_profile_data(pipe.profiles, mask5, "PIPE", 'tab:cyan')
collect_profile_data(prm.profiles, None, "PRM", 'tab:purple')
collect_profile_data(pp.profiles, None, "PUMP", 'tab:magenta')

# 4. Prepare the data for interpolation
# Combine all X, Y, Z, and temperature values into a single array for interpolation
X_all = np.concatenate([X for X, Y, Z, temp, label, color in all_profiles])
Y_all = np.concatenate([Y for X, Y, Z, temp, label, color in all_profiles])
Z_all = np.concatenate([Z for X, Y, Z, temp, label, color in all_profiles])
temp_all = np.concatenate([temp for X, Y, Z, temp, label, color in all_profiles])

# 5. Create a grid for interpolation
# Define the grid of X, Y, Z values where we will interpolate
x_grid = np.linspace(min(X_all), max(X_all), 100)
y_grid = np.linspace(min(Y_all), max(Y_all), 100)
z_grid = np.linspace(min(Z_all), max(Z_all), 100)

# Create a meshgrid from the grid
X_grid, Y_grid, Z_grid = np.meshgrid(x_grid, y_grid, z_grid)

# 6. Interpolate the temperature data onto the grid using griddata
temperature_grid = griddata(
    (X_all, Y_all, Z_all),
    temp_all,
    (X_grid, Y_grid, Z_grid),
    method='linear'
)

# 7. Flatten the grid for surface plotting
X_grid_flat = X_grid.flatten()
Y_grid_flat = Y_grid.flatten()
Z_grid_flat = Z_grid.flatten()

# 8. 2D projection of the interpolation on the plane defined by point1 and point2

# Define the two points that define the plane in (X, Z)
point1 = np.array([0, 0])
point2 = np.array([8000, 8000])

# Compute the direction vector of the line in (X, Z)
direction = point2 - point1
line_length = np.linalg.norm(direction)
direction_unit = direction / line_length

# Define the number of points along the line and along Y
num_line_points = 200
num_y_points = 100

# Distance along the line from point1 to point2
distances = np.linspace(0, line_length, num_line_points)
# Y values to scan
y_vals = np.linspace(min(Y_all), max(Y_all), num_y_points)

# Build grid of (distance, Y)
dist_grid, y_grid_proj = np.meshgrid(distances, y_vals)
# Compute corresponding (X, Z) for each distance
x_proj = point1[0] + dist_grid * direction_unit[0]
z_proj = point1[1] + dist_grid * direction_unit[1]

# Prepare the interpolator
interp_func = RegularGridInterpolator(
    (x_grid, y_grid, z_grid),
    temperature_grid,
    bounds_error=False,
    fill_value=np.nan
)

# Build the points for interpolation: shape (num_y_points*num_line_points, 3)
interp_points = np.column_stack([
    x_proj.ravel(),
    y_grid_proj.ravel(),
    z_proj.ravel()
])

# Interpolate temperature at each (X, Y, Z) on the plane
temp_proj = interp_func(interp_points).reshape(y_grid_proj.shape)

# Plot: X axis is distance from point1, Y axis is Y coordinate, color is temperature
fig, ax = plt.subplots(figsize=(10, 6))
c = ax.pcolormesh(dist_grid, y_grid_proj, temp_proj, shading='auto', cmap='viridis')
ax.set_xlabel("Distance from point1 [mm]")
ax.set_ylabel("Y [mm]")
ax.set_title("Temperature projection on plane from [1514,861] to [7265,6858]")
fig.colorbar(c, ax=ax, label="Temperature [K]")
plt.tight_layout()
plt.show()
