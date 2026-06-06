# 🔬 LiteLLM Gateway Tester

A lightweight **Streamlit** app to smoke-test any [LiteLLM](https://github.com/BerriAI/litellm)-compatible proxy gateway.  
Enter your gateway URL and virtual key, pick models, and instantly benchmark them.

![screenshot placeholder](https://placehold.co/900x500?text=LiteLLM+Gateway+Tester)

---

## Features

| | |
|---|---|
| 🔍 **Model discovery** | Fetches all models available to your virtual key via `GET /v1/models` |
| 📥 **Basic completion** | Measures end-to-end latency + prompt / completion / total token counts |
| 🌊 **Streaming** | Measures time-to-first-token (TTFT), total stream duration, and chunk count |
| 📊 **Summary table** | Pass/fail per model+test with all metrics in one view |
| 🔒 **No secrets stored** | Nothing written to disk; credentials live only in your browser session |

---

## Quick Start

```bash
# 1. Install dependencies
pip install streamlit openai pandas

# 2. Run
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Usage

1. **Gateway URL** — base URL of your LiteLLM proxy, e.g. `https://proxy.example.com`  
   (`/v1` is appended automatically)
2. **Virtual Key** — your `sk-...` LiteLLM virtual key
3. Click **🔄 Fetch Models** to discover available models
4. Select which models to test
5. Optionally customise the test prompt
6. Click **▶ Run Tests**

---

## What gets tested

For every selected model the app runs two requests:

### Basic (non-streaming)
```
POST /v1/chat/completions
{"stream": false}
```
Reports: **latency (ms)**, **prompt tokens**, **completion tokens**, **total tokens**, **response text**

### Streaming
```
POST /v1/chat/completions
{"stream": true}
```
Reports: **TTFT (ms)**, **total time (ms)**, **chunk count**, **full assembled response**

---

## Requirements

| Package | Version |
|---|---|
| `streamlit` | ≥ 1.30.0 |
| `openai` | ≥ 2.0.0 |
| `pandas` | ≥ 2.0.0 |

---

## License

MIT
