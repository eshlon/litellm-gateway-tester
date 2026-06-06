"""
LiteLLM Gateway Tester  –  Streamlit App
=========================================

Requirements (install once):
    pip install streamlit>=1.30.0 openai>=2.0.0 pandas>=2.0.0

Run:
    streamlit run app.py

What it does:
- Connects to any LiteLLM-compatible gateway (self-hosted or cloud)
- Uses GET /v1/models to discover all models available to your virtual key
- Tests each selected model with:
    • Basic (non-streaming) chat completion  →  latency + token usage
    • Streaming chat completion              →  TTFT + total time + chunk count
- All results shown live in the UI; nothing is written to disk
"""

import time
from typing import Optional

import pandas as pd
import streamlit as st
from openai import OpenAI

# ─── defaults (overridable in the sidebar) ────────────────────────────────────
DEFAULT_PROMPT = "In exactly one sentence, what is the capital of France and why is it famous?"
MAX_TOKENS = 200
# ──────────────────────────────────────────────────────────────────────────────


# ─── helpers ──────────────────────────────────────────────────────────────────

def make_client(gateway_url: str, key: str) -> OpenAI:
    base = gateway_url.rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1"
    return OpenAI(api_key=key, base_url=base)


def fetch_models(gateway_url: str, key: str) -> tuple[list[str], Optional[str]]:
    """Return (model_ids, error_message). model_ids is [] on error."""
    try:
        client = make_client(gateway_url, key)
        resp = client.models.list()
        ids = sorted([m.id for m in resp.data])
        return ids, None
    except Exception as exc:
        return [], str(exc)


def test_basic(client: OpenAI, model: str, prompt: str) -> dict:
    result = {
        "model": model, "test": "basic",
        "ok": False, "latency_ms": None,
        "tokens": None, "response": None, "error": None,
    }
    try:
        t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS,
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        content = resp.choices[0].message.content or ""
        usage = resp.usage
        result.update({
            "ok": True,
            "latency_ms": elapsed_ms,
            "tokens": {
                "prompt":     usage.prompt_tokens     if usage else "?",
                "completion": usage.completion_tokens if usage else "?",
                "total":      usage.total_tokens      if usage else "?",
            },
            "response": content.strip(),
        })
    except Exception as exc:
        result["error"] = str(exc)
    return result


def test_streaming(client: OpenAI, model: str, prompt: str) -> dict:
    result = {
        "model": model, "test": "streaming",
        "ok": False, "ttft_ms": None, "total_ms": None,
        "chunks": 0, "response": None, "error": None,
    }
    try:
        t0 = time.perf_counter()
        first_ts = None
        parts: list[str] = []

        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_TOKENS,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                if first_ts is None:
                    first_ts = time.perf_counter()
                parts.append(delta)
                result["chunks"] += 1

        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        result.update({
            "ok":       True,
            "ttft_ms":  round((first_ts - t0) * 1000) if first_ts else None,
            "total_ms": elapsed_ms,
            "response": "".join(parts).strip(),
        })
    except Exception as exc:
        result["error"] = str(exc)
    return result


