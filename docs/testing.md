# Testing

Synapse-NG has a comprehensive test suite that covers all aspects of the system, from the core networking components to the high-level application logic. The tests are designed to be run in a Docker environment to ensure a consistent and reproducible testing process.

## Running the Test Suite

To run the complete test suite, use the following command:

```bash
./test_suite.sh
```

This will run all of the tests in the suite, including tests for the base network, governance, economy, and common tools.

## Targeted Testing

You can also run specific subsets of the test suite by passing arguments to the `test_suite.sh` script.

*   `./test_suite.sh base`: Runs the base network tests only.
*   `./test_suite.sh governance`: Runs the governance tests only.
*   `./test_suite.sh economy`: Runs the economy tests only.

For more specific testing, you can use the following scripts:

*   `./test_common_tools_experiment.sh`: Runs the common tools tests.
*   `./test_immune_system.sh`: Runs the immune system tests.

## Test Coverage

The test suite covers the following scenarios:

*   **Network Convergence:** Verifies that the CRDT state synchronizes correctly across all nodes.
*   **WebRTC Connections:** Verifies that P2P connections can be established and maintained.
*   **SynapseSub Message Propagation:** Verifies that messages are correctly propagated throughout the network.
*   **Task Lifecycle:** Verifies that tasks can be created, claimed, and completed.
*   **Reputation v2:** Verifies that the tag-based reputation system is working correctly.
*   **Weighted Voting:** Verifies that the contextual voting system is working correctly.
*   **Synapse Points Economy:** Verifies that the SP economy is working correctly.
*   **Auction System:** Verifies that the auction system is working correctly.
*   **Common Tools Execution:** Verifies that common tools can be executed by authorized nodes.
*   **Network Operations:** Verifies that governance commands can be executed correctly.
*   **Immune System:** Verifies that the immune system can detect and heal network problems.