"""
Test script that validates algorithm behavior with real road closures.

This script:
1. Uses test cases discovered by find_best_test_cases.py
2. Tests all three algorithms before/after road closure
3. Shows clear evidence of path changes
4. Measures performance impact
"""

import pandas as pd
import time
import os
from algorithms import dijkstra_search, lpa_star_search, approx_apsp_search
from graph_builder import build_karachi_bus_graph
from simulation import KarachiBusSim

def run_algorithm_test(G, start, end, algorithm_name, algorithm_func, **kwargs):
    """Run a single algorithm and return results."""
    try:
        start_time = time.perf_counter()
        result = algorithm_func(G, start, end, **kwargs)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        if result is None:
            return None, float('inf'), latency_ms
        
        if len(result) >= 2:
            path, cost = result[0], result[1]
        else:
            return None, float('inf'), latency_ms
        
        return path, cost, latency_ms
    except Exception as e:
        print(f"    ERROR in {algorithm_name}: {str(e)}")
        return None, float('inf'), 0

def test_single_case(test_case_id, start_node, end_node, edge_to_close):
    """Test a single case with all three algorithms."""
    print(f"\n{'='*80}")
    print(f"TEST CASE #{test_case_id}")
    print(f"{'='*80}")
    print(f"Route: {start_node} → {end_node}")
    print(f"Edge to close: {edge_to_close[0]} → {edge_to_close[1]}\n")
    
    # Load fresh graph
    G = build_karachi_bus_graph(
        'karachi_bus_network_node_data.csv',
        'karachi_bus_network_edge_list.csv'
    )
    sim = KarachiBusSim(G)
    
    results = {
        'test_case': test_case_id,
        'start': start_node,
        'end': end_node,
        'edge': str(edge_to_close)
    }
    
    print("PHASE 1: BEFORE CLOSURE")
    print("-" * 80)
    
    # Store original edge weight
    original_weight = G[edge_to_close[0]][edge_to_close[1]]['weight']
    
    # Test all algorithms before closure
    dijkstra_path_before, dijkstra_cost_before, dijkstra_time_before = run_algorithm_test(
        G, start_node, end_node, "Dijkstra", dijkstra_search
    )
    
    lpa_path_before, lpa_cost_before, lpa_time_before = run_algorithm_test(
        G, start_node, end_node, "LPA*", lpa_star_search, previous_search_data=None
    )
    
    approx_path_before, approx_cost_before, approx_time_before = run_algorithm_test(
        G, start_node, end_node, "Approx-APSP", approx_apsp_search
    )
    
    if dijkstra_path_before is None:
        print(f"ERROR: No path found before closure. Skipping this test case.")
        return None
    
    print(f"Dijkstra:     {dijkstra_cost_before:8.2f} km | {dijkstra_time_before:8.4f} ms | {len(dijkstra_path_before)} nodes")
    print(f"LPA*:         {lpa_cost_before:8.2f} km | {lpa_time_before:8.4f} ms | {len(lpa_path_before) if lpa_path_before else 'N/A'} nodes")
    print(f"Approx-APSP:  {approx_cost_before:8.2f} km | {approx_time_before:8.4f} ms | {len(approx_path_before) if approx_path_before else 'N/A'} nodes")
    
    print(f"\nDijkstra path: {' → '.join(dijkstra_path_before[:5])}{'...' if len(dijkstra_path_before) > 5 else ''}")
    
    # Close the edge
    print("\n" + "PHASE 2: AFTER CLOSURE (Edge set to infinite weight)")
    print("-" * 80)
    G[edge_to_close[0]][edge_to_close[1]]['weight'] = float('inf')
    
    # Test all algorithms after closure
    dijkstra_path_after, dijkstra_cost_after, dijkstra_time_after = run_algorithm_test(
        G, start_node, end_node, "Dijkstra", dijkstra_search
    )
    
    lpa_path_after, lpa_cost_after, lpa_time_after = run_algorithm_test(
        G, start_node, end_node, "LPA*", lpa_star_search, previous_search_data=None
    )
    
    approx_path_after, approx_cost_after, approx_time_after = run_algorithm_test(
        G, start_node, end_node, "Approx-APSP", approx_apsp_search
    )
    
    if dijkstra_path_after is None:
        print("✗ NO PATH FOUND (network disconnected for this route)")
        dijkstra_cost_after = float('inf')
    else:
        print(f"Dijkstra:     {dijkstra_cost_after:8.2f} km | {dijkstra_time_after:8.4f} ms | {len(dijkstra_path_after)} nodes")
        print(f"  → Path: {' → '.join(dijkstra_path_after[:5])}{'...' if len(dijkstra_path_after) > 5 else ''}")
    
    if lpa_path_after is None:
        print(f"LPA*:         NO PATH (disconnected)")
    else:
        print(f"LPA*:         {lpa_cost_after:8.2f} km | {lpa_time_after:8.4f} ms | {len(lpa_path_after)} nodes")
    
    if approx_path_after is None:
        print(f"Approx-APSP:  NO PATH (disconnected)")
    else:
        print(f"Approx-APSP:  {approx_cost_after:8.2f} km | {approx_time_after:8.4f} ms | {len(approx_path_after)} nodes")
    
    print("\n" + "IMPACT ANALYSIS")
    print("-" * 80)
    
    if dijkstra_path_after is None:
        print("✓ Dijkstra:     Path DISCONNECTED (infinite cost)")
        dijkstra_change_pct = 100
        dijkstra_changed = True
    else:
        dijkstra_change = dijkstra_cost_after - dijkstra_cost_before
        dijkstra_change_pct = (dijkstra_change / dijkstra_cost_before * 100) if dijkstra_cost_before > 0 else 0
        dijkstra_changed = dijkstra_path_before != dijkstra_path_after
        status = "CHANGED" if dijkstra_changed else "SAME"
        print(f"✓ Dijkstra:     {status} (+{dijkstra_change_pct:.1f}% cost)")
    
    if lpa_path_after is None:
        lpa_changed = True
        print(f"✓ LPA*:         Path DISCONNECTED")
    else:
        lpa_changed = lpa_path_before != lpa_path_after
        status = "CHANGED" if lpa_changed else "SAME"
        lpa_change = lpa_cost_after - lpa_cost_before if lpa_cost_before > 0 else 0
        lpa_change_pct = (lpa_change / lpa_cost_before * 100) if lpa_cost_before > 0 and lpa_cost_after != float('inf') else 0
        print(f"✓ LPA*:         {status} (+{lpa_change_pct:.1f}% cost)")
    
    if approx_path_after is None:
        approx_changed = True
        print(f"✓ Approx-APSP:  Path DISCONNECTED")
    else:
        approx_changed = approx_path_before != approx_path_after
        status = "CHANGED" if approx_changed else "SAME"
        approx_change = approx_cost_after - approx_cost_before if approx_cost_before > 0 else 0
        approx_change_pct = (approx_change / approx_cost_before * 100) if approx_cost_before > 0 and approx_cost_after != float('inf') else 0
        print(f"✓ Approx-APSP:  {status} (+{approx_change_pct:.1f}% cost)")
    
    # Store results
    results['dijkstra_before'] = dijkstra_cost_before
    results['dijkstra_after'] = dijkstra_cost_after
    results['dijkstra_changed'] = dijkstra_changed
    results['lpa_before'] = lpa_cost_before
    results['lpa_after'] = lpa_cost_after
    results['lpa_changed'] = lpa_changed
    results['approx_before'] = approx_cost_before
    results['approx_after'] = approx_cost_after
    results['approx_changed'] = approx_changed
    
    return results

