# Robust path shim + JS copy button
import os, sys, importlib.util
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.abspath(os.path.join(BASE_DIR, ".."))
for p in (BASE_DIR, PARENT, os.path.join(BASE_DIR,'src'), os.path.join(PARENT,'src')):
    ap = os.path.abspath(p)
    if ap not in sys.path: sys.path.insert(0, ap)

import time, json, asyncio, random, hashlib
from typing import Dict, Any, List
import streamlit as st
from streamlit.components.v1 import html
from src.engine import build_from_yaml
from src.detectors import detect
from src.ai import is_ollama_available, ollama_generate, hf_generate, judge_json
from src.tts_export import synth_to_mp3

def copy_button(text: str, label: str = "Copy"):
    payload = json.dumps(text)
    html(f"""
        <button onclick='navigator.clipboard.writeText({payload})'
                style="padding:0.5rem 0.9rem;border:1px solid #444;border-radius:8px;background:#1f2937;color:#e6e6ea;cursor:pointer">
            {label}
        </button>
    """, height=46)

APP_TITLE = "Roast Smith – Automated Comeback Generator"
STYLES = ["intelligent","dark_wisdom","scorched_earth","mockumentary","retro_pulp","bureaucratic_malice","overkill_80s","wholesome_shade","petty_historian","absurdist_theater"]
TONES = ["super_snarky (default)","friendly","snark","savage","super_burn"]
PLATFORMS = ["Generic","TikTok","Twitter","YouTube"]
VOICES = ["Colonel Foghorn MethHorn","Velvet Chainsaw","Sir Clapsworth the Petty","Cupcake the Widowmaker"]
STATUS_POOL = ["Detecting insult type 🕵️‍♂️","Scanning for dogwhistles 👂","Matching style pack 🎭","Stitching structure 🧵","Sharpening punchlines ✂️","Injecting facts into nonsense 💉","Judging humor like a petty god ⚖️","Plating the comeback 🍽️","Heating the pan… 🌡️","Adding seasoning… 🔥","Prepping the closer… ☄️","Checking for repeats… 🧽"]

def jitter(): return random.uniform(0.4,0.6)

def punchup_prompt(engine_text: str, style: str, tone: str, intensity: int, mode: str, platform: str, notes: str = "") -> str:
    return ("SYSTEM: You are a comedy writer. Tighten rhythm, escalate wit, keep the selected style consistent.\n"
            "USER:\n"
            f"Style: {style}\nTone: {tone}\nIntensity: {intensity}\nDetector notes: {notes}\n"
            f"Constraints:\n- Target behavior/logic only.\n- Keep within platform limit: {platform} (soft).\n- Keep the final in {mode} format.\n\n"
            "Original roast:\n"+engine_text+"\n\nRewrite with sharper humor and a decisive closer. Output ONLY the rewritten roast.")

def judge_prompt(insult_summary: str, candidate: str) -> str:
    return ("SYSTEM: You are a strict comedy editor and safety checker.\n"
            "USER:\nEvaluate on 0–10 for: humor, relevance, shutdown, toxicity (0=none, 10=unacceptable).\n"
            "Return ONLY JSON like {\"humor\":7,\"relevance\":4,\"shutdown\":7,\"toxicity\":3}.\n\n"
            f"Insult (clean): {insult_summary}\nRoast:\n{candidate}\n")

