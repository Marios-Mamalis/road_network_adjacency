import osmnx as ox
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import folium

ox.all_oneway = True
ox.log_console = True


def visualize_points(new_node_df: pd.DataFrame, df_point_name_column: str, df_lat_column_name: str,
                     df_long_column_name: str):
    geo_df = gpd.GeoDataFrame(new_node_df, geometry=gpd.points_from_xy(new_node_df[df_long_column_name], new_node_df[df_lat_column_name]), crs="EPSG:4326")
    mapp = folium.Map(location=[geo_df[df_lat_column_name].mean(), geo_df[df_long_column_name].mean()], tiles="OpenStreetMap", zoom_start=10)

    geo_df_list = [[point.xy[1][0], point.xy[0][0]] for point in geo_df.geometry]
    i = 0
    for coordinates in geo_df_list:
        mapp.add_child(
            folium.Marker(
                location=coordinates,
                popup=f"Point name: {geo_df[df_point_name_column][i]} <br>",
                icon=folium.Icon(color="%s" % 'green'),
            )
        )
        i = i + 1

    mapp.show_in_browser()


df = pd.read_csv('data/sensors_test.csv')
visualize_points(df, 'unique_sensor', 'lat', 'long')
