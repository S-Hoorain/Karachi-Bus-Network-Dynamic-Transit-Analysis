"""
Find optimal test cases where road closures significantly impact shortest paths.

This script analyzes the Karachi bus network to:
1. Identify bottleneck edges (critical for many routes)
2. Find pairs of nodes where closing an edge forces a different path
3. Suggest test cases that clearly demonstrate algorithm behavior
"""

import networkx as nx
import pandas as pd
from algorithms import dijkstra_search
from graph_builder import build_karachi_bus_graph
from simulation import KarachiBusSim
import random

def analyze_network_structure():
    """Analyze the network to find critical edges and bottlenecks."""
    print("\n" + "="*80)
    print("ANALYZING NETWORK STRUCTURE FOR BOTTLENECK EDGES")
    print("="*80 + "\n")
    
    # Load graph
    G = build_karachi_bus_graph(
        'karachi_bus_network_node_data.csv',
        'karachi_bus_network_edge_list.csv'
    )
    
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")
    
    # 1. Identify high-centrality edges (betweenness centrality)
    print("Computing edge betweenness centrality (importance for routing)...")
    edge_betweenness = nx.edge_betweenness_centrality(G, weight='weight')
    
    # Sort by centrality
    top_edges = sorted(edge_betweenness.items(), key=lambda x: x[1], reverse=True)[:20]
    
    print("\nTop 20 Most Critical Edges (by betweenness centrality):")
    print("="*80)
    for i, ((u, v), centrality) in enumerate(top_edges, 1):
        edge_weight = G[u][v]['weight']
        print(f"{i:2d}. {u:20s} → {v:20s} | Centrality: {centrality:.6f} | Weight: {edge_weight:.2f} km")
    
    return G, top_edges

def find_affected_paths(G, edge_to_close):
    """Find all paths that use a specific edge."""
    u, v = edge_to_close
    
    # Get all nodes
    all_nodes = list(G.nodes())
    affected_count = 0
    example_paths = []
    
    for start in random.sample(all_nodes, min(100, len(all_nodes))):
        for end in random.sample(all_nodes, min(50, len(all_nodes))):
            if start == end:
                continue
            
            result = dijkstra_search(G, start, end)
            if result is not None:
                path, cost = result
                if path and len(path) > 1:
                    for i in range(len(path) - 1):
                        if path[i] == u and path[i+1] == v:
                            affected_count += 1
                            if len(example_paths) < 5:
                                example_paths.append((start, end, path, cost))
                            break
    
    return affected_count, example_paths

def test_path_change_after_closure(G, start_node, end_node):
    """Test a specific path before and after closing different edges."""
    # Get original path
    result = dijkstra_search(G, start_node, end_node)
    if result is None or result[0] is None:
        return None
    
    original_path, original_cost = result
    
    print(f"\nTesting route: {start_node} → {end_node}")
    print(f"Original path: {' → '.join(original_path)}")
    print(f"Original cost: {original_cost:.2f} km")
    
    test_results = []
    
    # Try closing each edge in the original path
    for i in range(len(original_path) - 1):
        edge = (original_path[i], original_path[i+1])
        original_weight = G[edge[0]][edge[1]]['weight']
        
        # Close the edge
        G[edge[0]][edge[1]]['weight'] = float('inf')
        
        # Find new path
        result = dijkstra_search(G, start_node, end_node)
        
        # Restore weight
        G[edge[0]][edge[1]]['weight'] = original_weight
        
        if result is not None and result[0] is not None:
            new_path, new_cost = result
            cost_increase = new_cost - original_cost
            cost_increase_pct = (cost_increase / original_cost * 100) if original_cost > 0 else 0
            
            test_results.append({
                'edge': edge,
                'original_cost': original_cost,
                'new_cost': new_cost,
                'cost_increase': cost_increase,
                'cost_increase_pct': cost_increase_pct,
                'original_path': original_path,
                'new_path': new_path,
                'path_changed': original_path != new_path
            })
        else:
            # No alternative path found
            test_results.append({
                'edge': edge,
                'original_cost': original_cost,
                'new_cost': float('inf'),
                'cost_increase': float('inf'),
                'cost_increase_pct': float('inf'),
                'original_path': original_path,
                'new_path': None,
                'path_changed': True
            })
    
    return test_results

