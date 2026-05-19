import pandas as pd
import folium
from conversion_gpx import convert_gpx_to_csv

# Chargement strava via le module
convert_gpx_to_csv("Acquisition_4_48.gpx", "strava_temp.csv")
strava = pd.read_csv("strava_temp.csv")
strava_pts = list(zip(strava["Latitude"].astype(float), strava["Longitude"].astype(float)))

# Chargement acquisition CSV 
df = pd.read_csv("synced_imu_gnss_clean.csv")
acq_pts = list(zip(df["latitude"], df["longitude"]))

# Carte
m = folium.Map(location=strava_pts[0], zoom_start=17)

folium.PolyLine(strava_pts, color="orange", weight=3, tooltip="Strava").add_to(m)
folium.PolyLine(acq_pts,    color="blue",   weight=3, tooltip="Acquisition").add_to(m)

m.save("map_both.html")
print("Carte enregistrée : map_both.html")

