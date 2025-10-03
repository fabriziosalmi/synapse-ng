# AI Setup Guide (Optional Feature)

> ⚠️ **Note**: AI capabilities are completely **optional**. Synapse-NG works fully without AI - this guide is only for users who want to enable advanced AI-powered features like autonomous agents and self-evolution.

## Overview

Synapse-NG supports optional AI-powered features:
- **AI Agent** (`/agent/prompt` API) - Natural language interface for node operations
- **Evolutionary Engine** (Phase 7) - Self-improving code generation and optimization

These features require:
1. A local LLM model (GGUF format)
2. `llama-cpp-python` library
3. Sufficient RAM (~1-2GB for small models)

## Quick Start

### 1. Install llama-cpp-python

Uncomment this line in `requirements.txt`:
```python
llama-cpp-python  # Required for AI features
```

Then rebuild:
```bash
docker-compose build
```

Or for local development:
```bash
pip install llama-cpp-python
```

**Note**: This requires build tools (gcc, cmake). On Alpine/slim images, install:
```bash
apk add gcc g++ cmake make  # Alpine
apt-get install build-essential cmake  # Debian/Ubuntu
```

### 2. Download AI Model

Create the models directory:
```bash
mkdir -p models/
```

**Recommended Model**: Qwen2.5-0.5B-Instruct (GGUF Q4_K_M)
- **Size**: ~350MB
- **RAM**: ~1GB during inference
- **Speed**: ~50-100 tokens/sec on modern CPU
- **Quality**: Good for command generation and reasoning

Download from Hugging Face:
```bash
# Using wget
wget https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  -O models/qwen3-0.6b.gguf

# Or using curl
curl -L https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  -o models/qwen3-0.6b.gguf
```

### 3. Configure Environment

Set the model path (optional, defaults to `models/qwen3-0.6b.gguf`):
```bash
# In docker-compose.yml or config.env
AI_MODEL_PATH=models/qwen3-0.6b.gguf
EVOLUTIONARY_LLM_PATH=models/qwen3-0.6b.gguf
```

### 4. Verify Setup

Check if AI is available:
```bash
curl http://localhost:8001/agent/status
```

Expected response:
```json
{
  "ai_available": true,
  "model_path": "models/qwen3-0.6b.gguf",
  "model_loaded": true
}
```

## Alternative Models

You can use any GGUF model compatible with llama.cpp:

### Small Models (~500MB, ~1GB RAM)
- **Qwen2.5-0.5B-Instruct** (recommended)
- **Phi-2** (2.7B parameters, Q4 quantization)
- **TinyLlama-1.1B**

### Medium Models (~2-4GB, ~4GB RAM)
- **Qwen2.5-1.5B-Instruct**
- **Mistral-7B** (Q4 quantization)
- **Llama-3-8B** (Q3/Q4 quantization)

### Where to Find Models

1. **Hugging Face**: https://huggingface.co/models?library=gguf
2. **TheBloke's Models**: https://huggingface.co/TheBloke (many popular models in GGUF)
3. **Qwen Official**: https://huggingface.co/Qwen

### Model Selection Criteria

- **For Testing**: Qwen2.5-0.5B-Instruct (~350MB)
- **For Production**: Qwen2.5-1.5B-Instruct (~1GB) or Mistral-7B Q4 (~4GB)
- **For Low RAM**: TinyLlama-1.1B (~700MB)
- **For High Quality**: Mistral-7B or Llama-3-8B (requires 8GB+ RAM)

## Usage Examples

### AI Agent API

Once configured, you can use natural language:

```bash
# Create a task using natural language
curl -X POST http://localhost:8001/agent/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a high-priority task to fix the UI bug with 50 SP reward",
    "channel": "global"
  }'
```

The AI will:
1. Parse your intent
2. Generate API commands
3. Execute them
4. Return results in plain language

### Autonomous Agent (Proactive Mode)

The AI can run in background and autonomously:
- Claim profitable tasks
- Participate in governance
- Optimize node strategy
- Monitor network health

Enable in environment:
```bash
AI_AUTONOMOUS_MODE=true
AI_STRATEGY=balanced  # Options: aggressive, balanced, conservative
```

## Performance Tuning

### CPU Threads
```bash
# Use more CPU cores for faster generation
AI_THREADS=4  # Default: auto-detect
```

### Context Window
```bash
# Limit context to save RAM
AI_MAX_CONTEXT=2048  # Default: 2048 tokens
```

