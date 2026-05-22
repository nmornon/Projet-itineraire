import pandas as pd
import folium
from conversion_gpx import convert_gpx_to_csv

# Chargement strava via le module
convert_gpx_to_csv("4_06.gpx", "strava_temp.csv")
strava = pd.read_csv("strava_temp.csv")
strava_pts = list(zip(strava["Latitude"].astype(float), strava["Longitude"].astype(float)))

df_brut = pd.read_csv("synced_imu_gnss.csv")
brut_pts = list(zip(df_brut["latitude"], df_brut["longitude"]))

# Chargement acquisition CSV 
df = pd.read_csv("kalman_outputs/kalman_result.csv")
acq_pts = list(zip(df["latitude"], df["longitude"]))

# Chargement acquisition CSV 
dsav = pd.read_csv("kalman_outputs/savgol_result.csv")
sav_pts = list(zip(dsav["latitude"], dsav["longitude"]))

# Carte
m = folium.Map(location=strava_pts[0], zoom_start=17)

folium.PolyLine(brut_pts, color="red", weight=2, tooltip="GPS de Base (Bruité)").add_to(m)
folium.PolyLine(strava_pts, color="orange", weight=3, tooltip="Strava").add_to(m)
folium.PolyLine(acq_pts,    color="blue",   weight=3, tooltip="Acquisition").add_to(m)
folium.PolyLine(sav_pts,    color="green",   weight=3, tooltip="Savgol").add_to(m)

m.save("map_both.html")
print("Carte enregistrée : map_both.html")

