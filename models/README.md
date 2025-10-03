# AI Models Directory

This directory is for **optional** AI model files (GGUF format) used by Synapse-NG's AI features.

## ⚠️ AI is Optional

**Synapse-NG works fully without AI**. This directory and AI features are completely optional. All core functionality (P2P networking, task management, governance, economy) operates without any AI dependencies.

## What Goes Here?

If you want to enable AI features, place your GGUF model files here:

```
models/
  └── qwen3-0.6b.gguf  # Example: Qwen3 0.6B model (~350MB)
```

## Quick Setup

**If you want AI features enabled:**

1. Download a model (see [AI Setup Guide](../docs/AI_SETUP.md))
2. Place it in this directory
3. Update `requirements.txt` (uncomment `llama-cpp-python`)
4. Rebuild: `docker-compose build`

**Recommended starter model:**
```bash
wget https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  -O models/qwen3-0.6b.gguf
```

## Why is this directory empty?

AI model files are:
- **Large** (hundreds of MB to several GB)
- **Binary files** (not suitable for git)
- **Optional** (not everyone needs AI)

Instead of bundling models, we provide instructions for users to download them separately if desired.

## What Happens Without Models?

If this directory is empty:
- ✅ Core P2P networking works
- ✅ Task management works
- ✅ Governance and voting work
- ✅ Economy and reputation work
- ❌ `/agent/*` endpoints return HTTP 503
- ❌ Phase 7 self-evolution is disabled

**Bottom line**: 95% of Synapse-NG functionality is available without AI.

## More Information

See the complete guide: **[docs/AI_SETUP.md](../docs/AI_SETUP.md)**

## License Note

Models you download may have their own licenses (MIT, Apache 2.0, etc.). Check the model's Hugging Face page for licensing details.

Popular open models:
- **Qwen**: Apache 2.0
- **Llama**: Llama Community License
- **Mistral**: Apache 2.0
- **Phi**: MIT

---

**Questions?** See [AI Setup Guide](../docs/AI_SETUP.md) or open an issue.
