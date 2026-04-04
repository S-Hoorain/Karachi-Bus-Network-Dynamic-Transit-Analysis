# Karachi Bus Network Dynamic Transit Analysis

A comprehensive simulation framework for analyzing dynamic routing algorithms in urban transportation networks, specifically designed for the Karachi bus network. This project implements and compares multiple shortest path algorithms under realistic traffic conditions including congestion, accidents, and road closures.

## 🚀 Features

- **Graph Construction**: Builds directed graphs from real Karachi bus network data
- **Dynamic Event Simulation**: Models traffic disruptions (congestion, accidents, closures)
- **Algorithm Comparison**: Implements and benchmarks Dijkstra, LPA*, and Approximate APSP
- **Performance Metrics**: Measures latency, path costs, and approximation quality
- **Incremental Updates**: Demonstrates LPA*'s efficiency for dynamic environments
- **Comprehensive Logging**: Saves results to CSV for analysis

## 📊 Algorithms Implemented

### Dijkstra's Algorithm
- **Complexity**: O(E log V) with binary heap
- **Use Case**: Static shortest path computation
- **Optimization**: Early termination when target node is dequeued

### Lifelong Planning A* (LPA*)
- **Complexity**: O(S log S) for incremental updates
- **Use Case**: Dynamic environments with changing edge weights
- **Features**: Maintains search state for efficient re-planning

### Approximate All-Pairs Shortest Paths (Approx-APSP)
- **Complexity**: Landmark-based preprocessing plus pruned query search
- **Use Case**: Large-scale networks requiring fast approximate paths
- **Status**: Implemented with landmark precomputations and budgeted search

## 🏗️ Project Structure

```
karachi-bus-network-analysis/
├── algorithms.py          # Dijkstra, LPA*, and Approx-APSP implementations
├── graph_builder.py       # Graph construction from CSV data
├── simulation.py          # Traffic event simulation and management
├── metrics.py            # Performance evaluation and logging
├── main.py               # Main experiment runner
├── test_algorithms.py    # Unit tests for algorithm validation
├── karachi_bus_network_node_data.csv    # Bus stop coordinates
├── karachi_bus_network_edge_list.csv    # Bus route connections
├── karachi_final_results.csv            # Experiment results
└── README.md
```

## 🔧 Installation

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup
```bash
# Clone the repository
git clone https://github.com/S-Hoorain/Karachi-Bus-Network-Dynamic-Transit-Analysis.git
cd Karachi-Bus-Network-Dynamic-Transit-Analysis

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

# Install dependencies
pip install networkx pandas numpy
```

## 🚀 Usage

### Running the Full Simulation
```bash
python main.py
```

This will:
1. Load the Karachi bus network data
2. Run experiments on predefined routes
3. Simulate traffic events and measure algorithm performance
4. Save results to `karachi_final_results.csv`

### Running Unit Tests
```bash
python test_algorithms.py
```

### Custom Analysis
Modify `main.py` to:
- Change test routes in the `test_routes` list
- Adjust event parameters in `simulation.py`
- Add new algorithms in `algorithms.py`

## 📈 Sample Output

```
Graph Construction Complete!
Total Stops (Nodes): 572
Total Routes (Edges): 1140

SCENARIO 1: DISRUPTION PHASE
Experiment 1_blocked: quaidabad to tower
Static Dijkstra: 23.32 km in 1.0672 ms
EVENT TRIGGERED: ACCIDENT at khokrapar_no_4
Dynamic Comparison: LPA* took 0.1553ms | Approx-APSP Stretch: infx

SCENARIO 1: RECOVERY PHASE
Traffic cleared! Measuring algorithm recovery speed
Results saved to karachi_final_results.csv
```

## 🔍 Key Findings

- **Dijkstra**: Reliable baseline, O(E log V) complexity
- **LPA***: 10-100x faster for incremental updates in dynamic scenarios
- **Dynamic Events**: Realistic simulation prevents unrealistic network isolation
- **Performance**: LPA* shows significant advantages in changing environments

## 📚 References

This project implements techniques discussed in the following research:

1. **Optimal Routing in Urban Road Networks**  
   MDPI Applied Sciences, 2025  
   *Discusses efficient shortest path algorithms for urban transportation*

2. **Near-Optimal (1 + ε)-Approximate Fully-Dynamic APSP**  
   FOCS 2024  
   *Presents approximation algorithms for dynamic all-pairs shortest paths*

3. **Reinforcement Learning and Incremental Search in Transportation**  
   Frontiers, 2025  
   *Explores incremental search techniques for transportation networks*

4. **Karachi Bus Network Dataset**  
   DAR Lab Pakistan  
   Available at: https://darlab-pakistan.github.io/karachi-bus-network/  
   *Real-world bus network data used for graph construction and testing*

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Karachi Metropolitan Corporation for bus network data
- Research community for algorithm foundations
- Open-source Python ecosystem (NetworkX, Pandas, NumPy)

---

