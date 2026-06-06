# 🔬 LiteLLM Gateway Tester

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=eshlon/litellm-gateway-tester)

A lightweight **Streamlit** app to smoke-test any [LiteLLM](https://github.com/BerriAI/litellm)-compatible proxy gateway.  
Enter your gateway URL and virtual key, pick models, and instantly benchmark them — no code changes needed.

---

## ✨ Features

| | |
|---|---|
| 🔍 **Model discovery** | Auto-fetches all models available to your virtual key via `GET /v1/models` |
| 📥 **Basic completion** | End-to-end latency + prompt / completion / total token counts |
| 🌊 **Streaming** | Time-to-first-token (TTFT), total stream duration, chunk count |
| 📊 **Summary table** | Pass / fail per model + test with all metrics in one view |
| 🔒 **Nothing stored** | Credentials live only in your browser session; nothing written to disk |

---

## 🚀 Run locally

```bash
pip install streamlit openai pandas
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501).

---

## ☁️ Deploy to Streamlit Community Cloud

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your fork, branch `main`, file `app.py`
4. Click **Deploy**

> **Note:** Your gateway URL and virtual key are entered at runtime in the sidebar — they are never stored or logged anywhere.

---

## 🛠️ Usage

1. **Gateway URL** — base URL of your LiteLLM proxy, e.g. `https://proxy.example.com`  
   (`/v1` is appended automatically if not present)
2. **Virtual Key** — your `sk-...` LiteLLM virtual key (masked input)
3. Click **🔄 Fetch Models** to discover available models
4. Select which models to test
5. Edit the test prompt if needed
6. Click **▶ Run Tests**

---

## 📐 What gets tested

For every selected model the app runs **two requests**:

### 📥 Basic (non-streaming)
```
POST /v1/chat/completions   {"stream": false}
```
→ **Latency (ms)** · **Prompt tokens** · **Completion tokens** · **Total tokens** · **Response text**

### 🌊 Streaming
```
POST /v1/chat/completions   {"stream": true}
```
→ **TTFT (ms)** · **Total time (ms)** · **Chunk count** · **Full assembled response**

---

## 📦 Requirements

```
streamlit>=1.30.0
openai>=2.0.0
pandas>=2.0.0
```

---

## 🤝 Compatible with

Any gateway that speaks the OpenAI API format, including:
- [LiteLLM Proxy](https://docs.litellm.ai/docs/proxy/quick_start)
- [OpenRouter](https://openrouter.ai)
- [Helicone](https://helicone.ai)
- Self-hosted LiteLLM on Kubernetes / Docker

---

## License

MIT
