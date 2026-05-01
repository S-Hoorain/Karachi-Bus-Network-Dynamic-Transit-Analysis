'''
Contains logic to add traffic or road disruptions to the graph (e.g., a function apply_traffic_jam(edge_id) that increases a weight).

allows you to create repeatable scenarios (like a morning rush hour) to test against all three algorithms.
'''

import random
import numpy as np
from datetime import datetime, timedelta

class TrafficEvent:
    def __init__(self, event_type, affected_edges, intensity, duration_mins):
        self.event_type = event_type  # 'congestion', 'accident', 'closure'
        self.affected_edges = affected_edges  # List of (u, v) tuples
        self.intensity = intensity  # Multiplier for edge weight
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=duration_mins)

class KarachiBusSim:
    def __init__(self, graph):
        self.base_graph = graph
        self.active_events = []
        # Store original weights to revert after events expire
        self.original_weights = { (u, v): d['weight'] for u, v, d in graph.edges(data=True) }

    def generate_random_event(self):
        # Generating realistic urban disruption into the network.

        event_types = ['congestion', 'accident', 'closure']
        etype = random.choice(event_types)
        
        # Picking a random hotspot (a node with high degree/centrality in a real life network)
        hotspot = random.choice(list(self.base_graph.nodes()))
        all_affected_edges = list(self.base_graph.edges(hotspot))
        
        # Limit closure events to no more than 10% of total edges to prevent unrealistic isolation
        total_edges = self.base_graph.number_of_edges()
        max_closure_edges = max(1, int(0.1 * total_edges))  # At least 1 edge
        
        if etype == 'closure':
            # Randomly select a subset of edges to close, up to 10% of total edges
            num_to_close = min(len(all_affected_edges), max_closure_edges)
            affected_edges = random.sample(all_affected_edges, num_to_close) if all_affected_edges else []
            intensity = float('inf')  # Road is impassable
            duration = random.randint(60, 180)
        else:
            # For congestion and accident, use all edges from hotspot
            affected_edges = all_affected_edges
            if etype == 'accident':
                intensity = random.uniform(3.0, 5.0)
                duration = random.randint(30, 90)
            else: # Congestion
                intensity = random.uniform(1.5, 2.5)
                duration = random.randint(20, 45)

        event = TrafficEvent(etype, affected_edges, intensity, duration)
        self.active_events.append(event)
        self._apply_event(event)
        return event

    def generate_targeted_event(self, current_path):
        """
        Generate a traffic event that hits the current path.
        This guarantees that algorithms are forced to reroute.
        
        Parameters:
        - current_path: List of nodes representing the current route
        
        Returns:
        - TrafficEvent object containing the disruption
        """
        
        if not current_path or len(current_path) < 2:
            # Fallback to random event if path is invalid
            return self.generate_random_event()
        
        # Select a random edge from the current path
        edge_idx = random.randint(0, len(current_path) - 2)
        target_edge = (current_path[edge_idx], current_path[edge_idx + 1])
        
        # Verify the edge exists in the graph
        if not self.base_graph.has_edge(target_edge[0], target_edge[1]):
            return self.generate_random_event()
        
        # Randomly choose between closure or severe congestion
        event_type = random.choice(['closure', 'congestion'])
        
        if event_type == 'closure':
            # Make the edge impassable
            affected_edges = [target_edge]
            intensity = float('inf')
            duration = random.randint(60, 180)
        else:
            # Severe congestion - high multiplier
            affected_edges = [target_edge]
            intensity = random.uniform(4.0, 6.0)
            duration = random.randint(30, 90)
        
        event = TrafficEvent(event_type, affected_edges, intensity, duration)
        self.active_events.append(event)
        self._apply_event(event)
        
        return event

    def _apply_event(self, event):
        # Updating the graph weights based on the event intensity.
        for u, v in event.affected_edges:
            if self.base_graph.has_edge(u, v):
                new_weight = self.original_weights[(u, v)] * event.intensity
                self.base_graph[u][v]['weight'] = new_weight
                self.base_graph[u][v]['event_active'] = True

    def step(self):
        # to clear expired events.
    
        current_time = datetime.now()
        expired = [e for e in self.active_events if current_time > e.end_time]
        
        for event in expired:
            for u, v in event.affected_edges:
                if self.base_graph.has_edge(u, v):
                    old_weight = self.base_graph[u][v]['weight']
                    self.base_graph[u][v]['weight'] = self.original_weights[(u, v)]
                    new_weight = self.base_graph[u][v]['weight']
                    self.base_graph[u][v]['event_active'] = False
                    print(f"Event expired: Edge ({u}, {v}) weight reverted from {old_weight:.2f} to {new_weight:.2f}")
            self.active_events.remove(event)
        
        return len(expired) > 0

    def get_current_state(self):
        # Returns a summary of disruptions
        return [
            {"type": e.event_type, "count": len(e.affected_edges), "ends": e.end_time}
            for e in self.active_events
        ]