def find_best_test_cases():
    """Find the best test cases by analyzing impact of closures."""
    G, top_edges = analyze_network_structure()
    
    print("\n" + "="*80)
    print("FINDING OPTIMAL TEST CASES")
    print("="*80)
    
    best_test_cases = []
    
    # Test paths through top 10 critical edges
    for edge_idx, (edge, centrality) in enumerate(top_edges[:10]):
        u, v = edge
        print(f"\nAnalyzing edge {edge_idx + 1}: {u} → {v}")
        
        affected_count, example_paths = find_affected_paths(G, edge)
        print(f"  ✓ This edge is used by ~{affected_count} different paths (sampled)")
        
        if example_paths:
            for start, end, path, cost in example_paths:
                test_result = test_path_change_after_closure(G, start, end)
                
                if test_result:
                    # Find the test case with highest impact
                    for tr in test_result:
                        if tr['path_changed'] and tr['cost_increase_pct'] > 0:
                            best_test_cases.append({
                                'start': start,
                                'end': end,
                                'edge_to_close': tr['edge'],
                                'cost_increase': tr['cost_increase'],
                                'cost_increase_pct': tr['cost_increase_pct'],
                                'original_path_length': len(tr['original_path']),
                                'new_path_length': len(tr['new_path']) if tr['new_path'] else float('inf')
                            })
    
    # Sort by cost increase percentage
    best_test_cases.sort(key=lambda x: x['cost_increase_pct'], reverse=True)
    
    print("\n" + "="*80)
    print("TOP 10 RECOMMENDED TEST CASES")
    print("(Routes where road closure has the biggest impact)")
    print("="*80 + "\n")
    
    for i, tc in enumerate(best_test_cases[:10], 1):
        print(f"{i}. Route: {tc['start']} → {tc['end']}")
        print(f"   Close edge: {tc['edge_to_close'][0]} → {tc['edge_to_close'][1]}")
        print(f"   Cost increase: {tc['cost_increase']:.2f} km ({tc['cost_increase_pct']:.1f}%)")
        print(f"   Path length change: {tc['original_path_length']} nodes → {tc['new_path_length']} nodes")
        print()
    
    # Save to CSV
    df = pd.DataFrame(best_test_cases[:20])
    df.to_csv('recommended_test_cases.csv', index=False)
    print(f"✓ Top 20 test cases saved to 'recommended_test_cases.csv'\n")
    
    return best_test_cases[:10]

def validate_test_case(start_node, end_node, edge_to_close):
    """Validate a specific test case and show detailed results."""
    print("\n" + "="*80)
    print("VALIDATING TEST CASE")
    print("="*80)
    print(f"\nTest: {start_node} → {end_node}")
    print(f"Edge to close: {edge_to_close[0]} → {edge_to_close[1]}\n")
    
    G = build_karachi_bus_graph(
        'karachi_bus_network_node_data.csv',
        'karachi_bus_network_edge_list.csv'
    )
    sim = KarachiBusSim(G)
    
    # Test with Dijkstra
    print("Testing Dijkstra algorithm:\n")
    
    # Original path
    result_orig = dijkstra_search(G, start_node, end_node)
    if result_orig is None or result_orig[0] is None:
        print(f"ERROR: No path found from {start_node} to {end_node}")
        return
    
    path_orig, cost_orig = result_orig
    print(f"BEFORE CLOSURE:")
    print(f"  Path: {' → '.join(path_orig)}")
    print(f"  Cost: {cost_orig:.2f} km")
    print(f"  Path length: {len(path_orig)} nodes")
    
    # Close the edge
    original_weight = G[edge_to_close[0]][edge_to_close[1]]['weight']
    G[edge_to_close[0]][edge_to_close[1]]['weight'] = float('inf')
    
    # New path
    result_new = dijkstra_search(G, start_node, end_node)
    
    if result_new is None or result_new[0] is None:
        print(f"\nAFTER CLOSURE:")
        print(f"  ✗ NO PATH FOUND (network disconnected for this route)")
        cost_new = float('inf')
        path_new = None
    else:
        path_new, cost_new = result_new
        print(f"\nAFTER CLOSURE:")
        print(f"  Path: {' → '.join(path_new)}")
        print(f"  Cost: {cost_new:.2f} km")
        print(f"  Path length: {len(path_new)} nodes")
    
    # Analysis
    print(f"\nIMPACT ANALYSIS:")
    if path_new is None:
        print(f"  ✓ Path disconnected (infinite cost)")
    else:
        cost_diff = cost_new - cost_orig
        cost_pct = (cost_diff / cost_orig * 100) if cost_orig > 0 else 0
        path_diff = len(path_new) - len(path_orig)
        
        print(f"  ✓ Cost increase: {cost_diff:.2f} km ({cost_pct:.1f}%)")
        print(f"  ✓ Path length change: {path_diff:+d} nodes")
        print(f"  ✓ Path changed: {path_orig != path_new}")
    
    # Restore weight
    G[edge_to_close[0]][edge_to_close[1]]['weight'] = original_weight
    
    print("\n" + "="*80)

if __name__ == "__main__":
    print("\n" + "█"*80)
    print("KARACHI BUS NETWORK - OPTIMAL TEST CASE FINDER")
    print("█"*80)
    
    # Find best test cases
    test_cases = find_best_test_cases()
    
    # Validate top 3 test cases
    if test_cases:
        for i, tc in enumerate(test_cases[:3], 1):
            print(f"\n{'='*80}")
            print(f"VALIDATING TEST CASE #{i}")
            print(f"{'='*80}")
            validate_test_case(tc['start'], tc['end'], tc['edge_to_close'])
