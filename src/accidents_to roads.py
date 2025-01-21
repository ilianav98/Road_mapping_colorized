import geopandas as gpd
import pandas as pd

# Load the road layer and the accidents layer
roads = gpd.read_file("edges.shp")
accidents = gpd.read_file("accidents_2022_with_nearest_road_TLV.shp")

# Ensure the "ID" and "HUMRAT_TEU" columns are present in the accidents layer
if "ID" not in accidents.columns or "HUMRAT_TEU" not in accidents.columns:
    raise ValueError("The accidents layer must contain 'ID' and 'HUMRAT_TEU' fields.")

# Group accidents by 'ID' and sum 'HUMRAT_TEU'
accidents_sum = accidents.groupby("ID")["HUMRAT_TEU"].sum().reset_index()

# Merge the summed data with the roads layer on 'ID'
roads_with_risk = roads.merge(accidents_sum, on="ID", how="left")

# Fill NaN values with 0 for roads that have no associated accidents
roads_with_risk["HUMRAT_TEU"] = roads_with_risk["HUMRAT_TEU"].fillna(0)

# Save the result to a new shapefile or GeoJSON (optional)
roads_with_risk.to_file("roads_accidents_TLV.shp", driver="ESRI Shapefile")  # Change path and format as needed

print("Roads with risk values have been calculated and saved.")
