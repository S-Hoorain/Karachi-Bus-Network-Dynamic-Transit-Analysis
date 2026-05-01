import networkx as nx
import os
import random
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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

    # Initialize path variables
    path_d = path_l = path_d2 = path_l2 = path_a = None
    cost_d = cost_l = cost_d2 = cost_l2 = cost_a = float('inf')
    time_d = time_l = time_d2 = time_l2 = time_a = 0
    stretch = float('inf')

    # CONTROL GROUP (BASELINE)
    # 1) Measuring Dijkstra (Baseline)
    path_d, cost_d, time_d = evaluator.measure_execution(
        "Dijkstra", dijkstra_search, sim.base_graph, start_node, end_node
    )
    
    if path_d is None:
        print(f"WARNING: No baseline path found from {start_node} to {end_node}. Experiment may be incomplete.")
    else:
        evaluator.log_experiment(experiment_id, "Dijkstra", time_d, cost_d, is_dynamic_update=False)
        print(f"Static Dijkstra: {cost_d:.2f} km in {time_d:.4f} ms")

    # 2) Measuring LPA* (Initial/Static Search)
    path_l, cost_l, time_l, memory = evaluator.measure_execution(
        "LPA*", lpa_star_search, sim.base_graph, start_node, end_node, previous_search_data=None
    )
    
    if path_l is None:
        print(f"WARNING: No LPA* path found from {start_node} to {end_node}.")
    else:
        # Store the result in our cache for the dynamic phase
        lpa_memory_cache[route_key] = memory 
        evaluator.log_experiment(experiment_id, "LPA*", time_l, cost_l, is_dynamic_update=False)

    # 3) Dynamic event simulation (Road/Stop Congestion or Closure)
    # Use targeted event that MUST affect the Dijkstra path
    event = sim.generate_targeted_event(path_d)
    print(f"EVENT TRIGGERED: {event.event_type.upper()} affecting {len(event.affected_edges)} edge(s)")

    # 4) Re-running Dijkstra (The 'Brute Force' Dynamic Approach)
    path_d2, cost_d2, time_d2 = evaluator.measure_execution(
        "Dijkstra", dijkstra_search, sim.base_graph, start_node, end_node
    )
    
    if path_d2 is None:
        print(f"WARNING: No path found after event from {start_node} to {end_node}.")
    else:
        evaluator.log_experiment(experiment_id, "Dijkstra", time_d2, cost_d2, is_dynamic_update=True)

    # 5) Running LPA* (Incremental Update)
    previous_data = lpa_memory_cache.get(route_key)
    path_l2, cost_l2, time_l2, updated_mem = evaluator.measure_execution(
        "LPA*", lpa_star_search, sim.base_graph, start_node, end_node, previous_search_data=previous_data
    )
    
    if path_l2 is None:
        print(f"WARNING: No LPA* path found after event from {start_node} to {end_node}.")
    else:
        # Update cache with new values for next time (e.g. recovery phase)
        lpa_memory_cache[route_key] = updated_mem
        evaluator.log_experiment(experiment_id, "LPA*", time_l2, cost_l2, is_dynamic_update=True)

    # 6) Measure Approx-APSP
    path_a, cost_a, time_a = evaluator.measure_execution(
        "Approx-APSP", approx_apsp_search, sim.base_graph, start_node, end_node, epsilon=0.2
    )
    
    if path_a is None:
        print(f"WARNING: No Approx-APSP path found from {start_node} to {end_node}.")
    else:
        evaluator.log_experiment(experiment_id, "Approx-APSP", time_a, cost_a, is_dynamic_update=True)
        # Calculate Stretch if we have both paths
        if path_d2 is not None and cost_d2 != float('inf'):
            stretch = evaluator.calculate_stretch(cost_a, cost_d2)

    # Print results
    if path_l2 is not None:
        print(f"Dynamic Comparison: LPA* took {time_l2:.4f}ms | Approx-APSP Stretch: {stretch:.2f}x")
    
    # Export graph to GraphML format for Gephi visualization (always export, even with partial results)
    try:
        export_graph_to_graphml(sim.base_graph, event, path_d, path_d2, path_l2, path_a, start_node, end_node, experiment_id)
    except Exception as e:
        print(f"WARNING: Failed to export GraphML for experiment {experiment_id}: {str(e)}")
        # Continue with the experiment even if export fails

