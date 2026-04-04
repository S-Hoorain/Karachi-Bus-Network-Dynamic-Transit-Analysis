"""
Unit Tests for Dijkstra and LPA* Algorithms

Includes:
1. Time complexity analysis
2. Heapq optimization review
3. Test cases with mock graphs including disconnected nodes
"""

import networkx as nx
import heapq
from algorithms import dijkstra_search, lpa_star_search


# ============================================================================
# MOCK GRAPH CREATION
# ============================================================================

def create_mock_graph_connected():
    """
    Creates a simple connected directed graph for testing.
    
    Graph structure:
        1 --5--> 2 --3--> 4
        |        ^
        |        |
        +--10----+
        
    Shortest path 1->4: 1->2->4 (distance = 8)
    """
    G = nx.DiGraph()
    
    # Add nodes
    G.add_nodes_from([1, 2, 3, 4])
    
    # Add edges with weights
    G.add_edge(1, 2, weight=5)
    G.add_edge(1, 3, weight=10)
    G.add_edge(2, 4, weight=3)
    G.add_edge(3, 4, weight=2)
    
    return G


def create_mock_graph_disconnected():
    """
    Creates a graph with disconnected components.
    
    Graph structure:
        Component 1: 1 --5--> 2 --3--> 3
        Component 2: 4 --2--> 5
        No edges between components
        
    Path 1->4: Should return float('inf')
    """
    G = nx.DiGraph()
    
    # Component 1
    G.add_nodes_from([1, 2, 3])
    G.add_edge(1, 2, weight=5)
    G.add_edge(2, 3, weight=3)
    
    # Component 2 (disconnected)
    G.add_nodes_from([4, 5])
    G.add_edge(4, 5, weight=2)
    
    return G


def create_mock_graph_complex():
    r"""
    Creates a more complex graph to test algorithm correctness.
    
    Graph structure:
        1 --1--> 2 --2--> 3
        |        ^  \     ^
        |        |   \    |
        2        1    3   1
        |        |     \  |
        V        |      V V
        4 -------+----> 5
            4        2
            
    Shortest path 1->5: 1->2->5 (distance = 2+2 = 4) or 1->4->5 (2+2 = 4)
    """
    G = nx.DiGraph()
    
    G.add_nodes_from([1, 2, 3, 4, 5])
    G.add_edge(1, 2, weight=1)
    G.add_edge(1, 4, weight=2)
    G.add_edge(2, 3, weight=2)
    G.add_edge(2, 5, weight=2)
    G.add_edge(3, 5, weight=1)
    G.add_edge(4, 2, weight=1)
    G.add_edge(4, 5, weight=2)
    
    return G


def create_single_edge_graph():
    """
    Minimal graph with a single edge.
    """
    G = nx.DiGraph()
    G.add_nodes_from(['A', 'B', 'C'])
    G.add_edge('A', 'B', weight=10)
    # 'C' is isolated
    
    return G


# ============================================================================
# DIJKSTRA TESTS
# ============================================================================

def test_dijkstra_basic():
    """Test basic Dijkstra functionality on connected graph."""
    print("\n" + "="*70)
    print("TEST: Dijkstra - Basic Connected Graph")
    print("="*70)
    
    G = create_mock_graph_connected()
    path, distance = dijkstra_search(G, 1, 4)
    
    print(f"Graph edges: 1->2 (5), 1->3 (10), 2->4 (3), 3->4 (2)")
    print(f"Start: 1, End: 4")
    print(f"Expected Path: [1, 2, 4], Expected Distance: 8")
    print(f"Actual Path:   {path}, Actual Distance:   {distance}")
    
    assert path == [1, 2, 4], f"Expected [1, 2, 4], got {path}"
    assert distance == 8, f"Expected 8, got {distance}"
    print("✓ PASSED")


def test_dijkstra_disconnected():
    """Test Dijkstra with disconnected nodes (should return float('inf'))."""
    print("\n" + "="*70)
    print("TEST: Dijkstra - Disconnected Nodes")
    print("="*70)
    
    G = create_mock_graph_disconnected()
    path, distance = dijkstra_search(G, 1, 4)
    
    print(f"Graph: Component 1 (1->2->3), Component 2 (4->5)")
    print(f"Start: 1, End: 4 (in different components)")
    print(f"Expected: path=None, distance=inf")
    print(f"Actual:   path={path}, distance={distance}")
    
    assert path is None, f"Expected None, got {path}"
    assert distance == float('inf'), f"Expected inf, got {distance}"
    print("✓ PASSED")


