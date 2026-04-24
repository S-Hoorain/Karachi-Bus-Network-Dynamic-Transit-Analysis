import pandas as pd
import networkx as nx
import math


def haversine(lat1, lon1, lat2, lon2):

    # Calculates distance between two points on the Earth in kilometers. 
    # Used for initial edge weights.

    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def build_karachi_bus_graph(nodes_path, edges_path):
    # 1) Load Data
    nodes_df = pd.read_csv(nodes_path)
    edges_df = pd.read_csv(edges_path)

    # Convert coordinate columns to numeric floats before graph construction
    nodes_df['latit'] = pd.to_numeric(nodes_df['latit'], errors='coerce')
    nodes_df['long'] = pd.to_numeric(nodes_df['long'], errors='coerce')
    
    # Initialize Directed Graph
    G = nx.DiGraph()

    # 2) Add Nodes with Metadata (Lat/Lon)
    nodes_with_attrs = []
    for _, row in nodes_df.iterrows():
        lat = row['latit']
        lon = row['long']
        if pd.isna(lat) or pd.isna(lon):
            continue
        nodes_with_attrs.append((row['node'], {'pos': (float(lat), float(lon))}))
    G.add_nodes_from(nodes_with_attrs)

    # 3) Add Edges with Weights
    # We calculate distance as the initial weight (baseline travel time)
    for _, row in edges_df.iterrows():
        u, v = row['stop1'], row['stop2']
        
        # Get coordinates for weight calculation
        try:
            node_u = nodes_df.loc[nodes_df['node'] == u].iloc[0]
            node_v = nodes_df.loc[nodes_df['node'] == v].iloc[0]
            
            dist = haversine(node_u['latit'], node_u['long'], 
                             node_v['latit'], node_v['long'])
            
            # Add edge with attributes needed for your 3 algorithms
            G.add_edge(u, v, 
                       weight=dist, # Base distance
                       traffic_factor=1.0, # Dynamic multiplier for later
                       bus_name=row['bus_name'],
                       id=row.get('route_id', 'N/A'))
        except IndexError:
            # Handle cases where a stop in edges.csv isn't in nodes.csv
            continue

    return G

if __name__ == "__main__":
    nodes_file = 'karachi_bus_network_node_data.csv'
    edges_file = 'karachi_bus_network_edge_list.csv'

    karachi_graph = build_karachi_bus_graph(nodes_file, edges_file)
    print(f"Graph Construction Complete!")
    print(f"Total Stops (Nodes): {karachi_graph.number_of_nodes()}")
    print(f"Total Routes (Edges): {karachi_graph.number_of_edges()}")

    sample_stop = "quaidabad"
    if karachi_graph.has_node(sample_stop):
        print(f"\nRoutes leaving {sample_stop}:")
        for neighbor in karachi_graph.neighbors(sample_stop):
            edge_data = karachi_graph.get_edge_data(sample_stop, neighbor)
            print(f" -> {neighbor} via {edge_data['bus_name']} (Dist: {edge_data['weight']:.2f} km)")