def export_base_graph_to_graphml(graph, filename="base_graph.graphml"):
    """
    Export the base graph to GraphML format for Gephi visualization.
    """
    try:
        # Create output directory
        graphml_dir = 'graphml_exports'
        os.makedirs(graphml_dir, exist_ok=True)
        
        # Create a copy of the graph to annotate
        G = graph.copy()
        
        # Clean up node attributes for GraphML compatibility
        for node in G.nodes():
            # Remove or convert problematic attributes
            if 'pos' in G.nodes[node]:
                pos = G.nodes[node]['pos']
                if isinstance(pos, tuple) and len(pos) == 2:
                    try:
                        G.nodes[node]['latitude'] = float(pos[0])
                        G.nodes[node]['longitude'] = float(pos[1])
                    except (TypeError, ValueError):
                        G.nodes[node]['latitude'] = pos[0]
                        G.nodes[node]['longitude'] = pos[1]
                del G.nodes[node]['pos']
            
            # Ensure all attributes are GraphML-compatible (strings, numbers, booleans)
            for attr, value in list(G.nodes[node].items()):
                if isinstance(value, (tuple, list, dict)):
                    G.nodes[node][attr] = str(value)
                elif not isinstance(value, (str, int, float, bool)):
                    G.nodes[node][attr] = str(value)
        
        # Clean up edge attributes for GraphML compatibility
        for u, v in G.edges():
            # Ensure all attributes are GraphML-compatible
            for attr, value in list(G[u][v].items()):
                if isinstance(value, (tuple, list, dict)):
                    G[u][v][attr] = str(value)
                elif not isinstance(value, (str, int, float, bool)):
                    G[u][v][attr] = str(value)
        
        filepath = os.path.join(graphml_dir, filename)
        
        # Export to GraphML, inferring numeric attribute types
        nx.write_graphml(G, filepath, infer_numeric_types=True)
        print(f" Base graph exported to: {filepath}")
        
    except Exception as e:
        print(f"WARNING: Base graph export failed: {str(e)}")
        import traceback
        traceback.print_exc()