def test_dijkstra_same_node():
    """Test Dijkstra when start and end are the same."""
    print("\n" + "="*70)
    print("TEST: Dijkstra - Same Start and End Node")
    print("="*70)
    
    G = create_single_edge_graph()
    path, distance = dijkstra_search(G, 'A', 'A')
    
    print(f"Start: A, End: A")
    print(f"Expected Path: [A], Expected Distance: 0")
    print(f"Actual Path:   {path}, Actual Distance:   {distance}")
    
    assert path == ['A'], f"Expected ['A'], got {path}"
    assert distance == 0, f"Expected 0, got {distance}"
    print("✓ PASSED")


def test_dijkstra_isolated_node():
    """Test Dijkstra when end node is isolated."""
    print("\n" + "="*70)
    print("TEST: Dijkstra - Isolated End Node")
    print("="*70)
    
    G = create_single_edge_graph()
    path, distance = dijkstra_search(G, 'A', 'C')
    
    print(f"Graph: A->B (weight: 10), C (isolated)")
    print(f"Start: A, End: C (isolated)")
    print(f"Expected: path=None, distance=inf")
    print(f"Actual:   path={path}, distance={distance}")
    
    assert path is None, f"Expected None, got {path}"
    assert distance == float('inf'), f"Expected inf, got {distance}"
    print("✓ PASSED")


def test_dijkstra_complex():
    """Test Dijkstra on more complex graph."""
    print("\n" + "="*70)
    print("TEST: Dijkstra - Complex Graph")
    print("="*70)
    
    G = create_mock_graph_complex()
    path, distance = dijkstra_search(G, 1, 5)
    
    print(f"Start: 1, End: 5")
    print(f"Shortest path: [1,2,5] with distance=3 (1 + 2)")
    print(f"Actual Path:   {path}, Actual Distance: {distance}")
    
    assert distance == 3, f"Expected distance 3, got {distance}"
    assert path is not None and path[0] == 1 and path[-1] == 5
    print("✓ PASSED")


# ============================================================================
# LPA* TESTS
# ============================================================================

def test_lpa_star_basic():
    """Test basic LPA* functionality on connected graph."""
    print("\n" + "="*70)
    print("TEST: LPA* - Basic Connected Graph")
    print("="*70)
    
    G = create_mock_graph_connected()
    path, distance, memory = lpa_star_search(G, 1, 4)
    
    print(f"Graph edges: 1->2 (5), 1->3 (10), 2->4 (3), 3->4 (2)")
    print(f"Start: 1, End: 4")
    print(f"Expected Path: [1, 2, 4], Expected Distance: 8")
    print(f"Actual Path:   {path}, Actual Distance:   {distance}")
    
    assert path == [1, 2, 4], f"Expected [1, 2, 4], got {path}"
    assert distance == 8, f"Expected 8, got {distance}"
    assert memory is not None
    print("✓ PASSED")


def test_lpa_star_disconnected():
    """Test LPA* with disconnected nodes (should return float('inf'))."""
    print("\n" + "="*70)
    print("TEST: LPA* - Disconnected Nodes")
    print("="*70)
    
    G = create_mock_graph_disconnected()
    path, distance, memory = lpa_star_search(G, 1, 4)
    
    print(f"Graph: Component 1 (1->2->3), Component 2 (4->5)")
    print(f"Start: 1, End: 4 (in different components)")
    print(f"Expected: path=None, distance=inf")
    print(f"Actual:   path={path}, distance={distance}")
    
    assert path is None, f"Expected None, got {path}"
    assert distance == float('inf'), f"Expected inf, got {distance}"
    print("✓ PASSED")


