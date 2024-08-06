import osmnx as ox
import pandas as pd
import geopandas as gpd
import folium

ox.all_oneway = True
ox.log_console = True

def visualize_points(new_node_df: pd.DataFrame, df_point_name_column: str, df_lat_column_name: str,
                     df_long_column_name: str, sp_annot: [str, ...]) -> None:
    """
    Given a DataFrame containing point names, their latitude and logitude, creates an interactive visualization of the
    points on a map on top of OpenStreetMap tiles.

    :param new_node_df: The given DataFrame. Must contain the columns mentioned below:
    :param df_point_name_column: (column dtype: str) The name of the column that contains point names.
    :param df_lat_column_name: (column dtype: float) The name of the column that contains point latitudes.
    :param df_long_column_name: (column dtype: float) The name of the column that contains point logitudes.
    :param sp_annot: Names of points that should be annotated differently from the rest (red, instead of green).
    :return: None
    """

    geo_df = gpd.GeoDataFrame(new_node_df, geometry=gpd.points_from_xy(new_node_df[df_long_column_name], new_node_df[df_lat_column_name]), crs="EPSG:4326")
    mapp = folium.Map(location=[geo_df[df_lat_column_name].mean(), geo_df[df_long_column_name].mean()], tiles="OpenStreetMap", zoom_start=10)

    geo_df_list = [[point.xy[1][0], point.xy[0][0]] for point in geo_df.geometry]
    i = 0
    for coordinates in geo_df_list:
        point_name = geo_df[df_point_name_column][i]
        mapp.add_child(
            folium.Marker(
                location=coordinates,
                popup=f"Point name: {point_name} <br>",
                icon=folium.Icon(color="%s" % 'green') if point_name not in sp_annot else folium.Icon(color="%s" % 'red'),
            )
        )
        i = i + 1

    mapp.show_in_browser()