def export_graph_to_graphml(graph, event, path_dijkstra, path_dijkstra_new, path_lpa, path_approx, start_node, end_node, experiment_id):
    """
    Export the graph to GraphML format with path and event annotations for Gephi visualization.
    """
    try:
        # Create output directory
        graphml_dir = 'graphml_exports'
        os.makedirs(graphml_dir, exist_ok=True)
        
        # Create a copy of the graph to annotate
        G = graph.copy()
        
        # Clean up base attributes first
        for node in G.nodes():
            if 'pos' in G.nodes[node]:
                pos = G.nodes[node]['pos']
                if isinstance(pos, tuple) and len(pos) == 2:
                    try:
                        G.nodes[node]['latitude'] = float(pos[0])
                        G.nodes[node]['longitude'] = float(pos[1])
                    except (TypeError, ValueError):
                        G.nodes[node]['latitude'] = pos[0]
                        G.nodes[node]['longitude'] = pos[1]
                del G.nodes[node]['pos']

        # Collect all nodes that are part of any path
        path_nodes = set()
        if path_dijkstra:
            path_nodes.update(path_dijkstra)
        if path_dijkstra_new:
            path_nodes.update(path_dijkstra_new)
        if path_lpa:
            path_nodes.update(path_lpa)
        if path_approx:
            path_nodes.update(path_approx)
        
        # Collect affected edges
        affected_edges = set()
        if event and hasattr(event, 'affected_edges'):
            affected_edges = set(event.affected_edges)
        
        # Add node attributes (ensure GraphML compatibility)
        for node in G.nodes():
            G.nodes[node]['is_start'] = str(node == start_node)
            G.nodes[node]['is_end'] = str(node == end_node)
            G.nodes[node]['in_path'] = str(node in path_nodes)
            
            # Add path membership
            G.nodes[node]['in_dijkstra_old'] = str(path_dijkstra and node in path_dijkstra)
            G.nodes[node]['in_dijkstra_new'] = str(path_dijkstra_new and node in path_dijkstra_new)
            G.nodes[node]['in_lpa'] = str(path_lpa and node in path_lpa)
            G.nodes[node]['in_approx'] = str(path_approx and node in path_approx)
        
        # Add edge attributes (ensure GraphML compatibility)
        for u, v in G.edges():
            G[u][v]['is_affected'] = str((u, v) in affected_edges)
            event_type = event.event_type if event and (u, v) in affected_edges else 'none'
            G[u][v]['event_type'] = str(event_type)
            
            # Add path membership
            G[u][v]['in_dijkstra_old'] = str((path_dijkstra and any((path_dijkstra[i], path_dijkstra[i+1]) == (u, v) for i in range(len(path_dijkstra)-1))) if path_dijkstra else False)
            G[u][v]['in_dijkstra_new'] = str((path_dijkstra_new and any((path_dijkstra_new[i], path_dijkstra_new[i+1]) == (u, v) for i in range(len(path_dijkstra_new)-1))) if path_dijkstra_new else False)
            G[u][v]['in_lpa'] = str((path_lpa and any((path_lpa[i], path_lpa[i+1]) == (u, v) for i in range(len(path_lpa)-1))) if path_lpa else False)
            G[u][v]['in_approx'] = str((path_approx and any((path_approx[i], path_approx[i+1]) == (u, v) for i in range(len(path_approx)-1))) if path_approx else False)
        
        # Generate filename
        safe_exp_id = str(experiment_id).replace(' ', '_')
        filename = f"graph_{start_node}_to_{end_node}_{safe_exp_id}.graphml"
        filepath = os.path.join(graphml_dir, filename)
        
        # Export to GraphML, inferring numeric attribute types
        nx.write_graphml(G, filepath, infer_numeric_types=True)
        print(f" GraphML exported: {filepath}")
        
    except Exception as e:
        print(f"WARNING: GraphML export failed: {str(e)}")
        import traceback
        traceback.print_exc()

