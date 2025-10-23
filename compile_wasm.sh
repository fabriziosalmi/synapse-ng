#!/bin/bash
# compile_wasm.sh - Helper script for compiling Rust to WebAssembly
#
# This script is used by EvolutionaryEngineManager to compile generated
# Rust code into WASM binaries with proper optimization and error handling.
#
# Usage:
#   ./compile_wasm.sh <input.rs> <output.wasm>
#
# Exit Codes:
#   0 - Success
#   1 - Missing arguments
#   2 - Rust compiler not found
#   3 - Compilation failed
#   4 - WASM target not installed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -ne 2 ]; then
    echo -e "${RED}ERROR: Missing arguments${NC}"
    echo "Usage: $0 <input.rs> <output.wasm>"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"

# Check if rustc is available
if ! command -v rustc &> /dev/null; then
    echo -e "${RED}ERROR: Rust compiler (rustc) not found${NC}"
    echo "Install Rust from: https://rustup.rs/"
    exit 2
fi

echo -e "${GREEN}[WASM Compiler]${NC} Starting compilation..."
echo "  Input:  $INPUT_FILE"
echo "  Output: $OUTPUT_FILE"

# Check if wasm32-unknown-unknown target is installed
if ! rustc --print target-list | grep -q "wasm32-unknown-unknown"; then
    echo -e "${YELLOW}WARNING: wasm32-unknown-unknown target not found${NC}"
    echo "Installing target..."
    rustup target add wasm32-unknown-unknown
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to install wasm32-unknown-unknown target${NC}"
        exit 4
    fi
fi

# Get rustc version
RUSTC_VERSION=$(rustc --version)
echo "  Rustc:  $RUSTC_VERSION"

# Compile with optimizations
echo -e "${GREEN}[WASM Compiler]${NC} Compiling..."

rustc "$INPUT_FILE" \
    --target wasm32-unknown-unknown \
    --crate-type=cdylib \
    -C opt-level=3 \
    -C lto=fat \
    -C panic=abort \
    -C codegen-units=1 \
    -o "$OUTPUT_FILE" \
    2>&1

COMPILE_EXIT_CODE=$?

if [ $COMPILE_EXIT_CODE -eq 0 ]; then
    # Get file size
    WASM_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
    WASM_SIZE_KB=$((WASM_SIZE / 1024))
    
    # Calculate SHA256 hash
    if command -v sha256sum &> /dev/null; then
        WASM_HASH=$(sha256sum "$OUTPUT_FILE" | awk '{print $1}')
    elif command -v shasum &> /dev/null; then
        WASM_HASH=$(shasum -a 256 "$OUTPUT_FILE" | awk '{print $1}')
    else
        WASM_HASH="N/A (sha256sum not available)"
    fi
    
    echo -e "${GREEN}[WASM Compiler]${NC} ✓ Compilation successful"
    echo "  Size:   ${WASM_SIZE} bytes (${WASM_SIZE_KB} KB)"
    echo "  SHA256: ${WASM_HASH}"
    
    # Optional: strip debug info to reduce size
    if command -v wasm-strip &> /dev/null; then
        echo -e "${GREEN}[WASM Compiler]${NC} Stripping debug info..."
        wasm-strip "$OUTPUT_FILE"
        
        STRIPPED_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
        STRIPPED_SIZE_KB=$((STRIPPED_SIZE / 1024))
        SAVED=$((WASM_SIZE - STRIPPED_SIZE))
        SAVED_KB=$((SAVED / 1024))
        
        echo "  Stripped: ${STRIPPED_SIZE} bytes (${STRIPPED_SIZE_KB} KB)"
        echo "  Saved:    ${SAVED} bytes (${SAVED_KB} KB)"
    fi
    
    exit 0
else
    echo -e "${RED}[WASM Compiler]${NC} ✗ Compilation failed"
    echo "  Exit code: $COMPILE_EXIT_CODE"
    exit 3
fi
