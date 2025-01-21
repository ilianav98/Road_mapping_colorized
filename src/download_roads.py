import osmnx as ox

# Configure OSMnx
ox.config(use_cache=True, log_console=True)

# Define the area of interest (Israel)
place_name = "Tel Aviv, Israel"

# Download the road network for cars (drivable roads)
road_network_drive = ox.graph_from_place(place_name, network_type='drive')

# Optionally, save it as a shapefile
ox.save_graph_shapefile(road_network_drive, filepath="israel_drivable_road_network_shapefile")

print("Drivable road network saved successfully!")