def run_stress_test(base_graph=None, num_iterations=1000, output_file="stress_test_results.csv"):
    """
    Run automated stress test with 1,000 iterations.
    """
 
    print("STARTING STRESS TEST (1,000 iterations)")


    try:
        # Initialize graph and simulator
        print("Building Karachi Bus Network")
        if base_graph is None:
            graph = build_karachi_bus_graph('karachi_bus_network_node_data.csv', 'karachi_bus_network_edge_list.csv')
        else:
            graph = base_graph.copy()  # Use a copy to avoid modifying the original
        sim = KarachiBusSim(graph)
        evaluator = MetricsEvaluator()
        print(" Graph and simulator initialized")

        # Get list of valid nodes for random selection
        all_nodes = list(graph.nodes())
        print(f" Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
        print(f"Starting stress test with {num_iterations} iterations\n")

        # Store previous LPA* search data for incremental updates
        previous_lpa_data = None
        successful_iterations = 0
        skipped_iterations = 0
        error_iterations = 0

        start_time = time.time()

        for iteration in range(1, num_iterations + 1):
            try:
                # Pick random start and end nodes
                start_node = random.choice(all_nodes)
                end_node = random.choice(all_nodes)

                # Ensure start and end are different
                while end_node == start_node:
                    end_node = random.choice(all_nodes)

                # Run baseline Dijkstra on original graph (before any event)
                dijkstra_result = dijkstra_search(graph, start_node, end_node)

                if dijkstra_result is None or len(dijkstra_result) < 2:
                    skipped_iterations += 1
                    continue

                path_d, cost_d = dijkstra_result[0], dijkstra_result[1]

                # Skip if no path exists or cost is infinite
                if path_d is None or cost_d == float('inf'):
                    skipped_iterations += 1
                    continue

                # Log baseline Dijkstra (Initial Query)
                start_time_iter = time.perf_counter()
                dijkstra_search(graph, start_node, end_node)
                end_time_iter = time.perf_counter()
                dijkstra_latency = (end_time_iter - start_time_iter) * 1000

                evaluator.log_experiment(
                    f"stress_{iteration}",
                    "Dijkstra",
                    dijkstra_latency,
                    cost_d,
                    is_dynamic_update=False
                )

                # Trigger targeted traffic event using the baseline path
                event = sim.generate_targeted_event(path_d)

                # Run all three algorithms on graph with disruption

                # 1. Dijkstra after event (Update)
                try:
                    dijkstra_result_after = dijkstra_search(graph, start_node, end_node)
                    if dijkstra_result_after is not None and len(dijkstra_result_after) >= 2:
                        path_d_after, cost_d_after = dijkstra_result_after[0], dijkstra_result_after[1]
                    else:
                        path_d_after, cost_d_after = None, float('inf')
                except Exception as e:
                    path_d_after, cost_d_after = None, float('inf')

                if path_d_after is None:
                    cost_d_after = float('inf')

                dijkstra_start = time.perf_counter()
                dijkstra_search(graph, start_node, end_node)
                dijkstra_end = time.perf_counter()
                dijkstra_update_latency = (dijkstra_end - dijkstra_start) * 1000

                evaluator.log_experiment(
                    f"stress_{iteration}",
                    "Dijkstra",
                    dijkstra_update_latency,
                    cost_d_after,
                    is_dynamic_update=True
                )

                # 2. LPA* with previous search data (incremental update)
                try:
                    lpa_start = time.perf_counter()
                    result = lpa_star_search(graph, start_node, end_node, previous_search_data=previous_lpa_data)
                    lpa_end = time.perf_counter()
                    lpa_latency = (lpa_end - lpa_start) * 1000

                    if result is not None:
                        if len(result) == 3:  # path, cost, memory
                            path_l, cost_l, memory = result
                        elif len(result) == 2:  # path, cost
                            path_l, cost_l = result
                            memory = None
                        else:
                            path_l, cost_l, memory = None, float('inf'), None
                    else:
                        path_l, cost_l, memory = None, float('inf'), None

                    # Store memory for next iteration
                    previous_lpa_data = memory

                except Exception as e:
                    path_l, cost_l, lpa_latency = None, float('inf'), 0

                if path_l is None:
                    cost_l = float('inf')

                evaluator.log_experiment(
                    f"stress_{iteration}",
                    "LPA*",
                    lpa_latency,
                    cost_l,
                    is_dynamic_update=True
                )

                # 3. Approx-APSP
                try:
                    approx_start = time.perf_counter()
                    result = approx_apsp_search(graph, start_node, end_node)
                    approx_end = time.perf_counter()
                    approx_latency = (approx_end - approx_start) * 1000

                    if result is not None:
                        if len(result) == 3:  # path, cost, memory
                            path_a, cost_a, _ = result
                        elif len(result) == 2:  # path, cost
                            path_a, cost_a = result
                        else:
                            path_a, cost_a = None, float('inf')
                    else:
                        path_a, cost_a = None, float('inf')

                except Exception as e:
                    path_a, cost_a, approx_latency = None, float('inf'), 0

                if path_a is None:
                    cost_a = float('inf')

                evaluator.log_experiment(
                    f"stress_{iteration}",
                    "Approx-APSP",
                    approx_latency,
                    cost_a,
                    is_dynamic_update=True
                )

                # Clear the event and reset graph weights
                sim.step()

                successful_iterations += 1

                # Print progress every 50 iterations
                if iteration % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = iteration / elapsed if elapsed > 0 else 0
                    eta = (num_iterations - iteration) / rate if rate > 0 else 0
                    print(f"Progress: {iteration}/{num_iterations} iterations "
                          f"({successful_iterations} successful, {skipped_iterations} skipped, {error_iterations} errors) "
                          f"[{rate:.1f} iter/sec, ETA: {eta/60:.1f} min]")

            except KeyboardInterrupt:
                print(f"\n{'!'*80}")
                print("STRESS TEST INTERRUPTED BY USER")
                print(f"{'!'*80}")
                print(f"Completed {iteration-1}/{num_iterations} iterations")
                print(f"Successful: {successful_iterations}, Skipped: {skipped_iterations}, Errors: {error_iterations}")
                break

            except Exception as e:
                error_iterations += 1
                if iteration % 100 == 0:  # Only print errors every 100 iterations to avoid spam
                    print(f"Error in iteration {iteration}: {str(e)}")
                continue

        # Save results to CSV
        try:
            evaluator.save_results(output_file)
            print(f"\n Stress test completed!")
            print(f"  Total iterations: {num_iterations}")
            print(f"  Successful iterations: {successful_iterations}")
            print(f"  Skipped iterations: {skipped_iterations}")
            print(f"  Error iterations: {error_iterations}")
            print(f"  Results saved to {output_file}")
        except Exception as e:
            print(f" Error saving results: {str(e)}")

        return evaluator.results

    except KeyboardInterrupt:
        print("STRESS TEST INTERRUPTED BY USER")
        return []

    except Exception as e:
        print(f"Error during stress test setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def analyze_results(results_file="stress_test_results.csv"):
    # Analyze stress test results and generate visualizations.
 
    print("STRESS TEST RESULTS ANALYSIS - ACADEMIC PAPER FORMAT")


    try:
        # Load results
        if not os.path.exists(results_file):
            print(f"ERROR: Results file '{results_file}' not found.")
            return

        print(f"Loading results from {results_file}")
        df = pd.read_csv(results_file)
        print(f" Loaded {len(df)} records from {results_file}\n")

        # Basic data validation
        if len(df) == 0:
            print("ERROR: Results file is empty.")
            return

        # Analysis 1: Update Latency

        print("ANALYSIS 1: UPDATE LATENCY BY ALGORITHM")


        print("Filtering update data")
        update_data = df[df['type'] == 'Update'].copy()
        update_data = update_data.dropna(subset=['algorithm', 'latency_ms'])
        update_data = update_data[update_data['latency_ms'] != float('inf')]
        update_data = update_data[update_data['latency_ms'] > 0]

        if len(update_data) == 0:
            print("WARNING: No valid update latency data found.")
        else:
            print(f" Processing {len(update_data)} update records")

            latency_by_algo = update_data.groupby('algorithm')['latency_ms'].mean().sort_values(ascending=False)

            print("\nMean Update Latency (milliseconds):")
            for algo, latency in latency_by_algo.items():
                print(f"  {algo}: {latency:.6f} ms")

            # Create bar chart
            print("Generating latency comparison chart")
            fig, ax = plt.subplots(figsize=(12, 7))

            algorithms = latency_by_algo.index.tolist()
            latencies = latency_by_algo.values

            # Check if logarithmic scale is needed
            max_latency = max(latencies)
            min_latency = min(latencies)
            ratio = max_latency / min_latency if min_latency > 0 else 1

            use_log_scale = ratio > 100

            # Create bar chart with custom colors
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            bars = ax.bar(algorithms, latencies, color=colors[:len(algorithms)],
                          width=0.6, edgecolor='black', linewidth=2, alpha=0.8)

            # Set y-axis to logarithmic if needed
            if use_log_scale:
                ax.set_yscale('log')
                ax.set_ylabel('Update Latency (ms) [Log Scale]', fontsize=13, fontweight='bold')
                print("\n Using logarithmic scale due to performance differences >100x")
            else:
                ax.set_ylabel('Update Latency (ms)', fontsize=13, fontweight='bold')

            ax.set_xlabel('Algorithm', fontsize=13, fontweight='bold')
            ax.set_title('Update Latency Comparison\n(Lower is Better - Dynamic Graph Updates)',
                        fontsize=15, fontweight='bold', pad=20)

            # Add value labels on bars
            for bar, value in zip(bars, latencies):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.4f}',
                        ha='center', va='bottom', fontsize=12, fontweight='bold')

            # Customize grid
            ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.7)
            ax.set_axisbelow(True)

            # Set y-axis limits with some padding
            if use_log_scale:
                ax.set_ylim(min_latency * 0.5, max_latency * 5)
            else:
                margin = (max_latency - min_latency) * 0.1
                ax.set_ylim(0, max_latency + margin)

            plt.tight_layout()

            # Save figure as high-resolution PNG
            output_path = "latency_comparison.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
            print(f" Latency comparison chart saved to: {output_path}")
            plt.close()
        
        # Analysis 2: Stretch Factor
        print("ANALYSIS 2: STRETCH FACTOR ANALYSIS (Approx-APSP)")


        print("Computing stretch factors")
        df_copy = df.copy()
        df_copy = df_copy.dropna(subset=['experiment_id', 'algorithm', 'path_cost'])

        print("Creating pivot table")
        results_pivot = df_copy.pivot_table(
            index='experiment_id',
            columns='algorithm',
            values='path_cost',
            aggfunc='first'
        )

        if 'Dijkstra' in results_pivot.columns and 'Approx-APSP' in results_pivot.columns:
            print("Calculating stretch factors")
            stretch_factors = []

            for idx, row in results_pivot.iterrows():
                dijkstra_cost = row['Dijkstra']
                approx_cost = row['Approx-APSP']

                if pd.isna(dijkstra_cost) or pd.isna(approx_cost):
                    continue
                if dijkstra_cost == float('inf') or approx_cost == float('inf'):
                    continue
                if dijkstra_cost <= 0:
                    continue

                stretch = approx_cost / dijkstra_cost

                if 1.0 <= stretch <= 10.0:
                    stretch_factors.append(stretch)

            if len(stretch_factors) > 0:
                print(f" Computed {len(stretch_factors)} valid stretch factors")
                stretch_array = np.array(stretch_factors)
                mean_stretch = np.mean(stretch_array)
                median_stretch = np.median(stretch_array)
                percentile_95 = np.percentile(stretch_array, 95)


                print("STRETCH FACTOR STATISTICS (Approx-APSP vs Dijkstra)")

                print(f"  Mean Stretch Factor:       {mean_stretch:.6f}")
                print(f"  Median Stretch Factor:     {median_stretch:.6f}")
                print(f"  95th Percentile Factor:    {percentile_95:.6f}")
                print(f"  Min Stretch Factor:        {np.min(stretch_array):.6f}")
                print(f"  Max Stretch Factor:        {np.max(stretch_array):.6f}")
                print(f"  Standard Deviation:        {np.std(stretch_array):.6f}")
                print(f"  Sample Size:               {len(stretch_factors)}")

            else:
                print("WARNING: No valid stretch factors found.")
        else:
            print("WARNING: Missing required algorithm columns for stretch factor analysis.")

        # Analysis 3: Path Cost Comparison

        print("ANALYSIS 3: PATH COST COMPARISON")


        print("Analyzing path costs")
        valid_data = df.copy()
        valid_data = valid_data.dropna(subset=['algorithm', 'path_cost'])
        valid_data = valid_data[valid_data['path_cost'] != float('inf')]
        valid_data = valid_data[valid_data['path_cost'] > 0]

        if len(valid_data) > 0:
            print(f" Processing {len(valid_data)} valid path cost records")
            cost_by_algo = valid_data.groupby('algorithm')['path_cost'].agg(['mean', 'median', 'min', 'max'])
            print("\nPath Cost Statistics by Algorithm:")
            print(cost_by_algo.to_string())
        else:
            print("WARNING: No valid path cost data found.")


        print(" ANALYSIS COMPLETE")


    except KeyboardInterrupt:

        print("ANALYSIS INTERRUPTED BY USER")

        print("Partial results may have been saved.")
        print("You can resume analysis later or run with smaller dataset.")
        return

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

