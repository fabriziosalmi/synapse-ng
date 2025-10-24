# Getting Started

This guide provides a detailed walkthrough of how to set up and run a Synapse-NG node. You can choose between a quick and easy Docker setup or a manual setup for local development.

## Prerequisites

Before you begin, make sure you have the following software installed:

*   **Docker & Docker Compose:** For the recommended setup.
*   **Python 3.10+:** For manual setup and local development.
*   **`jq`:** A command-line JSON processor used by the test scripts.

## Docker Setup (Recommended)

The easiest way to get started with Synapse-NG is by using Docker. This method will set up a 3-node network with a single command.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/fabriziosalmi/synapse-ng.git
    cd synapse-ng
    ```

2.  **Start the network:**
    ```bash
    docker-compose up --build -d
    ```
    This command will build the Docker images and start three Synapse-NG nodes in the background.

3.  **Verify the network status:**
    ```bash
    curl http://localhost:8001/state | jq '.global.nodes | length'
    ```
    You should see an output of `3`, indicating that all three nodes are running and have formed a network.

4.  **Run the test suite:**
    ```bash
    ./test_suite.sh
    ```
    This will run the complete test suite to ensure that everything is working correctly.

## Manual Setup (Local Development)

If you want to do local development or run a node without Docker, you can follow these manual setup instructions.

1.  **Install dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```

2.  **Generate a node identity:**
    ```bash
    python3 -c "
    from app.identity import generate_identity
    import os
    os.makedirs('data/node-1', exist_ok=True)
    generate_identity('data/node-1')
    print('✅ Identity generated')
    "
    ```
    This will create a new identity for your node and store it in the `data/node-1` directory.

3.  **Start the node:**
    ```bash
    export NODE_ID="node-1"
    export HTTP_PORT=8000
    python3 app/main.py
    ```
    This will start a single Synapse-NG node on your local machine.
