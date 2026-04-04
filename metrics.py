import time
import pandas as pd
import numpy as np

# Evaluates the perfomance of the different algorithms we are omparing in terms of latency and stretch factor.

class MetricsEvaluator:
    def __init__(self):
        self.results = []

    def measure_execution(self, algo_name, func, *args, **kwargs):
        # Measures Latency/Time and Result of algorithm.
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        latency = (end_time - start_time) * 1000 # Convert to milliseconds
        
        # Handle None return (unimplemented functions)
        if result is None:
            return None, None, latency
        
        # Handle different return signatures
        if len(result) == 2:  # Dijkstra: path, cost
            path, cost = result
            return path, cost, latency
        elif len(result) == 3:  # LPA*: path, cost, memory
            path, cost, memory = result
            return path, cost, latency, memory
        else:
            raise ValueError(f"Unexpected return signature for {algo_name}")

    def log_experiment(self, experiment_id, algo_name, latency, cost, is_dynamic_update=False):
        self.results.append({
            "experiment_id": experiment_id,
            "algorithm": algo_name,
            "type": "Update" if is_dynamic_update else "Initial Query",
            "latency_ms": latency,
            "path_cost": cost
        })

    def calculate_stretch(self, approx_cost, exact_cost):
        # Calculates the (1+epsilon) stretch factor.
        return approx_cost / exact_cost if exact_cost > 0 else 1

    def save_results(self, filename="experiment_results.csv"):
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        
        # Print Summary Statistics for your report
        summary = df.groupby(['algorithm', 'type'])['latency_ms'].mean()
        print("\nAverage Latency (ms):")
        print(summary)

evaluator = MetricsEvaluator()


## need to add in main
# 1. Measure Dijkstra (Exact Baseline)
# path_d, cost_d, time_d = evaluator.measure_execution("Dijkstra", dijkstra_func, G, start, end)
# evaluator.log_experiment(1, "Dijkstra", time_d, cost_d)

# 2. Measure Your (1+e) Approx
# path_a, cost_a, time_a = evaluator.measure_execution("Approx-APSP", approx_func, G, start, end)
# evaluator.log_experiment(1, "Approx-APSP", time_a, cost_a)

# 3. Calculate Stretch for Report
# stretch = evaluator.calculate_stretch(cost_a, cost_d)
# print(f"Current Stretch Factor: {stretch:.2f}x")