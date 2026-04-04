import networkx as nx
from datetime import datetime, timedelta
from graph_builder import build_karachi_bus_graph
from simulation import KarachiBusSim
from algorithms import dijkstra_search, lpa_star_search, approx_apsp_search
from metrics import MetricsEvaluator

# Create a dictionary to hold search states for different routes
lpa_memory_cache = {}

def run_experiment_cycle(sim, evaluator, start_node, end_node, experiment_id):
    # Runs a full comparison cycle Static vs. Dynamic.
    global lpa_memory_cache
    route_key = f"{start_node}->{end_node}"

    print(f"\nExperiment {experiment_id}: {start_node} to {end_node}")

    # CONTROL GROUP (BASELINE)
    # runs Dijkstra function
    # records ms it took
    # saves  shortest distance in km to the logger
    
    # 1) Measuring Dijkstra (Baseline)
    path_d, cost_d, time_d = evaluator.measure_execution(
        "Dijkstra", dijkstra_search, sim.base_graph, start_node, end_node
    )
    if path_d is None:
        print(f"WARNING: No path found from {start_node} to {end_node} (cost: {cost_d}). Skipping experiment.")
        return  # Skip the rest of the experiment for this route
    
    evaluator.log_experiment(experiment_id, "Dijkstra", time_d, cost_d, is_dynamic_update=False)
    print(f"Static Dijkstra: {cost_d:.2f} km in {time_d:.4f} ms")

    # 2) Measuring LPA* (Initial/Static Search)
    # captures initial search state (memory) for the route.
    # We pass None for memory because it's the first time
    path_l, cost_l, time_l, memory = evaluator.measure_execution(
        "LPA*", lpa_star_search, sim.base_graph, start_node, end_node, previous_search_data=None
    )
    if path_l is None:
        print(f"WARNING: No path found from {start_node} to {end_node} with LPA*. Skipping experiment.")
        return
    
    # Store the result in our cache for the dynamic phase
    lpa_memory_cache[route_key] = memory 
    evaluator.log_experiment(experiment_id, "LPA*", time_l, cost_l, is_dynamic_update=False)

    # 3) Dynamic event simulation (Road/Stop Congestion or Closure)
    event = sim.generate_random_event()
    print(f"EVENT TRIGGERED: {event.event_type.upper()} at {event.affected_edges[0][0]}")

    # 4) Re-running Dijkstra (The 'Brute Force' Dynamic Approach)
    path_d2, cost_d2, time_d2 = evaluator.measure_execution(
        "Dijkstra", dijkstra_search, sim.base_graph, start_node, end_node
    )
    if path_d2 is None:
        print(f"WARNING: No path found after event from {start_node} to {end_node}. Skipping dynamic comparison.")
        return
    
    evaluator.log_experiment(experiment_id, "Dijkstra", time_d2, cost_d2, is_dynamic_update=True)

    # 5) Running LPA* (Incremental Update)
    # Now we pass the memory we saved from the static run
    # this allows the algorithm to only update affected nodes.
    previous_data = lpa_memory_cache.get(route_key)
    
    path_l2, cost_l2, time_l2, updated_mem = evaluator.measure_execution(
        "LPA*", lpa_star_search, sim.base_graph, start_node, end_node, previous_search_data=previous_data
    )
    if path_l2 is None:
        print(f"WARNING: No path found with LPA* after event from {start_node} to {end_node}. Skipping.")
        return
    
    # Update cache with new values for next time (e.g. recovery phase)
    lpa_memory_cache[route_key] = updated_mem
    evaluator.log_experiment(experiment_id, "LPA*", time_l2, cost_l2, is_dynamic_update=True)

    # EXPERIMENTAL GROUP (APPROXIMATION)
    # captures the speed of the approximate search.
    # 6) Measure Your (1+e) Approx
    path_a, cost_a, time_a = evaluator.measure_execution(
        "Approx-APSP", approx_apsp_search, sim.base_graph, start_node, end_node, epsilon=0.2
    )
    if path_a is None:
        print(f"WARNING: No path found with Approx-APSP from {start_node} to {end_node}.")
        stretch = float('inf')
    else:
        evaluator.log_experiment(experiment_id, "Approx-APSP", time_a, cost_a, is_dynamic_update=True)
        # 7) Calculating Stretch
        stretch = evaluator.calculate_stretch(cost_a, cost_d2)
    
    print(f"Dynamic Comparison: LPA* took {time_l2:.4f}ms | Approx-APSP Stretch: {stretch:.2f}x")

def main():
    # 1) Setup
    G = build_karachi_bus_graph('karachi_bus_network_node_data.csv', 'karachi_bus_network_edge_list.csv')
    sim = KarachiBusSim(G)
    evaluator = MetricsEvaluator()
    
    test_routes = [("quaidabad", "tower"), ("sohrab_goth", "power_house")] 

    for i, (start, end) in enumerate(test_routes):
        # DISRUPTION PHASE (Testing Dijkstra's robustness to changes)
        print(f"\nSCENARIO {i+1}: DISRUPTION PHASE")
        
        # Run comparison while road is blocked
        run_experiment_cycle(sim, evaluator, start, end, f"{i+1}_blocked")

        # RECOVERY PHASE (Testing LPA*'s strength)
        print(f"\nSCENARIO {i+1}: RECOVERY PHASE")
        
        # Manually expire the event to test repair logic
        for e in sim.active_events:
            e.end_time = datetime.now() - timedelta(seconds=1)
        
        # calling step to revert weights
        if sim.step():
            print("Traffic cleared! Measuring algorithm recovery speed")
            run_experiment_cycle(sim, evaluator, start, end, f"{i+1}_recovered")

    evaluator.save_results("karachi_final_results.csv")

if __name__ == "__main__":
    main()