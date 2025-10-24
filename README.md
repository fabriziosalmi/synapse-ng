# 🧬 Synapse-NG: The Autonomous Digital Organism

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

**A self-governing, self-funding, self-evolving decentralized network.**

Synapse-NG is a decentralized peer-to-peer network that functions as a living digital organism. It can think, make decisions, own resources, and evolve without central control. Each node is an autonomous agent, and together they form a collective intelligence.

*[Insert a GIF of the dashboard or a high-level architecture diagram here]*

---

## 🚀 Quick Start

Get a 3-node network running in under 5 minutes with Docker.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/fabriziosalmi/synapse-ng.git
    cd synapse-ng
    ```

2.  **Start the network:**
    ```bash
    docker-compose up --build -d
    ```

3.  **Verify the network status:**
    ```bash
    curl http://localhost:8001/state | jq '.global.nodes | length'
    ```
    You should see an output of `3`.

4.  **Run the test suite:**
    ```bash
    ./test_suite.sh
    ```

---

## 📖 Documentation

For a deeper dive into Synapse-NG, explore our comprehensive documentation:

*   **[Getting Started](docs/getting-started.md):** A detailed guide to setting up and running a node.
*   **[Architecture](docs/architecture.md):** An overview of the system's architecture.
*   **[Governance](docs/governance.md):** An explanation of the governance system.
*   **[Economy](docs/economy.md):** A guide to the economic system.
*   **[API Reference](docs/api-reference.md):** A reference for the project's API endpoints.

---

## 🤝 Contributing

Contributions are welcome! Please read our [contributing guidelines](docs/contributing.md) to get started.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.