def main():
    print("\n" + "█"*80)
    print("KARACHI BUS NETWORK - ROAD CLOSURE VALIDATION TEST")
    print("█"*80)
    print("\nThis script tests algorithms with actual road closures to verify")
    print("that the algorithms properly adapt to network changes.\n")
    
    # Check if recommended test cases exist
    if not os.path.exists('recommended_test_cases.csv'):
        print("ERROR: 'recommended_test_cases.csv' not found.")
        print("Please run 'find_best_test_cases.py' first to discover optimal test cases.\n")
        return
    
    # Load test cases
    df_cases = pd.read_csv('recommended_test_cases.csv')
    print(f"Loaded {len(df_cases)} recommended test cases from 'recommended_test_cases.csv'\n")
    
    # Run tests
    test_results = []
    
    for idx, row in df_cases.iterrows():
        start = row['start']
        end = row['end']
        
        # Parse edge string (comes as "'(u, v)'" or similar)
        edge_str = str(row['edge_to_close'])
        # Extract u and v
        parts = edge_str.strip("()' ").split(',')
        edge_u = parts[0].strip().strip("'\"")
        edge_v = parts[1].strip().strip("'\"")
        edge = (edge_u, edge_v)
        
        result = test_single_case(idx + 1, start, end, edge)
        if result:
            test_results.append(result)
    
    # Summary
    print("\n" + "█"*80)
    print("TEST SUMMARY")
    print("█"*80 + "\n")
    
    if test_results:
        df_results = pd.DataFrame(test_results)
        
        dijkstra_changed_count = df_results['dijkstra_changed'].sum()
        lpa_changed_count = df_results['lpa_changed'].sum()
        approx_changed_count = df_results['approx_changed'].sum()
        
        print(f"Total test cases run: {len(test_results)}")
        print(f"\nAlgorithms that adapted to road closure:")
        print(f"  Dijkstra:    {dijkstra_changed_count}/{len(test_results)} paths changed ✓" if dijkstra_changed_count > 0 else f"  Dijkstra:    {dijkstra_changed_count}/{len(test_results)} paths changed ✗")
        print(f"  LPA*:        {lpa_changed_count}/{len(test_results)} paths changed ✓" if lpa_changed_count > 0 else f"  LPA*:        {lpa_changed_count}/{len(test_results)} paths changed ✗")
        print(f"  Approx-APSP: {approx_changed_count}/{len(test_results)} paths changed ✓" if approx_changed_count > 0 else f"  Approx-APSP: {approx_changed_count}/{len(test_results)} paths changed ✗")
        
        # Save results
        df_results.to_csv('validation_results.csv', index=False)
        print(f"\n✓ Detailed results saved to 'validation_results.csv'")

if __name__ == "__main__":
    main()
