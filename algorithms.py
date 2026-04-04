'''
Contains three separate functions or classes: run_dijkstra(), run_lpa_star(), and run_approx_apsp().

Input: Takes the graph object and (source, destination) nodes.

should only do math/logic and not care about the simulation or CSVs.
'''

import heapq

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

# --- skeleton for rest of the algos---

def approx_apsp_search(graph, start_node, end_node, epsilon=0.1):
    """
    [TO BE IMPLEMENTED]
    (1+epsilon)-Approximate logic based on the FOCS 2024 paper.
    Uses planar spanners to return a sub-optimal but faster path.
    """
    pass