def run_baseline_experiments(base_graph=None):
    # Run baseline experiments on 4 optimal test routes discovered through network analysis.
    # These routes use bottleneck edges where road closures have maximum impact.
 
    print("RUNNING BASELINE EXPERIMENTS")


    try:
        # 1) Setup
        print("Setting up experiment environment")
        if base_graph is None:
            G = build_karachi_bus_graph('karachi_bus_network_node_data.csv', 'karachi_bus_network_edge_list.csv')
        else:
            G = base_graph.copy()  # Use a copy to avoid modifying the original
        sim = KarachiBusSim(G)
        evaluator = MetricsEvaluator()
        print(" Environment setup complete")

        # Optimal test routes discovered through network analysis (bottleneck edges with maximum closure impact)
        test_routes = [
            ("korangi_no_1", "sector_no_7-d"),      # 51.29 km - disconnects when critical edge closes
            ("korangi_no_3", "orangi_town"),        # 88.63 km - disconnects when critical edge closes
            ("orangi_town", "karella_mour"),        # 65.05 km - disconnects when critical edge closes
            ("orangi_town", "godhra")               # 19.41 km - disconnects when critical edge closes
        ]

        total_scenarios = len(test_routes) * 2  # disruption + recovery per route
        completed_scenarios = 0

        for i, (start, end) in enumerate(test_routes):

            print(f"ROUTE {i+1}/{len(test_routes)}: {start} → {end}")


            # DISRUPTION PHASE (Testing Dijkstra's robustness to changes)
            print(f"\nSCENARIO {completed_scenarios+1}/{total_scenarios}: DISRUPTION PHASE")
            try:
                # Run comparison while road is blocked
                run_experiment_cycle(sim, evaluator, start, end, f"{i+1}_blocked")
                print(f" Disruption phase completed for route {i+1}")
                completed_scenarios += 1
            except Exception as e:
                print(f" Error in disruption phase for route {i+1}: {str(e)}")
                continue

            # RECOVERY PHASE (Testing LPA*'s strength)
            print(f"\nSCENARIO {completed_scenarios+1}/{total_scenarios}: RECOVERY PHASE")
            try:
                # Manually expire the event to test repair logic
                for e in sim.active_events:
                    e.end_time = datetime.now() - timedelta(seconds=1)

                # calling step to revert weights
                if sim.step():
                    print("Traffic cleared! Measuring algorithm recovery speed")
                    run_experiment_cycle(sim, evaluator, start, end, f"{i+1}_recovered")
                    print(f" Recovery phase completed for route {i+1}")
                else:
                    print(f"WARNING: Could not clear traffic for route {i+1}")
                completed_scenarios += 1
            except Exception as e:
                print(f" Error in recovery phase for route {i+1}: {str(e)}")
                continue

        print(f"BASELINE EXPERIMENTS COMPLETE")
        print(f"Completed {completed_scenarios}/{total_scenarios} scenarios")

        try:
            evaluator.save_results("karachi_final_results.csv")
            print(" Results saved to karachi_final_results.csv")
        except Exception as e:
            print(f" Error saving results: {str(e)}")

    except KeyboardInterrupt:

        print("BASELINE EXPERIMENTS INTERRUPTED BY USER")

        print("Partial results may have been saved.")
        print("You can resume experiments later.")
        return

    except Exception as e:
        print(f"Error during baseline experiments: {str(e)}")
        import traceback
        traceback.print_exc()