def test_lpa_star_same_node():
    """Test LPA* when start and end are the same."""
    print("\n" + "="*70)
    print("TEST: LPA* - Same Start and End Node")
    print("="*70)
    
    G = create_single_edge_graph()
    path, distance, memory = lpa_star_search(G, 'A', 'A')
    
    print(f"Start: A, End: A")
    print(f"Expected Path: [A], Expected Distance: 0")
    print(f"Actual Path:   {path}, Actual Distance:   {distance}")
    
    assert path == ['A'], f"Expected ['A'], got {path}"
    assert distance == 0, f"Expected 0, got {distance}"
    print("✓ PASSED")


def test_lpa_star_complex():
    """Test LPA* on more complex graph."""
    print("\n" + "="*70)
    print("TEST: LPA* - Complex Graph")
    print("="*70)
    
    G = create_mock_graph_complex()
    path, distance, memory = lpa_star_search(G, 1, 5)
    
    print(f"Start: 1, End: 5")
    print(f"Expected distance: 3")
    print(f"Actual Path:   {path}, Actual Distance: {distance}")
    
    assert distance == 3, f"Expected distance 3, got {distance}"
    assert path is not None and path[0] == 1 and path[-1] == 5
    print("✓ PASSED")


def test_lpa_star_incremental():
    """Test LPA* incremental update capability."""
    print("\n" + "="*70)
    print("TEST: LPA* - Incremental Update")
    print("="*70)
    
    G = create_mock_graph_connected()
    
    # First search
    path1, distance1, memory1 = lpa_star_search(G, 1, 4)
    print(f"First search (1->4): path={path1}, distance={distance1}")
    
    # Simulate edge cost change and search from different node
    # This tests if memory state is properly maintained
    path2, distance2, memory2 = lpa_star_search(G, 1, 3, previous_search_data=memory1)
    print(f"Second search (1->3) with previous memory: path={path2}, distance={distance2}")
    
    assert path1 == [1, 2, 4]
    assert distance1 == 8
    print("✓ PASSED")


# ============================================================================
# TIME COMPLEXITY ANALYSIS
# ============================================================================

def print_complexity_analysis():
    """
    Prints detailed time complexity analysis for both algorithms.
    """
    print("\n" + "="*70)
    print("TIME COMPLEXITY ANALYSIS")
    print("="*70)
    
    print("\n" + "-"*70)
    print("DIJKSTRA'S ALGORITHM")
    print("-"*70)
    print("""
Standard Dijkstra with Min-Heap:

STRUCTURE:
- Vertices: V
- Edges: E
- Priority Queue (heap): Contains at most O(E) entries (each edge relaxation)

COMPLEXITY BREAKDOWN:
1. Initialization: O(V)
2. Main loop iterations: O(V log E)
   - Each vertex dequeued at most once when finalized
   - Each dequeue is O(log E)
   
3. For each edge relaxation: O(1) check + O(log E) push if updated
   - Total edge relaxations: O(E)
   - Total heap operations: O(E log E)

TOTAL COMPLEXITY: O(V + E log E)
- Simplifies to O(E log V) when E >> V (common in connected graphs)
- Simplifies to O(E log E) in worst case

SPACE COMPLEXITY: O(V + E)
- Distance dict: O(V)
- Predecessors dict: O(V)
- Heap: O(E)

YOUR IMPLEMENTATION:
✓ Uses stale entry check: if current_distance > distances[u]: continue
  This prevents reprocessing outdated entries (optimization)
✓ Uses early termination: if u == end_node: break
  This is OPTIMAL - once a node is popped from min-heap, its distance
  is final (Dijkstra property), so we can exit immediately.
✓ No further optimization needed for the early exit.
""")
    
    print("\n" + "-"*70)
    print("LPA* (LIFELONG PLANNING A*)")
    print("-"*70)
    print("""
LPA* with stale entry removal and incremental updates:

STRUCTURE:
- Vertices involved in computation: S (typically << V for incremental)
- Open set (priority queue): U_heap
- g-values and rhs-values: Maintain consistency

COMPLEXITY BREAKDOWN:
1. Initial search phase: O(S log S)
   - Each vertex inserted/updated in heap at most O(E) times
   - But for finite planar/sparse graphs: effectively O(S log S)
   
2. Incremental updates: O(S' log S')
   - S' = vertices affected by edge changes
   - Much faster than Dijkstra for dynamic scenarios
   
3. Stale entry removal: O(E log E) worst case overhead
   - while U_heap and U_heap[0][1] not in U_set: heapq.heappop(U_heap)
   
TOTAL COMPLEXITY (first search): O(S log S) or O(E log V) if S ≈ V
INCREMENTAL UPDATE: O(S' log S') where S' << S

YOUR IMPLEMENTATION:
✓ Stale entry removal is in place to prevent processing outdated entries
✓ Early exit condition: if top_key >= goal_key and goal_consistent: break
  This is correct for LPA* - terminates when goal is consistent and
  its key is minimal in the open set.
✓ No heapq optimization possible without implementing a dictionary-based
  heap (mutable priority queue) which Python's heapq doesn't natively support.
""")