# ─── UI ───────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="LiteLLM Gateway Tester",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 LiteLLM Gateway Tester")
st.caption(
    "Benchmark any LiteLLM-compatible proxy — latency · streaming TTFT · token usage  "
    "· [GitHub](https://github.com/eshlon/litellm-gateway-tester)"
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    gateway_url = st.text_input(
        "Gateway URL",
        placeholder="https://your-litellm-gateway.example.com",
        help="Base URL of your LiteLLM proxy (e.g. https://proxy.example.com). `/v1` is appended automatically.",
        key="inp_gateway_url",
    )

    virtual_key = st.text_input(
        "Virtual Key",
        type="password",
        placeholder="sk-...",
        help="Your LiteLLM virtual key — never stored or logged",
        key="inp_virtual_key",
    )

    st.divider()

    col1, col2 = st.columns(2)
    ready = bool(gateway_url and virtual_key)
    fetch_btn = col1.button("🔄 Fetch Models", use_container_width=True, disabled=not ready)
    clear_btn = col2.button("🗑️ Clear",         use_container_width=True)

    if clear_btn:
        for k in ["models", "selected_models", "results",
                  "inp_gateway_url", "inp_virtual_key"]:
            st.session_state.pop(k, None)
        st.rerun()

    # Fetch models
    if fetch_btn and ready:
        with st.spinner("Fetching models…"):
            ids, err = fetch_models(gateway_url, virtual_key)
        if err:
            st.error(f"Failed to fetch models:\n```\n{err}\n```")
            st.session_state.pop("models", None)
        else:
            st.session_state["models"] = ids
            st.success(f"✅ Found **{len(ids)}** model(s)")

    # Model selector (shown once models are loaded)
    if "models" in st.session_state and st.session_state["models"]:
        st.divider()
        st.subheader("Select Models to Test")
        all_models = st.session_state["models"]

        col_a, col_b = st.columns(2)
        if col_a.button("All",  use_container_width=True):
            st.session_state["selected_models"] = list(all_models)
        if col_b.button("None", use_container_width=True):
            st.session_state["selected_models"] = []

        selected = st.multiselect(
            "Models",
            options=all_models,
            default=st.session_state.get("selected_models", all_models[:3]),
            label_visibility="collapsed",
        )
        st.session_state["selected_models"] = selected
    elif "models" not in st.session_state:
        st.info("Enter your gateway URL + key and click **Fetch Models**.")

    st.divider()
    st.subheader("Test Prompt")
    prompt = st.text_area(
        "Prompt",
        value=DEFAULT_PROMPT,
        height=90,
        label_visibility="collapsed",
    )

    run_btn = st.button(
        "▶ Run Tests",
        type="primary",
        use_container_width=True,
        disabled=not (ready and st.session_state.get("selected_models")),
    )

    st.divider()
    st.caption(
        "🔒 **Privacy:** Your gateway URL and virtual key are held only in "
        "your browser's session memory. They are never written to disk, "
        "never logged, and only sent to your own gateway. "
        "Closing the tab erases them instantly."
    )

# ── Main area ─────────────────────────────────────────────────────────────────

def build_summary_df(results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        row = {
            "Model":  r["model"],
            "Test":   r["test"].upper(),
            "Status": "✅ PASS" if r["ok"] else "❌ FAIL",
        }
        if r["test"] == "basic" and r["ok"]:
            row["Latency (ms)"] = r["latency_ms"]
            row["Tokens"]       = r["tokens"]["total"] if r["tokens"] else "-"
            row["TTFT (ms)"]    = "-"
            row["Chunks"]       = "-"
        elif r["test"] == "streaming" and r["ok"]:
            row["Latency (ms)"] = r["total_ms"]
            row["Tokens"]       = "-"
            row["TTFT (ms)"]    = r["ttft_ms"]
            row["Chunks"]       = r["chunks"]
        else:
            row["Latency (ms)"] = "-"
            row["Tokens"]       = "-"
            row["TTFT (ms)"]    = "-"
            row["Chunks"]       = "-"
            row["Error"]        = r.get("error", "")
        rows.append(row)
    return pd.DataFrame(rows)


def show_summary(results: list[dict]) -> None:
    df = build_summary_df(results)
    passed = sum(1 for r in results if r["ok"])
    failed = len(results) - passed

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tests", len(results))
    m2.metric("✅ Passed",   passed)
    m3.metric("❌ Failed",   failed)
    m4.metric("Pass Rate",   f"{100 * passed // len(results)}%" if results else "0%")
    st.dataframe(df, use_container_width=True, hide_index=True)


if run_btn:
    selected_models = st.session_state.get("selected_models", [])
    if not selected_models:
        st.warning("No models selected.")
        st.stop()

    client = make_client(gateway_url, virtual_key)
    all_results: list[dict] = []
    st.session_state["results"] = []

    st.subheader("🧪 Live Test Results")

    for model in selected_models:
        st.markdown(f"### 🤖 `{model}`")
        col_basic, col_stream = st.columns(2)

        with col_basic:
            with st.status("⏳ Basic completion…", expanded=False) as status:
                r = test_basic(client, model, prompt)
                all_results.append(r)
                st.session_state["results"].append(r)
                if r["ok"]:
                    status.update(label="✅ Basic  PASS", state="complete")
                    st.metric("Latency", f"{r['latency_ms']} ms")
                    if r["tokens"]:
                        t = r["tokens"]
                        st.metric("Total Tokens", t["total"],
                                  delta=f"↑{t['prompt']}  ↓{t['completion']}")
                    st.caption("**Reply:**")
                    st.info(r["response"] or "*(empty)*")
                else:
                    status.update(label="❌ Basic  FAIL", state="error")
                    st.error(r["error"])

        with col_stream:
            with st.status("⏳ Streaming…", expanded=False) as status:
                r = test_streaming(client, model, prompt)
                all_results.append(r)
                st.session_state["results"].append(r)
                if r["ok"]:
                    status.update(label="✅ Streaming  PASS", state="complete")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("TTFT",   f"{r['ttft_ms']} ms")
                    c2.metric("Total",  f"{r['total_ms']} ms")
                    c3.metric("Chunks", r["chunks"])
                    st.caption("**Reply:**")
                    st.info(r["response"] or "*(empty)*")
                else:
                    status.update(label="❌ Streaming  FAIL", state="error")
                    st.error(r["error"])

        st.divider()

    st.subheader("📊 Summary")
    show_summary(all_results)

elif "results" in st.session_state and st.session_state["results"]:
    st.subheader("📊 Previous Run Summary")
    show_summary(st.session_state["results"])
    st.info("Results from a previous run. Press **▶ Run Tests** to run again.")

else:
    st.markdown("""
    ### How to use

    1. **Enter your gateway URL** — the base URL of your LiteLLM proxy
    2. **Enter your virtual key** — format `sk-...`
    3. Click **🔄 Fetch Models** to load all models available to your key
    4. **Select the models** you want to test (defaults to first 3)
    5. Optionally edit the **test prompt**
    6. Click **▶ Run Tests** to benchmark every selected model with:
       - 📥 **Basic completion** → full latency, prompt/completion/total token counts
       - 🌊 **Streaming** → time-to-first-token (TTFT), total stream time, chunk count

    ---

    | Endpoint used | Description |
    |---|---|
    | `GET /v1/models` | Discovers all models your key can access |
    | `POST /v1/chat/completions` | Runs basic and streaming chat completion |
    """)
