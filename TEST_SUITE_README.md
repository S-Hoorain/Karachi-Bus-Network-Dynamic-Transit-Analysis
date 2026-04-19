# Road Closure Test Suite

This test suite helps identify and validate which test routes actually show meaningful impact from road closures.

## Problem

The original test cases may not show clear evidence of road closures affecting paths because:
1. The graph may have many alternative routes
2. Some roads might not be critical for any particular route pair
3. The test cases might use generic node pairs that don't clearly demonstrate the impact

## Solution

This suite provides a two-step process to find and validate the best test cases:

### Step 1: Discover Optimal Test Cases

Run `find_best_test_cases.py` to analyze the network and find routes where road closures have maximum impact:

```bash
python find_best_test_cases.py
```

**What it does:**
- Analyzes the Karachi bus network structure
- Identifies bottleneck edges (critical for many routes)
- Finds pairs of nodes where closing an edge forces a significant path change
- Computes edge betweenness centrality to identify critical infrastructure
- Generates a ranked list of recommended test cases

**Output:**
- Console output showing top 20 most critical edges
- `recommended_test_cases.csv` - CSV file with the top 20 test cases

**Example output:**
```
Top 20 Most Critical Edges (by betweenness centrality):
1. node_1234 → node_5678 | Centrality: 0.145323 | Weight: 2.50 km
...

TOP 10 RECOMMENDED TEST CASES
(Routes where road closure has the biggest impact)

1. Route: location_A → location_B
   Close edge: node_X → node_Y
   Cost increase: 5.32 km (15.3%)
   Path length change: 4 nodes → 8 nodes
```

### Step 2: Validate with Real Tests

Run `test_road_closure.py` to test all three algorithms on the discovered test cases:

```bash
python test_road_closure.py
```

**What it does:**
- Loads recommended test cases from `recommended_test_cases.csv`
- For each test case:
  - Finds shortest path BEFORE road closure
  - Closes the identified edge
  - Finds shortest path AFTER road closure
  - Measures path change and cost impact
  - Tests all three algorithms: Dijkstra, LPA*, Approx-APSP

**Output:**
- Detailed console output for each test case showing:
  - Original paths and costs
  - New paths and costs after closure
  - Which algorithms detected the change
  - Percentage cost increase
- `validation_results.csv` - Summary of all test results

**Example output:**
```
TEST CASE #1
================================================================================
Route: location_A → location_B
Edge to close: node_X → node_Y

PHASE 1: BEFORE CLOSURE
Dijkstra:     25.50 km |   0.0234 ms | 7 nodes
LPA*:         25.50 km |   0.0198 ms | 7 nodes
Approx-APSP:  25.50 km |   0.0412 ms | 7 nodes

PHASE 2: AFTER CLOSURE (Edge set to infinite weight)
Dijkstra:     30.82 km |   0.0287 ms | 11 nodes
LPA*:         30.82 km |   0.0156 ms | 11 nodes
Approx-APSP:  30.82 km |   0.0531 ms | 11 nodes

IMPACT ANALYSIS
✓ Dijkstra:     CHANGED (+20.9% cost)
✓ LPA*:         CHANGED (+20.9% cost)
✓ Approx-APSP:  CHANGED (+20.9% cost)
```

## Why This Matters

1. **Bottleneck Identification**: The test suite identifies which edges are truly critical
2. **Meaningful Impact**: Tests show real cost changes and path adaptations
3. **Algorithm Validation**: Confirms that algorithms properly handle network disruptions
4. **Performance Comparison**: Compare how quickly each algorithm adapts to changes

## File Cleanup

Already removed obsolete files:
- ✓ `stress_test.py` - Now integrated into `main.py`
- ✓ `analysis.py` - Now integrated into `main.py`
- ✓ `visualization.py` - Replaced by GraphML export for Gephi

## Quick Start

```bash
# Step 1: Find the best test cases (takes ~1-2 minutes)
python find_best_test_cases.py

# Step 2: Validate algorithms on these test cases (takes ~30-60 seconds)
python test_road_closure.py

# Step 3: Review results
cat validation_results.csv
```

## Integration with Main System

The discovered test cases can be manually integrated into `main.py` to replace the generic test routes with ones that show real impact.
