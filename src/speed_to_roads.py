import geopandas as gpd

# Load the shapefile
shapefile_path = "roads_accidents_TLV.shp"
roads = gpd.read_file(shapefile_path)

# Define a function to calculate speed based on the "highway" field
def calculate_speed(highway):
    speed_dict = {
        "motorway": 90,
        "trunk": 70,
        "primary": 40,
        "secondary": 40,
        "tertiary": 30,
        "residential": 20,
        "unclassified": 10,
        "motorway_link": 55,
        "trunk_link": 45,
        "primary_link": 25,
        "secondary_link": 25,
        "tertiary_link": 15,
    }
    return speed_dict.get(highway, None)  # Return None if the highway type is not in the dictionary

# Create a new column "speed" and calculate values
roads["speed"] = roads["highway"].apply(calculate_speed)

# Save the updated shapefile
output_path = "TLV_roads_with_speeds.shp"
roads.to_file(output_path)

print(f"Updated shapefile saved to {output_path}")