def show_menu():
    print("DYNAMIC ROUTING ALGORITHMS - INTEGRATED SYSTEM")
    print("\nChoose operation:")
    print("  1) Run baseline experiments (2 test routes)")
    print("  2) Run stress test (1,000 iterations)")
    print("  3) Run analysis on results")
    print("  4) Run all (experiments → stress test → analysis)")
    print("  0) Exit")
    print()
    
    choice = input("Enter choice (0-4): ").strip()
    return choice

def main():
    # Build the base graph and export it for visualization
    print("Building Karachi Bus Network for GraphML export")
    base_graph = build_karachi_bus_graph('karachi_bus_network_node_data.csv', 'karachi_bus_network_edge_list.csv')
    export_base_graph_to_graphml(base_graph, "karachi_bus_network_base.graphml")
    print()

    run_baseline_experiments(base_graph)
    run_stress_test(base_graph)
    analyze_results()

    """while True:
        choice = show_menu()
        if choice == '0':
            print("Exiting.")
            break
        elif choice == '1':
            run_baseline_experiments(base_graph)
        elif choice == '2':
            run_stress_test(base_graph)
        elif choice == '3':
            analyze_results()
        elif choice == '4':
            run_baseline_experiments(base_graph)
            run_stress_test(base_graph)
            analyze_results()
        else:
            print("Invalid choice. Please enter 0-4.")"""


if __name__ == "__main__":
    main()