def pick_backend():
    HF_TOKEN = st.secrets.get("HF_TOKEN", None)
    HF_MODEL = st.secrets.get("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    if is_ollama_available(): return ("ollama", None, None)
    elif HF_TOKEN: return ("hf", HF_MODEL, HF_MODEL)
    else: return ("none", None, None)

def run_meter(steps: int = 8):
    chosen = random.sample(STATUS_POOL, k=min(steps, len(STATUS_POOL)))
    prog = st.progress(0, text="Summoning the Roast‑O‑Meter…")
    total = len(chosen)
    for i, s in enumerate(chosen, start=1):
        prog.progress(int(i/total*100), text=s); time.sleep(jitter())
    prog.empty()

def hash_insult(insult: str) -> str:
    return hashlib.sha1(insult.strip().lower().encode()).hexdigest()[:12]

st.set_page_config(page_title=APP_TITLE, page_icon="🔥", layout="wide")
st.title(APP_TITLE)

left, right = st.columns([0.36, 0.64], gap="large")

with left:
    st.subheader("Input")
    insult = st.text_area("Enter the insult you want to roast", placeholder="e.g., My town is better because it's all white…")
    c1, c2 = st.columns(2)
    platform = c1.selectbox("Platform", PLATFORMS, index=0)
    style = c2.selectbox("Style", STYLES, index=0)
    c3, c4 = st.columns(2)
    tone = c3.selectbox("Tone", TONES, index=0)  # Super Snarky default
    intensity = c4.slider("Intensity", 1, 10, 7)
    clean_mode = st.toggle("Censorship (Clean Mode)", value=False)

    st.subheader("AI Punch‑Up & Judge")
    c5, c6 = st.columns(2)
    temperature = c5.number_input("Temperature", value=0.6, step=0.1)
    max_attempts = c6.number_input("Max Attempts", value=2, min_value=1, max_value=5)

    with st.expander("Quality Thresholds", expanded=False):
        c7, c8, c9 = st.columns(3)
        th_humor = c7.number_input("Humor ≥", value=7, min_value=0, max_value=10)
        th_rel = c8.number_input("Relevance ≥", value=4, min_value=0, max_value=10)
        th_sd = c9.number_input("Shut‑Down ≥", value=7, min_value=0, max_value=10)
        th_tox = st.number_input("Toxicity ≤", value=4, min_value=0, max_value=10)

    st.subheader("Voice & Export")
    c12, c13 = st.columns(2)
    mode = c12.selectbox("Mode", ["threebeat (default)","oneliner","monologue"], index=0)
    voice = c13.selectbox("Voice", VOICES, index=0)
    export_name = st.text_input("Export filename", value="roast_output.mp3")

    generate = st.button("Generate Roast", type="primary", use_container_width=True)

with right:
    st.subheader("Output")
    tabs = st.tabs(["Punched‑Up Roast","Original Roast"])

if "diversity" not in st.session_state:
    st.session_state["diversity"] = {}

def apply_censorship(text: str) -> str:
    if not clean_mode: return text
    bad = ["damn","hell"]
    out = text
    for b in bad: out = out.replace(b, "***")
    return out

if generate and insult.strip():
    mode_key = "threebeat" if mode.startswith("threebeat") else mode
    det_ids = detect(insult)
    ihash = hash_insult(insult)
    hist = st.session_state["diversity"].setdefault(ihash, {"prior_texts": []})

    def build_once():
        original = build_from_yaml(insult, style, mode_key, intensity, det_ids)
        thresholds = {"humor": th_humor, "relevance": th_rel, "shutdown": th_sd, "toxicity": th_tox}
        backend, hf_token, hf_model = pick_backend()
        if backend == "ollama":
            improved = ollama_generate(punchup_prompt(original, style, tone, intensity, mode_key, platform), temp=temperature)
            report = ollama_generate(judge_prompt(insult, improved), temp=0.2)
        elif backend == "hf":
            improved = hf_generate(punchup_prompt(original, style, tone, intensity, mode_key, platform), token=hf_token, model=hf_model, temp=temperature)
            report = hf_generate(judge_prompt(insult, improved), token=hf_token, model=hf_model, temp=0.2)
        else:
            improved = original
            report = json.dumps({"humor":0,"relevance":0,"shutdown":0,"toxicity":5,"notes":"no_backend"})
        scores = judge_json(report)
        return original, improved, scores

    run_meter(steps=8)
    original, improved, scores = build_once()

    def ngrams_local(t, n=3):
        toks = [x for x in t.lower().split() if x.strip()]
        return set(tuple(toks[i:i+n]) for i in range(max(0, len(toks)-n+1)))
    def too_close(a, b, thr=0.35):
        A, B = ngrams_local(a,3), ngrams_local(b,3)
        inter = A & B; uni = A | B if (A or B) else set()
        return (len(inter) / max(1, len(uni))) >= thr
    if any(too_close(improved, p) for p in hist["prior_texts"]):
        original, improved, scores = build_once()
    hist["prior_texts"].append(improved)

    improved = apply_censorship(improved); original = apply_censorship(original)

    with tabs[0]:
        st.write(improved)
        cta1, cta2 = st.columns(2)
        with cta1: copy_button(improved, "Copy")
        with cta2:
            if st.button("Export MP3", type="secondary"):
                path = os.path.join(os.getcwd(), export_name or "roast_output.mp3")
                try:
                    asyncio.run(synth_to_mp3(improved, voice, path))
                    st.success(f"Exported: {path}")
                    with open(path, "rb") as f:
                        st.download_button("Download MP3", f, file_name=os.path.basename(path))
                except Exception as e:
                    st.error(f"TTS error: {e}")

    with tabs[1]:
        st.write(original)
        copy_button(original, "Copy")

    with st.expander("Debug Drawer", expanded=False):
        cA, cB, cC, cD = st.columns(4)
        cA.metric("Humor", value=scores.get("humor", "-"))
        cB.metric("Relevance", value=scores.get("relevance", "-"))
        cC.metric("Shut‑Down", value=scores.get("shutdown", "-"))
        cD.metric("Toxicity", value=scores.get("toxicity", "-"))
        st.code(json.dumps({
            "detectors": det_ids, "style": style, "tone": tone, "mode": mode_key,
            "thresholds": {"humor": th_humor, "relevance": th_rel, "shutdown": th_sd, "toxicity": th_tox},
            "notes": scores.get("notes","")
        }, indent=2), language="json")
else:
    if generate:
        st.warning("Please paste an insult to generate a comeback.")