### Temperature (Creativity)
```bash
AI_TEMPERATURE=0.7  # Default: 0.7 (0.0=deterministic, 1.0=creative)
```

## Troubleshooting

### Build Errors (llama-cpp-python)

**Problem**: `Could not find compiler set in environment variable CC: gcc`

**Solution**: Install build tools:
```bash
# Alpine (Docker)
RUN apk add --no-cache gcc g++ cmake make

# Debian/Ubuntu
RUN apt-get update && apt-get install -y build-essential cmake
```

### Out of Memory

**Problem**: Node crashes with OOM during model loading

**Solution**: Use a smaller model or increase container RAM:
```yaml
# docker-compose.yml
services:
  node-1:
    mem_limit: 2g  # Increase from default
```

### Slow Generation

**Problem**: AI responses take >10 seconds

**Solution**:
1. Use a smaller model (0.5B instead of 7B)
2. Increase CPU threads: `AI_THREADS=8`
3. Use GPU acceleration (requires cuda build of llama-cpp-python)

### Model Not Found

**Problem**: `FileNotFoundError: models/qwen3-0.6b.gguf`

**Solution**: 
1. Check file exists: `ls -lh models/`
2. Verify path in env: `echo $AI_MODEL_PATH`
3. Download model (see step 2 above)

## Disabling AI

To disable AI features:

1. **Comment out** `llama-cpp-python` in `requirements.txt`
2. **Remove** environment variables `AI_MODEL_PATH`, `EVOLUTIONARY_LLM_PATH`
3. **Rebuild** containers: `docker-compose build`

The system will automatically detect AI is unavailable and disable:
- `/agent/*` endpoints (return 503)
- Evolutionary engine (stays inactive)
- Autonomous background loops

All core P2P, governance, and task management features continue working normally.

## Security Considerations

### Model Safety
- **Use trusted sources**: Only download models from reputable sources (Hugging Face official, TheBloke)
- **Verify checksums**: Check SHA256 hashes when available
- **Scan for malware**: Models are binary files, scan before use

### API Rate Limiting
AI endpoints can be expensive. Consider rate limiting:
```python
# In production, add rate limiting to /agent/* endpoints
AGENT_RATE_LIMIT=10  # Max 10 requests per minute per node
```

### Resource Isolation
Run AI-heavy workloads in separate containers:
```yaml
# docker-compose.yml
services:
  node-ai:
    image: synapse-ng-ai  # Custom image with AI
    mem_limit: 4g
  
  node-lite:
    image: synapse-ng  # Standard image, no AI
    mem_limit: 512m
```

## Advanced: GPU Acceleration

For production deployments, use GPU acceleration:

### 1. Install CUDA-enabled llama-cpp-python
```bash
pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

### 2. Update Docker for GPU
```yaml
# docker-compose.yml
services:
  node-1:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 3. Configure llama.cpp for GPU
```python
# In ai_agent.py, add:
Llama(
    model_path=model_path,
    n_gpu_layers=32,  # Offload layers to GPU
    n_ctx=2048
)
```

**Performance Gain**: ~10-50x faster generation with GPU vs CPU.

## FAQ

**Q: Do I need AI to use Synapse-NG?**  
A: No! AI is completely optional. All core features (P2P, tasks, governance, economy) work without AI.

**Q: How much does AI slow down the node?**  
A: Minimal. AI runs on-demand only when you call `/agent/*` endpoints. Background loops are opt-in.

**Q: Can I use OpenAI/Anthropic instead of local models?**  
A: Not currently. Synapse-NG is designed for privacy and decentralization, so only local models are supported. You could fork and add API support.

**Q: What if my model is in PyTorch format (.bin/.safetensors)?**  
A: Convert to GGUF using llama.cpp's conversion tools:
```bash
python convert.py --outtype q4_k_m model.safetensors
```

**Q: Is AI required for Phase 7 (Network Singularity)?**  
A: Yes, Phase 7's self-evolution features require AI. But Phases 1-6 (95% of functionality) work without AI.

## Resources

- **llama.cpp GitHub**: https://github.com/ggerganov/llama.cpp
- **llama-cpp-python Docs**: https://llama-cpp-python.readthedocs.io/
- **GGUF Models**: https://huggingface.co/models?library=gguf
- **Qwen Models**: https://huggingface.co/Qwen
- **Model Quantization Guide**: https://github.com/ggerganov/llama.cpp/blob/master/examples/quantize/README.md

---

**Still Need Help?**  
Open an issue: https://github.com/fabriziosalmi/synapse-ng/issues
