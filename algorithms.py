'''
Contains three separate functions or classes: run_dijkstra(), run_lpa_star(), and run_approx_apsp().

Input: Takes the graph object and (source, destination) nodes.

should only do math/logic and not care about the simulation or CSVs.
'''

import heapq
import math
import random

# Global Index to persist landmark data across search calls
_apsp_index = None 

def dijkstra_search(graph, start_node, end_node):
    """
    Optimized Dijkstra using a Min-Heap.
    Baseline for the Karachi Bus Network.
    """
    # distances[node] = total weight from start to that node
    distances = {node: float('inf') for node in graph.nodes()}
    distances[start_node] = 0
    
    # predecessors[node] = previous node in the shortest path
    predecessors = {node: None for node in graph.nodes()}
    
    # Priority Queue stores distance and current_node
    P_queue = [(0, start_node)]

    while P_queue:
        current_distance, u = heapq.heappop(P_queue)

        # If we found shorter path already skip
        if current_distance > distances[u]:
            continue
            
        # end node reached
        if u == end_node:
            break

        for v in graph.neighbors(u):
            weight = graph[u][v].get('weight', float('inf'))
            new_distance = current_distance + weight

            if new_distance < distances[v]:
                distances[v] = new_distance
                predecessors[v] = u
                heapq.heappush(P_queue, (new_distance, v))

    # Reconstructing path from end to start
    path = []
    current = end_node
    while current is not None:
        path.insert(0, current)
        current = predecessors[current]

    # Returning none if no path exists
    if distances[end_node] == float('inf'):
        return None, float('inf')

    return path, distances[end_node]

def lpa_star_search(graph, start_node, end_node, previous_search_data=None):
    INF = float('inf')

    # -------------------------------------------------------------------------
    # Restore or initialise state
    # -------------------------------------------------------------------------
    if previous_search_data is not None:
        g       = previous_search_data['g_values']
        rhs     = previous_search_data['rhs_values']
        U_set   = previous_search_data['U_set']
        changed = previous_search_data.get('changed_edges', [])
    else:
        g       = {node: INF for node in graph.nodes()}
        rhs     = {node: INF for node in graph.nodes()}
        rhs[start_node] = 0
        U_set   = {start_node}
        changed = []

    # -------------------------------------------------------------------------
    # Rebuild heap from U_set
    # -------------------------------------------------------------------------
    U_heap = []
    for node in U_set:
        m = min(g[node], rhs[node])
        heapq.heappush(U_heap, ((m, m), node))

    # -------------------------------------------------------------------------
    # Handle changed edges (incremental updates)
    # -------------------------------------------------------------------------
    for (u, v) in changed:
        best = INF
        preds = graph.predecessors(v) if graph.is_directed() else graph.neighbors(v)

        for pred in preds:
            w = graph[pred][v].get('weight', INF)
            best = min(best, g[pred] + w)

        rhs[v] = best

        if g[v] != rhs[v]:
            if v not in U_set:
                U_set.add(v)
                m = min(g[v], rhs[v])
                heapq.heappush(U_heap, ((m, m), v))
        else:
            U_set.discard(v)

    # -------------------------------------------------------------------------
    # ComputeShortestPath
    # -------------------------------------------------------------------------
    while True:
        # Remove stale entries
        while U_heap and U_heap[0][1] not in U_set:
            heapq.heappop(U_heap)

        if not U_heap:
            break

        top_key, u = U_heap[0]

        m_goal = min(g[end_node], rhs[end_node])
        goal_key = (m_goal, m_goal)
        goal_consistent = (g[end_node] == rhs[end_node])

        if top_key >= goal_key and goal_consistent:
            break

        heapq.heappop(U_heap)
        U_set.discard(u)

        if g[u] > rhs[u]:
            # Overconsistent
            g[u] = rhs[u]
            succs = graph.successors(u) if graph.is_directed() else graph.neighbors(u)

            for s in succs:
                if s != start_node:
                    best = INF
                    preds = graph.predecessors(s) if graph.is_directed() else graph.neighbors(s)

                    for pred in preds:
                        w = graph[pred][s].get('weight', INF)
                        best = min(best, g[pred] + w)

                    rhs[s] = best

                if g[s] != rhs[s]:
                    if s not in U_set:
                        U_set.add(s)
                        m = min(g[s], rhs[s])
                        heapq.heappush(U_heap, ((m, m), s))
                else:
                    U_set.discard(s)

        else:
            # Underconsistent
            g[u] = INF
            succs = list(graph.successors(u) if graph.is_directed() else graph.neighbors(u))

            for s in succs + [u]:
                if s != start_node:
                    best = INF
                    preds = graph.predecessors(s) if graph.is_directed() else graph.neighbors(s)

                    for pred in preds:
                        w = graph[pred][s].get('weight', INF)
                        best = min(best, g[pred] + w)

                    rhs[s] = best

                if g[s] != rhs[s]:
                    if s not in U_set:
                        U_set.add(s)
                        m = min(g[s], rhs[s])
                        heapq.heappush(U_heap, ((m, m), s))
                else:
                    U_set.discard(s)

    # -------------------------------------------------------------------------
    # Path reconstruction
    # -------------------------------------------------------------------------
    if g[end_node] == INF:
        updated_memory = {
            'g_values': g,
            'rhs_values': rhs,
            'U_set': U_set,
            'changed_edges': []
        }
        return None, INF, updated_memory

    path = [end_node]
    current = end_node
    visited = set()

    while current != start_node:
        if current in visited:
            updated_memory = {
                'g_values': g,
                'rhs_values': rhs,
                'U_set': U_set,
                'changed_edges': []
            }
            return None, INF, updated_memory

        visited.add(current)

        preds = list(graph.predecessors(current) if graph.is_directed() else graph.neighbors(current))
        best_pred, best_cost = None, INF

        for pred in preds:
            w = graph[pred][current].get('weight', INF)
            cost = g[pred] + w
            if cost < best_cost:
                best_cost = cost
                best_pred = pred

        if best_pred is None:
            updated_memory = {
                'g_values': g,
                'rhs_values': rhs,
                'U_set': U_set,
                'changed_edges': []
            }
            return None, INF, updated_memory

        path.insert(0, best_pred)
        current = best_pred

    # -------------------------------------------------------------------------
    # Final return
    # -------------------------------------------------------------------------
    updated_memory = {
        'g_values': g,
        'rhs_values': rhs,
        'U_set': U_set,
        'changed_edges': []
    }

    return path, g[end_node], updated_memory

