import os.path
import pandas as pd
import osmnx as ox
import taxicab as tc
import geopy.distance
import tqdm
import numpy as np


def get_distances(new_node_df: pd.DataFrame, df_point_name_column: str, df_lat_column_name: str,
                  df_long_column_name: str, graph_path: str, offset: float = 0.05) -> (pd.DataFrame, pd.DataFrame):

    ox.all_oneway = False
    ox.log_console = False

    if not os.path.exists(graph_path):
        G = ox.graph_from_bbox(north=new_node_df[df_lat_column_name].max() + offset,
                               south=new_node_df[df_lat_column_name].min() - offset,
                               east=new_node_df[df_long_column_name].max() + offset,
                               west=new_node_df[df_long_column_name].min() - offset,
                               network_type='drive')
        ox.save_graphml(G, filepath=graph_path)
    else:
        G = ox.load_graphml(graph_path)

    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    new_nodes = new_node_df[df_point_name_column].tolist()
    new_node_df.index = new_nodes

    road_distances = []
    vince_distances = []
    for i in tqdm.tqdm(new_nodes):  # origin -> dest
        try:
            orig = tuple(new_node_df.loc[i, [df_lat_column_name, df_long_column_name]].tolist())
            row_for_road_distances = []
            row_for_vince_distances = []
            for j in new_nodes:
                dest = tuple(new_node_df.loc[j, [df_lat_column_name, df_long_column_name]].tolist())
                if i == j:
                    row_for_road_distances.append(0)
                    row_for_vince_distances.append(0)
                else:
                    row_for_road_distances.append(tc.shortest_path(G, orig, dest)[0])
                    row_for_vince_distances.append(geopy.distance.geodesic(orig, dest).km * 1000)

            road_distances.append(row_for_road_distances)
            vince_distances.append(row_for_vince_distances)

        except Exception:
            road_distances.append([np.nan] * len(new_nodes))
            vince_distances.append([np.nan] * len(new_nodes))


    road_df = pd.DataFrame(road_distances, columns=new_nodes, index=new_nodes)
    vince_df = pd.DataFrame(vince_distances, columns=new_nodes, index=new_nodes)

    return road_df, vince_df


def calculate_distance_metric(vince_distances_df: pd.DataFrame, road_network_distances_df: pd.DataFrame) -> pd.DataFrame:
    distance_metric_df = vince_distances_df/road_network_distances_df
    np.fill_diagonal(distance_metric_df.values, 0)

    print(vince_distances_df)
    print(road_network_distances_df)
    print(distance_metric_df)

    return distance_metric_df


def scale_adjacency_matrix(distance_metric_df: pd.DataFrame) -> pd.DataFrame:
    pass

df = pd.read_csv('data/sensors_test.csv')
road, vince = get_distances(df, 'unique_sensor', 'lat', 'long', 'data/test.ml')
calculate_distance_metric(vince, road)
