import os.path
import pandas as pd
import osmnx as ox
import taxicab as tc
import geopy.distance
import tqdm
import numpy as np


def get_distances(node_df: pd.DataFrame, df_point_name_column: str, df_lat_column_name: str,
                  df_long_column_name: str, graph_path: str, overwrite: bool = False, offset: float = 0.05,
                  km_eq_k: float = 5) -> pd.DataFrame:
    """
    Given a DataFrame containing point names, their latitude and logitude, calculates the adjacency matrix for the road
    network.

    :param node_df: The given DataFrame. Must contain the columns mentioned below:
    :param df_point_name_column: (column dtype: str) The name of the column that contains point names.
    :param df_lat_column_name: (column dtype: float) The name of the column that contains point latitudes.
    :param df_long_column_name: (column dtype: float) The name of the column that contains point logitudes.
    :param graph_path: Path to the generated .ml graph file.
    :param overwrite: Whether the graph .ml file should be overwritten (True) or not (False).
    :param offset: Specifies the degrees by which the graph's area should be expanded by, beyond its original bounding
    box (determined by the points' coordinates) in each direction.
    :param km_eq_k: Specifies at what kilometer the connectivity metric's second component (road distance) should
    drop below 0.5. The higher the km_eq_k, the more connected the network.
    :return: The adjacency matrix (zero diagonal).
    """

    ox.all_oneway = False
    ox.log_console = False

    if not os.path.exists(graph_path) or overwrite:
        G = ox.graph_from_bbox(north=node_df[df_lat_column_name].max() + offset,
                               south=node_df[df_lat_column_name].min() - offset,
                               east=node_df[df_long_column_name].max() + offset,
                               west=node_df[df_long_column_name].min() - offset,
                               network_type='drive')
        ox.save_graphml(G, filepath=graph_path)
    else:
        G = ox.load_graphml(graph_path)

    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    new_nodes = node_df[df_point_name_column].tolist()
    node_df.index = new_nodes

    road_distances = []
    vince_distances = []
    for i in tqdm.tqdm(new_nodes):  # origin -> dest
        try:
            orig = tuple(node_df.loc[i, [df_lat_column_name, df_long_column_name]].tolist())
            row_for_road_distances = []
            row_for_vince_distances = []
            for j in new_nodes:
                dest = tuple(node_df.loc[j, [df_lat_column_name, df_long_column_name]].tolist())
                if i == j:
                    row_for_road_distances.append(0)
                    row_for_vince_distances.append(0)
                else:
                    row_for_road_distances.append(tc.shortest_path(G, orig, dest)[0]/1000)
                    row_for_vince_distances.append(geopy.distance.geodesic(orig, dest).km)

            road_distances.append(row_for_road_distances)
            vince_distances.append(row_for_vince_distances)
        except Exception:
            road_distances.append([np.nan] * len(new_nodes))
            vince_distances.append([np.nan] * len(new_nodes))

    road_df = pd.DataFrame(road_distances, columns=new_nodes, index=new_nodes)
    vince_df = pd.DataFrame(vince_distances, columns=new_nodes, index=new_nodes)

    # calculate the metric
    eq_k = -km_eq_k / np.log(0.5)
    distance_metric_df = (vince_df / road_df) * np.exp(-road_df/eq_k)
    np.fill_diagonal(distance_metric_df.values, 0)

    return distance_metric_df