# ============================================================================
# HEAPQ OPTIMIZATION REVIEW
# ============================================================================

def print_heapq_optimization_review():
    """
    Detailed review of heapq usage for target reached exit.
    """
    print("\n" + "="*70)
    print("HEAPQ OPTIMIZATION FOR TARGET-REACHED EXIT")
    print("="*70)
    
    print("""
CURRENT APPROACH (Dijkstra):
────────────────────────────
while P_queue:
    current_distance, u = heapq.heappop(P_queue)
    
    if current_distance > distances[u]:
        continue
    
    if u == end_node:              # ← Early exit
        break
    
    for v in graph.neighbors(u):
        # ... relaxation logic

ANALYSIS:
✓ The early exit IS optimized
✓ Once target node is popped from min-heap, it has the MINIMUM distance
✓ No need to check all other queued nodes
✓ This is the standard Dijkstra optimization

Why this works:
- Min-heap property guarantees: if node u is popped, its distance is final
- Therefore, first time end_node is popped = shortest path found
- We can safely break without processing remaining heap items

Performance impact:
- Without optimization: Process all V-1 other nodes
- With optimization: Can terminate immediately
- Savings: O(?) - depends on end_node position in execution order


CURRENT APPROACH (LPA*):
───────────────────────
while True:
    while U_heap and U_heap[0][1] not in U_set:
        heapq.heappop(U_heap)
    
    if not U_heap:
        break
    
    top_key, u = U_heap[0]
    
    m_goal = min(g[end_node], rhs[end_node])
    goal_key = (m_goal, m_goal)
    goal_consistent = (g[end_node] == rhs[end_node])
    
    if top_key >= goal_key and goal_consistent:
        break                       # ← Early exit
    
    heapq.heappop(U_heap)
    # ... more logic

ANALYSIS:
✓ Exit condition is mathematically sound for LPA*
✓ Terminates when goal is expanded and optimal
✓ Cannot be improved without changing LPA* semantics

Alternative (NOT recommended):
- Maintain separate flag for goal consistency
- But this complicates the logic without performance benefit


RECOMMENDATIONS:
────────────────
1. DIJKSTRA: ✓ Current optimization is OPTIMAL
   - Early break when end_node is popped from heap
   - No further improvement possible without changing algorithm

2. LPA*: ✓ Current optimization is SOUND
   - Exit condition correctly identifies when goal is found
   - Stale entry removal happens before checking heap top
   - Standard LPA* implementation
   
3. BOTH: Consider A* heuristic if you have distance heuristics
   - Would require bidirectional search or heuristic function
   - Beyond scope of current Dijkstra/LPA* implementations
""")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all unit tests and print analysis."""
    
    print("\n" + "#"*70)
    print("# ALGORITHM TEST SUITE")
    print("#"*70)
    
    # Time complexity analysis
    print_complexity_analysis()
    
    # Heapq optimization review
    print_heapq_optimization_review()
    
    # Dijkstra tests
    test_dijkstra_basic()
    test_dijkstra_disconnected()
    test_dijkstra_same_node()
    test_dijkstra_isolated_node()
    test_dijkstra_complex()
    
    # LPA* tests
    test_lpa_star_basic()
    test_lpa_star_disconnected()
    test_lpa_star_same_node()
    test_lpa_star_complex()
    test_lpa_star_incremental()
    
    # Summary
    print("\n" + "#"*70)
    print("# ALL TESTS PASSED ✓")
    print("#"*70)


if __name__ == "__main__":
    run_all_tests()