class ApproxAPSPIndex:
    """
    Search Engine index that stores landmark distance tables.
    Matches the (1+epsilon) theoretical approach from FOCS 2024.
    """
    def __init__(self, graph, num_landmarks=None):
        self.graph = graph
        nodes = list(graph.nodes())
        
        # Selecting Hubs based on node degree and random sampling
        if num_landmarks is None:
            num_landmarks = max(3, math.ceil(math.log2(len(nodes) + 1)) + 2)
        
        sorted_nodes = sorted(nodes, key=lambda v: graph.degree(v), reverse=True)
        self.landmarks = list(set(sorted_nodes[:num_landmarks // 2] + 
                             random.sample(nodes, num_landmarks // 2)))

        # Pre-calculating forward and reverse distances for all landmarks
        self.d_fwd = {L: self._dijkstra_core(graph, L) for L in self.landmarks}
        rev_g = graph.reverse(copy=False)
        self.d_rev = {L: self._dijkstra_core(rev_g, L) for L in self.landmarks}

    @staticmethod
    def _dijkstra_core(g, src):
        dist = {node: float('inf') for node in g.nodes()}
        dist[src] = 0
        P_queue = [(0, src)]
        while P_queue:
            d, u = heapq.heappop(P_queue)
            if d > dist[u]: continue
            for v in g.neighbors(u):
                w = g[u][v].get('weight', 1.0)
                if d + w < dist[v]:
                    dist[v] = d + w
                    heapq.heappush(P_queue, (dist[v], v))
        return dist

def approx_apsp_search(graph, start_node, end_node, epsilon=0.1):
    """
    (1+epsilon)-Approximate logic based on the FOCS 2024 paper.
    Uses landmark-based pruned search to return sub-optimal fast paths.
    """
    global _apsp_index
    
    # Initialize index if it doesn't exist or graph has changed
    if _apsp_index is None or _apsp_index.graph != graph:
        _apsp_index = ApproxAPSPIndex(graph)

    idx = _apsp_index
    if start_node == end_node: return [start_node], 0.0

    # Calculating the Landmark Upper Bound
    ub = min((idx.d_rev[L].get(start_node, float('inf')) + 
              idx.d_fwd[L].get(end_node, float('inf'))) for L in idx.landmarks)

    # Fallback to exact search if landmarks provide no connectivity
    if ub == float('inf'):
        return dijkstra_search(graph, start_node, end_node)

    # Executing the Pruned Search based on budget (1 + epsilon) * UB
    budget = (1 + epsilon) * ub
    dist = {node: float('inf') for node in graph.nodes()}
    pred = {node: None for node in graph.nodes()}
    dist[start_node] = 0
    P_queue = [(0, start_node)]

    while P_queue:
        d, u = heapq.heappop(P_queue)
        if d > dist[u]: continue
        if u == end_node: break

        for v in graph.neighbors(u):
            w = graph[u][v].get('weight', 1.0)
            new_dist = d + w
            
            # Instant Lower Bound check using pre-computed tables
            lb = 0
            for L in idx.landmarks:
                lb = max(lb, idx.d_rev[L].get(v, 0) - idx.d_rev[L].get(end_node, 0),
                             idx.d_fwd[L].get(end_node, 0) - idx.d_fwd[L].get(v, 0))
            
            # Pruning the search if current distance + lower bound exceeds budget
            if new_dist + lb > budget: continue

            if new_dist < dist[v]:
                dist[v] = new_dist
                pred[v] = u
                heapq.heappush(P_queue, (new_dist, v))

    # Path reconstruction from end to start
    if dist[end_node] == float('inf'):
        return None, float('inf')

    path, cur = [], end_node
    while cur is not None:
        path.insert(0, cur)
        cur = pred[cur]
    return path, dist[end_node]