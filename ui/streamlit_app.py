"""Streamlit UI for Market Incident Analyst — MIRA Premium Fintech Design.

Modes:
- API mode: calls FastAPI backend (default when backend is running)
- Direct mode: calls the orchestrator directly (simpler for local dev)
"""

import html as html_module
import json
import os
from datetime import datetime

import httpx
import streamlit as st

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MIRA · Market Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.environ.get("API_URL", "http://localhost:8000")

# ── Theme variables ───────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

_DARK = dict(
    bg="#040810", bg2="#07101C", bg3="#0B1828", bg4="#101F30",
    accent="#00FFB3", accent2="#06B6D4",
    amber="#F59E0B", red="#F43F5E", green="#10B981",
    dim="rgba(0,255,179,0.07)",
    border="rgba(0,255,179,0.07)", border2="rgba(0,255,179,0.22)",
    text="#E8EDF5", sub="#8FA3B8", muted="#4D6B80", faint="#1E3048",
    glow="0 0 24px rgba(0,255,179,0.15)", glow2="0 0 48px rgba(0,255,179,0.28)",
    bg_radial1="rgba(0,255,179,0.045)", bg_radial2="rgba(6,182,212,0.022)",
    bg_grid="rgba(0%2C255%2C179%2C0.02)",
    ticker_bg="#07101C",
    summary_border="rgba(6,182,212,0.14)",
    sidebar_bg="#07101C",
    input_panel_bg="#07101C",
)

_LIGHT = dict(
    bg="#F5F2EC", bg2="#EDE9DF", bg3="#E4DFD3", bg4="#D9D3C5",
    accent="#008C62", accent2="#0277A8",
    amber="#C47D0A", red="#D6304E", green="#0A7A56",
    dim="rgba(0,140,98,0.07)",
    border="rgba(0,140,98,0.1)", border2="rgba(0,140,98,0.32)",
    text="#1A2530", sub="#3D5266", muted="#6B8294", faint="#B0C0CC",
    glow="0 0 24px rgba(0,140,98,0.18)", glow2="0 0 48px rgba(0,140,98,0.32)",
    bg_radial1="rgba(0,140,98,0.04)", bg_radial2="rgba(2,119,168,0.025)",
    bg_grid="rgba(0%2C140%2C98%2C0.035)",
    ticker_bg="#EDE9DF",
    summary_border="rgba(2,119,168,0.18)",
    sidebar_bg="#EDE9DF",
    input_panel_bg="#EDE9DF",
)


def _theme_vars() -> dict:
    return _DARK if st.session_state["theme"] == "dark" else _LIGHT


# ── Global CSS ────────────────────────────────────────────────────────────────
def _build_css(t: dict) -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Outfit:wght@300;400;500;600&family=Syne:wght@600;700;800&display=swap');

/* ── Variables ──────────────────────────────────────────────── */
:root {{
  --bg:       {t['bg']};
  --bg2:      {t['bg2']};
  --bg3:      {t['bg3']};
  --bg4:      {t['bg4']};
  --accent:   {t['accent']};
  --accent2:  {t['accent2']};
  --amber:    {t['amber']};
  --red:      {t['red']};
  --green:    {t['green']};
  --dim:      {t['dim']};
  --border:   {t['border']};
  --border2:  {t['border2']};
  --text:     {t['text']};
  --sub:      {t['sub']};
  --muted:    {t['muted']};
  --faint:    {t['faint']};
  --glow:     {t['glow']};
  --glow2:    {t['glow2']};
  --ff-d:     'Bebas Neue', sans-serif;
  --ff-m:     'JetBrains Mono', monospace;
  --ff-b:     'Outfit', sans-serif;
  --ff-h:     'Syne', sans-serif;
}}

/* ── Hide native Streamlit theme picker from toolbar menu ────── */
[data-testid="main-menu-list"] li:has([data-testid="main-menu-theme"]),
[data-testid="main-menu-list"] ul:first-child {{
  display: none !important;
}}
/* Hide the entire theme section (System/Light/Dark radio group) */
div[data-baseweb="radio-group"],
[class*="themeSelector"],
[data-testid="stThemeSelect"],
[aria-label="Theme"] {{
  display: none !important;
}}
/* Target the menu items by position — theme block is first section */
[data-testid="main-menu-list"] > ul:first-of-type {{
  display: none !important;
}}

/* ── Streamlit header / toolbar ─────────────────────────────── */
[data-testid="stHeader"] {{
  background: var(--bg2) !important;
  border-bottom: 1px solid var(--border) !important;
  backdrop-filter: blur(8px) !important;
}}
[data-testid="stHeader"]::after {{
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0.15;
  pointer-events: none;
}}
/* Deploy button + toolbar icons */
[data-testid="stToolbar"] {{
  right: 1rem !important;
}}
button[data-testid="baseButton-header"],
[data-testid="stToolbarActionButtonIcon"] {{
  color: var(--muted) !important;
  border-color: var(--border) !important;
}}
button[data-testid="baseButton-header"]:hover {{
  color: var(--accent) !important;
  background: var(--dim) !important;
}}
/* Top-right "Deploy" label */
[data-testid="stDeployButton"] {{
  font-family: var(--ff-m) !important;
  font-size: 0.68rem !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;
  background: transparent !important;
  border-radius: 4px !important;
  padding: 0.3rem 0.85rem !important;
  transition: color 0.2s, border-color 0.2s, box-shadow 0.2s !important;
}}
[data-testid="stDeployButton"]:hover {{
  color: var(--accent) !important;
  border-color: var(--border2) !important;
  box-shadow: var(--glow) !important;
}}

/* ── Reset ──────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [class*="css"] {{
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: var(--ff-b) !important;
}}
.stApp {{
  background: var(--bg) !important;
  background-image:
    radial-gradient(ellipse 110% 45% at 50% -8%, {t['bg_radial1']} 0%, transparent 65%),
    radial-gradient(ellipse 55% 35% at 85% 15%, {t['bg_radial2']} 0%, transparent 55%),
    url("data:image/svg+xml,%3Csvg width='80' height='80' xmlns='http://www.w3.org/2000/svg'%3E%3Cdefs%3E%3Cpattern id='g' width='80' height='80' patternUnits='userSpaceOnUse'%3E%3Cpath d='M80 0L0 0 0 80' fill='none' stroke='{t['bg_grid']}' stroke-width='1'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23g)'/%3E%3C/svg%3E") !important;
  min-height: 100vh;
}}

/* ── Layout ─────────────────────────────────────────────────── */
.main .block-container {{
  padding: 0 3.5rem 5rem !important;
  max-width: 1440px !important;
}}

/* ── Sidebar ────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
  background: var(--bg2) !important;
  border-right: 1px solid var(--border) !important;
}}
[data-testid="stSidebar"] > div:first-child {{
  padding: 2rem 1.5rem !important;
}}

/* ── Typography ─────────────────────────────────────────────── */
h1, h2, h3, h4 {{
  font-family: var(--ff-d) !important;
  letter-spacing: 0.05em !important;
  color: var(--text) !important;
  line-height: 1 !important;
}}

/* ── Labels ─────────────────────────────────────────────────── */
label,
.stSelectbox > label,
.stTextInput > label,
.stCheckbox > label span,
.stRadio > label,
.stRadio > div > label p {{
  font-family: var(--ff-m) !important;
  font-size: 0.68rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.16em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}}

/* ── Text Input ─────────────────────────────────────────────── */
.stTextInput > div > div > input {{
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
  color: var(--text) !important;
  font-family: var(--ff-m) !important;
  font-size: 0.95rem !important;
  padding: 0.65rem 1rem !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  caret-color: var(--accent) !important;
}}
.stTextInput > div > div > input:focus {{
  border-color: var(--border2) !important;
  box-shadow: var(--glow) !important;
  outline: none !important;
  background: var(--bg4) !important;
}}
.stTextInput > div > div > input::placeholder {{
  color: var(--faint) !important;
  font-style: italic !important;
}}

/* ── Select ─────────────────────────────────────────────────── */
[data-baseweb="select"] > div {{
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
  color: var(--text) !important;
  font-family: var(--ff-m) !important;
  font-size: 0.88rem !important;
  transition: border-color 0.2s !important;
}}
[data-baseweb="select"] > div:hover {{
  border-color: var(--border2) !important;
}}
[data-baseweb="popover"] [data-testid="stVirtualDropdown"],
[data-baseweb="popover"] ul {{
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
}}
[data-baseweb="popover"] li {{
  font-family: var(--ff-m) !important;
  font-size: 0.84rem !important;
  color: var(--text) !important;
  background: transparent !important;
}}
[data-baseweb="popover"] li:hover,
[data-baseweb="popover"] [aria-selected="true"] {{
  background: var(--dim) !important;
  color: var(--accent) !important;
}}

/* ── Primary Button ─────────────────────────────────────────── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {{
  background: linear-gradient(118deg, #00FFB3 0%, #00C896 100%) !important;
  color: #040810 !important;
  border: none !important;
  border-radius: 4px !important;
  font-family: var(--ff-h) !important;
  font-weight: 700 !important;
  font-size: 0.8rem !important;
  letter-spacing: 0.24em !important;
  text-transform: uppercase !important;
  padding: 0.85rem 1.5rem !important;
  transition: box-shadow 0.25s, transform 0.18s !important;
  box-shadow: 0 0 28px rgba(0,255,179,0.25), 0 2px 12px rgba(0,0,0,0.4) !important;
}}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {{
  box-shadow: 0 0 50px rgba(0,255,179,0.45), 0 4px 20px rgba(0,0,0,0.5) !important;
  transform: translateY(-2px) !important;
}}
.stButton > button[kind="primary"]:active {{
  transform: translateY(0) !important;
}}

/* ── Secondary / Download Buttons ───────────────────────────── */
.stButton > button:not([kind="primary"]),
.stDownloadButton > button {{
  background: transparent !important;
  border: 1px solid var(--border2) !important;
  color: var(--accent) !important;
  border-radius: 4px !important;
  font-family: var(--ff-m) !important;
  font-size: 0.74rem !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  transition: background 0.2s, box-shadow 0.2s !important;
}}
.stButton > button:not([kind="primary"]):hover,
.stDownloadButton > button:hover {{
  background: var(--dim) !important;
  box-shadow: var(--glow) !important;
}}

/* ── Checkbox ───────────────────────────────────────────────── */
.stCheckbox > label > div:first-child > div {{
  border-color: var(--border2) !important;
}}
.stCheckbox > label > div:first-child input:checked ~ div {{
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}}

/* ── Radio ──────────────────────────────────────────────────── */
.stRadio > div > label {{
  font-family: var(--ff-m) !important;
  font-size: 0.78rem !important;
  color: var(--sub) !important;
}}

/* ── Metric ─────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 1.5rem !important;
  position: relative !important;
  overflow: hidden !important;
}}
[data-testid="stMetric"]::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent), transparent);
}}
[data-testid="stMetricLabel"] p {{
  font-family: var(--ff-m) !important;
  font-size: 0.66rem !important;
  letter-spacing: 0.16em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}}
[data-testid="stMetricValue"] {{
  font-family: var(--ff-d) !important;
  font-size: 2.8rem !important;
  color: var(--accent) !important;
  letter-spacing: 0.02em !important;
  line-height: 1.1 !important;
}}
[data-testid="stMetricDelta"] {{
  font-family: var(--ff-m) !important;
  font-size: 0.74rem !important;
}}

/* ── Expander ───────────────────────────────────────────────── */
[data-testid="stExpander"] {{
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  margin-bottom: 0.55rem !important;
  overflow: hidden !important;
}}
[data-testid="stExpander"] summary {{
  padding: 0.9rem 1.25rem !important;
  font-family: var(--ff-m) !important;
  font-size: 0.8rem !important;
  color: var(--text) !important;
  border-left: 3px solid transparent !important;
  transition: background 0.2s, border-color 0.2s !important;
  list-style: none !important;
}}
[data-testid="stExpander"] summary:hover {{
  background: var(--dim) !important;
  border-left-color: var(--accent) !important;
}}
[data-testid="stExpander"][open] > details > summary,
[data-testid="stExpander"] details[open] > summary {{
  border-left-color: var(--accent) !important;
  color: var(--accent) !important;
}}

/* ── Alert blocks ───────────────────────────────────────────── */
[data-testid="stAlert"] {{
  border-radius: 6px !important;
  border-left: 3px solid !important;
  border-top: 1px solid !important;
  border-right: 1px solid !important;
  border-bottom: 1px solid !important;
  font-family: var(--ff-b) !important;
  font-size: 0.88rem !important;
  line-height: 1.65 !important;
}}
[data-testid="stAlert"][data-baseweb="notification"] {{
  background: rgba(6,182,212,0.07) !important;
  border-color: rgba(6,182,212,0.22) !important;
  border-left-color: var(--accent2) !important;
}}
.stAlert[data-testid="stAlert"] {{
  background: rgba(245,158,11,0.07) !important;
  border-color: rgba(245,158,11,0.22) !important;
  border-left-color: var(--amber) !important;
}}
[data-testid="stException"] {{
  background: rgba(244,63,94,0.07) !important;
  border-color: rgba(244,63,94,0.22) !important;
}}

/* ── Spinner ────────────────────────────────────────────────── */
.stSpinner > div {{ border-top-color: var(--accent) !important; }}

/* ── Caption ────────────────────────────────────────────────── */
.stCaption,
[data-testid="stCaptionContainer"] p {{
  font-family: var(--ff-m) !important;
  font-size: 0.68rem !important;
  color: var(--muted) !important;
  letter-spacing: 0.06em !important;
}}

/* ── Divider ────────────────────────────────────────────────── */
hr {{
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 2rem 0 !important;
}}

/* ── Code ───────────────────────────────────────────────────── */
code {{
  background: var(--bg2) !important;
  color: var(--accent) !important;
  font-family: var(--ff-m) !important;
  font-size: 0.84em !important;
  padding: 0.15em 0.5em !important;
  border-radius: 3px !important;
  border: 1px solid var(--border) !important;
}}

/* ── Scrollbar ──────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border2); border-radius: 2px; }}

/* ── Animations ─────────────────────────────────────────────── */
@keyframes slideUp {{
  from {{ opacity: 0; transform: translateY(22px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
  from {{ opacity: 0; }}
  to   {{ opacity: 1; }}
}}
@keyframes scanPulse {{
  0%,100% {{ opacity: 0.45; }}
  50%      {{ opacity: 1; }}
}}
@keyframes barFill {{
  from {{ width: 0%; opacity: 0; }}
  to   {{ width: var(--bar-w); opacity: 1; }}
}}
@keyframes ticker {{
  from {{ transform: translateX(0); }}
  to   {{ transform: translateX(-50%); }}
}}
@keyframes glowPulse {{
  0%,100% {{ box-shadow: 0 0 18px rgba(0,255,179,0.18); }}
  50%      {{ box-shadow: 0 0 36px rgba(0,255,179,0.38); }}
}}

.hero-anim   {{ animation: slideUp 0.65s cubic-bezier(.16,1,.3,1) forwards; }}
.report-anim {{ animation: slideUp 0.5s cubic-bezier(.16,1,.3,1) 0.05s both; }}
.card-anim   {{ animation: slideUp 0.5s cubic-bezier(.16,1,.3,1) both; }}

/* ── Ticker tape ────────────────────────────────────────────── */
.ticker-wrap {{
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  border-top: 1px solid var(--border);
  padding: 0.5rem 0;
  overflow: hidden;
  white-space: nowrap;
  position: relative;
  margin: 0 -3.5rem 0;
}}
.ticker-wrap::before,
.ticker-wrap::after {{
  content: '';
  position: absolute;
  top: 0; bottom: 0;
  width: 6rem;
  z-index: 2;
  pointer-events: none;
}}
.ticker-wrap::before {{ left: 0; background: linear-gradient(90deg, var(--bg2), transparent); }}
.ticker-wrap::after  {{ right: 0; background: linear-gradient(-90deg, var(--bg2), transparent); }}
.ticker-inner {{
  display: inline-flex;
  gap: 2.5rem;
  animation: ticker 32s linear infinite;
}}
.ticker-item {{
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  font-family: var(--ff-m);
  font-size: 0.68rem;
  letter-spacing: 0.04em;
  color: var(--muted);
  flex-shrink: 0;
}}
.ticker-sep {{ color: var(--faint); }}
.ticker-sym {{ color: var(--sub); font-weight: 500; }}
.ticker-up  {{ color: var(--green); }}
.ticker-dn  {{ color: var(--red); }}

/* ── Sidebar brand ──────────────────────────────────────────── */
.mira-brand {{
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding-bottom: 1.75rem;
  margin-bottom: 1.25rem;
  border-bottom: 1px solid var(--border);
}}
.mira-brand-icon {{
  width: 38px; height: 38px;
  background: linear-gradient(135deg, var(--accent), #00C896);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; font-weight: 700; color: #040810;
  flex-shrink: 0;
  animation: glowPulse 3s ease-in-out infinite;
}}
.mira-brand-text {{ line-height: 1.2; }}
.mira-brand-name {{
  font-family: 'Syne', sans-serif;
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: var(--text);
}}
.mira-brand-sub {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.57rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  margin-top: 3px;
}}

/* ── Live badge ─────────────────────────────────────────────── */
.live-badge {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--green);
  background: rgba(16,185,129,0.08);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: 3px;
  padding: 0.28rem 0.65rem;
  margin-bottom: 1.5rem;
}}
.live-dot {{
  width: 5px; height: 5px;
  background: var(--green);
  border-radius: 50%;
  animation: scanPulse 1.4s ease-in-out infinite;
}}

/* ── Sidebar info rows ──────────────────────────────────────── */
.sidebar-info {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: var(--muted);
  line-height: 1.8;
}}
.si-row {{
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid var(--border);
}}
.si-row:last-child {{ border-bottom: none; }}
.si-label {{
  color: var(--faint);
  font-size: 0.6rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  width: 58px;
  flex-shrink: 0;
}}
.si-val {{
  color: var(--sub);
  font-size: 0.68rem;
}}

/* ── Section label ──────────────────────────────────────────── */
.section-label {{
  font-family: 'Syne', sans-serif;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.25rem;
}}
.section-label .dot {{
  color: var(--accent);
  font-size: 0.5rem;
  animation: scanPulse 2.5s ease-in-out infinite;
}}

/* ── Hero ───────────────────────────────────────────────────── */
.hero {{
  padding: 4rem 0 3.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0;
}}
.hero-eyebrow {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.63rem;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 1.75rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}}
.hero-eyebrow::before {{
  content: '';
  display: inline-block;
  width: 28px; height: 1px;
  background: var(--accent);
  opacity: 0.55;
}}
.hero-layout {{
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 3rem;
}}
.hero-title {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(4rem, 7.5vw, 7rem);
  line-height: 0.88;
  letter-spacing: 0.04em;
  color: var(--text);
  margin-bottom: 0;
}}
.hero-title-outline {{
  -webkit-text-stroke: 1.5px var(--accent);
  color: transparent;
  display: block;
}}
.hero-sub {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.9rem;
  color: var(--muted);
  letter-spacing: 0.01em;
  line-height: 1.75;
  max-width: 460px;
  margin-top: 1.5rem;
}}
.hero-meta {{
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1.5rem;
  padding-bottom: 0.5rem;
}}
.hero-meta-item {{
  text-align: right;
}}
.hero-meta-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--faint);
  display: block;
  margin-bottom: 0.25rem;
}}
.hero-meta-val {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.8rem;
  color: var(--sub);
  letter-spacing: 0.06em;
  line-height: 1;
}}

/* ── Input panel titlebar ───────────────────────────────────── */
.input-panel-titlebar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-bottom: none;
  border-radius: 10px 10px 0 0;
  padding: 0.9rem 1.5rem;
  margin-top: 2.5rem;
  position: relative;
}}
.input-panel-titlebar::after {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0.2;
}}
.panel-dots {{
  display: flex;
  gap: 0.4rem;
  align-items: center;
}}
.panel-dot {{
  width: 9px; height: 9px;
  border-radius: 50%;
}}
.panel-dot-r {{ background: #F43F5E; opacity: 0.6; }}
.panel-dot-y {{ background: #F59E0B; opacity: 0.6; }}
.panel-dot-g {{ background: var(--accent); opacity: 0.6; }}

/* ── Report header ──────────────────────────────────────────── */
.report-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 1.75rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--border);
  position: relative;
  overflow: visible;
}}
.report-header-ghost {{
  position: absolute;
  right: -0.5rem; top: -1.5rem;
  font-family: 'Bebas Neue', sans-serif;
  font-size: 10rem;
  line-height: 1;
  color: rgba(0,255,179,0.03);
  letter-spacing: 0.04em;
  pointer-events: none;
  user-select: none;
  clip-path: inset(0 0 0 0);
}}
.report-ticker {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 5.5rem;
  line-height: 0.86;
  letter-spacing: 0.04em;
  color: var(--text);
}}
.report-company {{
  font-family: 'Outfit', sans-serif;
  font-size: 1rem;
  color: var(--sub);
  margin-top: 0.5rem;
  font-weight: 300;
  letter-spacing: 0.02em;
}}
.report-badge {{
  display: inline-block;
  padding: 0.28rem 0.8rem;
  border: 1px solid var(--border2);
  border-radius: 3px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--accent);
  margin-top: 0.8rem;
  background: rgba(0,255,179,0.04);
}}
.report-ts {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  color: var(--faint);
  margin-top: 0.3rem;
}}
.report-ts-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--faint);
}}

/* ── Info card ──────────────────────────────────────────────── */
.info-card {{
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
  height: 100%;
}}
.info-card-accent-top {{
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent), transparent);
}}
.info-card-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.75rem;
}}
.info-card-value-big {{
  font-family: 'Bebas Neue', sans-serif;
  font-size: 3.5rem;
  line-height: 1;
  letter-spacing: 0.02em;
}}
.info-card-sub {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  color: var(--muted);
  margin-top: 0.4rem;
  letter-spacing: 0.06em;
}}
.info-card-body {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.875rem;
  color: var(--sub);
  line-height: 1.8;
  margin: 0;
}}

/* ── Summary card ───────────────────────────────────────────── */
.summary-card {{
  background: var(--bg3);
  border: 1px solid rgba(6,182,212,0.14);
  border-radius: 8px;
  padding: 1.75rem 1.75rem 1.75rem 2rem;
  margin-bottom: 2rem;
  position: relative;
  overflow: hidden;
}}
.summary-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  background: linear-gradient(180deg, var(--accent2), rgba(6,182,212,0.1));
}}
.summary-label {{
  font-family: 'Syne', sans-serif;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--accent2);
  margin-bottom: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}}
.summary-text {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.95rem;
  color: #C8D8E8;
  line-height: 1.85;
  margin: 0;
}}

/* ── Factor card ────────────────────────────────────────────── */
.factor-card {{
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 6px;
  margin-bottom: 0.75rem;
  overflow: hidden;
  transition: border-color 0.2s, transform 0.15s;
}}
.factor-card:hover {{
  border-color: var(--border2);
  transform: translateX(3px);
}}
.factor-header {{
  padding: 1rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 3px solid transparent;
}}
.factor-header-meta {{
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}}
.conf-badge {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.57rem;
  font-weight: 600;
  letter-spacing: 0.16em;
  padding: 0.22rem 0.6rem;
  border-radius: 2px;
}}
.cat-badge {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.57rem;
  letter-spacing: 0.12em;
  color: var(--muted);
  background: var(--bg2);
  padding: 0.22rem 0.6rem;
  border-radius: 2px;
}}
.factor-title {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--text);
}}
.factor-num {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  color: var(--faint);
  flex-shrink: 0;
  letter-spacing: 0.06em;
}}
.factor-body {{
  padding: 0 1.25rem 1.25rem;
  border-top: 1px solid rgba(0,255,179,0.04);
}}
.factor-desc {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.875rem;
  color: var(--sub);
  line-height: 1.78;
  margin: 1rem 0 0.85rem;
}}

/* ── Confidence bar ─────────────────────────────────────────── */
.conf-bar-wrap {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0.25rem 0 0.75rem;
}}
.conf-bar-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.56rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  flex-shrink: 0;
  width: 62px;
}}
.conf-bar-track {{
  flex: 1;
  height: 3px;
  background: var(--faint);
  border-radius: 2px;
  overflow: hidden;
}}
.conf-bar-fill {{
  height: 100%;
  border-radius: 2px;
  width: var(--bar-w);
  animation: barFill 0.9s cubic-bezier(.16,1,.3,1) 0.2s both;
}}
.conf-pct {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: var(--muted);
  flex-shrink: 0;
  width: 30px;
  text-align: right;
}}

/* ── Evidence ───────────────────────────────────────────────── */
.evidence-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.56rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--faint);
  margin: 0.75rem 0 0.55rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}}
.evidence-label::after {{
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}}
.evidence-item {{
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0.38rem;
  align-items: flex-start;
}}
.evidence-arrow {{
  color: var(--accent);
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  margin-top: 0.2rem;
  opacity: 0.55;
}}
.evidence-text {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.8rem;
  color: var(--muted);
  line-height: 1.62;
}}

/* ── Risk / Outlook cards ───────────────────────────────────── */
.risk-card {{
  background: var(--bg3);
  border: 1px solid rgba(244,63,94,0.14);
  border-radius: 8px;
  padding: 1.5rem 1.5rem 1.5rem 1.8rem;
  position: relative;
  overflow: hidden;
  height: 100%;
}}
.risk-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  background: linear-gradient(180deg, #F43F5E, rgba(244,63,94,0.1));
}}
.outlook-card {{
  background: var(--bg3);
  border: 1px solid rgba(16,185,129,0.14);
  border-radius: 8px;
  padding: 1.5rem 1.5rem 1.5rem 1.8rem;
  position: relative;
  overflow: hidden;
  height: 100%;
}}
.outlook-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  background: linear-gradient(180deg, #10B981, rgba(16,185,129,0.1));
}}
.card-section-label {{
  font-family: 'Syne', sans-serif;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}}
.card-section-body {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.875rem;
  color: var(--sub);
  line-height: 1.8;
  margin: 0;
}}

/* ── Data quality note ──────────────────────────────────────── */
.dq-note {{
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem 1.25rem;
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  margin-bottom: 2rem;
}}
.dq-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.57rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--faint);
  flex-shrink: 0;
  margin-top: 0.1rem;
  line-height: 1.8;
}}
.dq-body {{
  font-family: 'Outfit', sans-serif;
  font-size: 0.8rem;
  color: var(--faint);
  line-height: 1.7;
}}

/* ── Scan dots ──────────────────────────────────────────────── */
.scan-active {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.74rem;
  color: var(--accent);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}}
.scan-dot {{
  width: 6px; height: 6px;
  background: var(--accent);
  border-radius: 50%;
  animation: scanPulse 0.8s ease-in-out infinite;
}}
.scan-dot:nth-child(2) {{ animation-delay: 0.15s; }}
.scan-dot:nth-child(3) {{ animation-delay: 0.3s; }}

/* ── Theme toggle ────────────────────────────────────────────── */
.theme-section-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.58rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--faint);
  margin-bottom: 0.5rem;
}}
.theme-row {{
  display: flex;
  align-items: center;
  gap: 0.65rem;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.55rem 0.9rem;
  margin-bottom: 0.4rem;
}}
.theme-row-icon {{
  font-size: 0.85rem;
  flex-shrink: 0;
  line-height: 1;
}}
.theme-row-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  color: var(--sub);
  flex: 1;
}}
.theme-toggle-track {{
  width: 30px; height: 16px;
  background: var(--faint);
  border-radius: 8px;
  position: relative;
  flex-shrink: 0;
  transition: background 0.3s;
}}
.theme-toggle-track.is-light {{
  background: var(--accent);
}}
.theme-toggle-thumb {{
  width: 12px; height: 12px;
  background: var(--bg);
  border-radius: 50%;
  position: absolute;
  top: 2px; left: 2px;
  transition: transform 0.3s cubic-bezier(.16,1,.3,1), background 0.3s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.35);
}}
.theme-toggle-track.is-light .theme-toggle-thumb {{
  transform: translateX(14px);
}}
</style>
"""


def _inject_css() -> None:
    t = _theme_vars()
    st.markdown(_build_css(t), unsafe_allow_html=True)


_inject_css()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    _is_dark = st.session_state["theme"] == "dark"
    st.markdown(
        f"""
<div class="mira-brand">
  <div class="mira-brand-icon">◈</div>
  <div class="mira-brand-text">
    <div class="mira-brand-name">MIRA</div>
    <div class="mira-brand-sub">Market Analyst · v0.1.0</div>
  </div>
</div>
<div class="live-badge">
  <div class="live-dot"></div> System Online
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Theme toggle ──────────────────────────────────────────────────────────
    _track_class = "theme-toggle-track" + ("" if _is_dark else " is-light")
    _theme_label = "Dark Mode" if _is_dark else "Light Mode"
    _theme_icon  = "🌙" if _is_dark else "☀️"
    st.markdown(
        f"""
<div class="theme-section-label">Appearance</div>
<div class="theme-row">
  <span class="theme-row-icon">{_theme_icon}</span>
  <span class="theme-row-label">{_theme_label}</span>
  <div class="{_track_class}">
    <div class="theme-toggle-thumb"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button(
        f"Switch to {'Light' if _is_dark else 'Dark'} Mode",
        use_container_width=True,
        key="theme_toggle_btn",
    ):
        st.session_state["theme"] = "light" if _is_dark else "dark"
        st.rerun()

    mode = st.radio(
        "Backend Mode",
        ["API (FastAPI)", "Direct (in-process)"],
        help="API mode requires the FastAPI server running on port 8000.",
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        """
<div class="sidebar-info">
  <div class="si-row">
    <span class="si-label">Engine</span>
    <span class="si-val">LangChain + OpenAI</span>
  </div>
  <div class="si-row">
    <span class="si-label">News</span>
    <span class="si-val">Finnhub API</span>
  </div>
  <div class="si-row">
    <span class="si-label">Prices</span>
    <span class="si-val">yFinance</span>
  </div>
  <div class="si-row">
    <span class="si-label">Filings</span>
    <span class="si-val">SEC EDGAR</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ── Ticker tape ───────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="ticker-wrap">
  <div class="ticker-inner">
    <span class="ticker-item"><span class="ticker-sym">AAPL</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +1.24%</span></span>
    <span class="ticker-item"><span class="ticker-sym">TSLA</span><span class="ticker-sep">·</span><span class="ticker-dn">▼ −2.87%</span></span>
    <span class="ticker-item"><span class="ticker-sym">NVDA</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +3.41%</span></span>
    <span class="ticker-item"><span class="ticker-sym">MSFT</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +0.93%</span></span>
    <span class="ticker-item"><span class="ticker-sym">GOOGL</span><span class="ticker-sep">·</span><span class="ticker-dn">▼ −0.55%</span></span>
    <span class="ticker-item"><span class="ticker-sym">AMZN</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +1.78%</span></span>
    <span class="ticker-item"><span class="ticker-sym">META</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +2.14%</span></span>
    <span class="ticker-item"><span class="ticker-sym">BRK.B</span><span class="ticker-sep">·</span><span class="ticker-dn">▼ −0.31%</span></span>
    <span class="ticker-item"><span class="ticker-sym">JPM</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +0.67%</span></span>
    <span class="ticker-item"><span class="ticker-sym">XOM</span><span class="ticker-sep">·</span><span class="ticker-dn">▼ −1.22%</span></span>
    <span class="ticker-item"><span class="ticker-sym">NFLX</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +0.88%</span></span>
    <span class="ticker-item"><span class="ticker-sym">AMD</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +4.02%</span></span>
    <!-- duplicate for seamless loop -->
    <span class="ticker-item"><span class="ticker-sym">AAPL</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +1.24%</span></span>
    <span class="ticker-item"><span class="ticker-sym">TSLA</span><span class="ticker-sep">·</span><span class="ticker-dn">▼ −2.87%</span></span>
    <span class="ticker-item"><span class="ticker-sym">NVDA</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +3.41%</span></span>
    <span class="ticker-item"><span class="ticker-sym">MSFT</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +0.93%</span></span>
    <span class="ticker-item"><span class="ticker-sym">GOOGL</span><span class="ticker-sep">·</span><span class="ticker-dn">▼ −0.55%</span></span>
    <span class="ticker-item"><span class="ticker-sym">AMZN</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +1.78%</span></span>
    <span class="ticker-item"><span class="ticker-sym">META</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +2.14%</span></span>
    <span class="ticker-item"><span class="ticker-sym">BRK.B</span><span class="ticker-sep">·</span><span class="ticker-dn">▼ −0.31%</span></span>
    <span class="ticker-item"><span class="ticker-sym">JPM</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +0.67%</span></span>
    <span class="ticker-item"><span class="ticker-sym">XOM</span><span class="ticker-sep">·</span><span class="ticker-dn">▼ −1.22%</span></span>
    <span class="ticker-item"><span class="ticker-sym">NFLX</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +0.88%</span></span>
    <span class="ticker-item"><span class="ticker-sym">AMD</span><span class="ticker-sep">·</span><span class="ticker-up">▲ +4.02%</span></span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero hero-anim">
  <div class="hero-eyebrow">AI-Powered Equity Analysis System</div>
  <div class="hero-layout">
    <div>
      <div class="hero-title">
        MARKET<br>
        <span class="hero-title-outline">INCIDENT</span>
        ANALYST
      </div>
      <p class="hero-sub">
        Detects and explains unusual stock price movements using real-time data,
        news sentiment, SEC filings, and multi-factor LLM synthesis.
      </p>
    </div>
    <div class="hero-meta">
      <div class="hero-meta-item">
        <span class="hero-meta-label">Data Sources</span>
        <span class="hero-meta-val">04</span>
      </div>
      <div class="hero-meta-item">
        <span class="hero-meta-label">LLM Engine</span>
        <span class="hero-meta-val">GPT-4</span>
      </div>
      <div class="hero-meta-item">
        <span class="hero-meta-label">Avg Latency</span>
        <span class="hero-meta-val">~30s</span>
      </div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# ── Input Panel ───────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="input-panel-titlebar">
  <div class="panel-dots">
    <div class="panel-dot panel-dot-r"></div>
    <div class="panel-dot panel-dot-y"></div>
    <div class="panel-dot panel-dot-g"></div>
  </div>
  <div class="section-label" style="margin-bottom:0;">
    <span class="dot">◆</span> Analysis Parameters
  </div>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 2])

with col1:
    ticker = (
        st.text_input(
            "Stock Ticker",
            value="",
            placeholder="e.g. AAPL",
            max_chars=5,
            help="US stock ticker symbol — 1 to 5 uppercase letters",
        )
        .upper()
        .strip()
    )

with col2:
    query = st.text_input(
        "Research Question (optional)",
        value="",
        placeholder="e.g. Why is this stock moving today?",
    )

col3, col4 = st.columns([1, 2])

with col3:
    period = st.selectbox(
        "Lookback Period",
        ["1mo", "3mo", "6mo", "1y"],
        index=1,
    )

with col4:
    include_filings = st.checkbox(
        "Include SEC filings analysis (slower)",
        value=False,
    )

# ── Backend Functions ─────────────────────────────────────────────────────────
def call_api(
    ticker: str, query: str, period: str, include_filings: bool
) -> dict:
    payload: dict = {
        "ticker": ticker,
        "period": period,
        "include_filings": include_filings,
    }
    if query:
        payload["query"] = query

    resp = httpx.post(f"{API_URL}/analyze", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def call_direct(
    ticker: str, query: str, period: str, include_filings: bool
) -> dict:
    import asyncio

    from app.config import get_settings
    from app.models.request import AnalysisRequest
    from app.orchestrator import analyze

    request = AnalysisRequest(
        ticker=ticker,
        query=query or None,
        period=period,
        include_filings=include_filings,
    )
    settings = get_settings()
    report = asyncio.run(analyze(request, settings))
    return report.model_dump(mode="json")


# ── Report Renderer ───────────────────────────────────────────────────────────
def _conf_colors(conf: str) -> tuple[str, str]:
    """Return (hex_color, rgba_bg) for a confidence level."""
    return {
        "high":   ("#F43F5E", "rgba(244,63,94,0.12)"),
        "medium": ("#F59E0B", "rgba(245,158,11,0.12)"),
        "low":    ("#10B981", "rgba(16,185,129,0.12)"),
    }.get(conf, ("#64748B", "rgba(100,116,139,0.12)"))


def render_factor(factor: dict, index: int) -> str:
    conf = factor.get("confidence", "low")
    conf_color, conf_bg = _conf_colors(conf)
    category = html_module.escape(factor.get("category", "other")).upper()
    title    = html_module.escape(factor.get("title", "Unknown Factor"))
    desc     = html_module.escape(factor.get("description", ""))
    evidence = factor.get("supporting_evidence", [])

    bar_widths = {"high": "85%", "medium": "52%", "low": "28%"}
    bar_pcts   = {"high": "85", "medium": "52", "low": "28"}
    bar_w   = bar_widths.get(conf, "28%")
    bar_pct = bar_pcts.get(conf, "28")

    ev_html = ""
    if evidence:
        items = "".join(
            f'<div class="evidence-item">'
            f'<span class="evidence-arrow">›</span>'
            f'<span class="evidence-text">{html_module.escape(str(ev))}</span>'
            f"</div>"
            for ev in evidence
        )
        ev_html = (
            f'<div class="evidence-label">Supporting Evidence</div>'
            f"{items}"
        )

    return (
        f'<div class="factor-card">'
        f'  <div class="factor-header" style="border-left-color:{conf_color};">'
        f'    <div class="factor-header-meta">'
        f'      <span class="conf-badge" style="color:{conf_color};background:{conf_bg};">'
        f'        {conf.upper()}'
        f'      </span>'
        f'      <span class="cat-badge">{category}</span>'
        f'      <span class="factor-title">{title}</span>'
        f'    </div>'
        f'    <span class="factor-num">#{index:02d}</span>'
        f'  </div>'
        f'  <div class="factor-body">'
        f'    <div class="conf-bar-wrap">'
        f'      <span class="conf-bar-label">Confidence</span>'
        f'      <div class="conf-bar-track">'
        f'        <div class="conf-bar-fill" style="--bar-w:{bar_w};background:{conf_color};"></div>'
        f'      </div>'
        f'      <span class="conf-pct">{bar_pct}%</span>'
        f'    </div>'
        f'    <p class="factor-desc">{desc}</p>'
        f"    {ev_html}"
        f"  </div>"
        f"</div>"
    )


def _format_ts(generated_at: str) -> str:
    """Parse ISO timestamp to display string, robust to timezone variants."""
    try:
        return datetime.fromisoformat(generated_at).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return generated_at[:19].replace("T", " ") if len(generated_at) >= 19 else generated_at


def render_report(report: dict) -> None:
    ticker_sym   = html_module.escape(report.get("ticker", ""))
    company      = html_module.escape(report.get("company_name", "Unknown"))
    generated_at = report.get("generated_at", "")
    summary      = html_module.escape(report.get("executive_summary", ""))
    price_move   = report.get("price_move", {})
    factors      = report.get("factors", [])
    risk         = html_module.escape(report.get("risk_assessment", "N/A"))
    outlook      = html_module.escape(report.get("outlook", "N/A"))
    dq_note      = html_module.escape(report.get("data_quality_note", "N/A"))

    direction  = price_move.get("direction", "flat")
    magnitude  = price_move.get("magnitude_pct", 0.0)
    timeframe  = html_module.escape(price_move.get("timeframe", "N/A"))
    move_desc  = html_module.escape(price_move.get("description", "N/A"))

    mag_color  = "#00FFB3" if direction == "up" else "#F43F5E" if direction == "down" else "#64748B"
    dir_icon   = "▲" if direction == "up" else "▼" if direction == "down" else "◆"
    mag_sign   = "+" if magnitude >= 0 else ""
    ts_display = _format_ts(generated_at)

    # ── Report header ─────────────────────────────────────────────────────────
    st.markdown(
        f"""
<div class="report-anim">
  <div class="report-header">
    <div>
      <div class="report-ticker">{ticker_sym}</div>
      <div class="report-company">{company}</div>
      <div class="report-badge">Incident Report</div>
    </div>
    <div style="text-align:right;">
      <div class="report-ts-label">Generated</div>
      <div class="report-ts">{ts_display}</div>
    </div>
    <div class="report-header-ghost">{ticker_sym}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Price move + description ──────────────────────────────────────────────
    mc1, mc2 = st.columns([1, 2])
    with mc1:
        st.markdown(
            f"""
<div class="info-card card-anim" style="animation-delay:0.05s;">
  <div class="info-card-accent-top" style="background:linear-gradient(90deg,{mag_color},transparent);"></div>
  <div class="info-card-label">Price Move</div>
  <div class="info-card-value-big" style="color:{mag_color};">
    {dir_icon} {mag_sign}{magnitude:.1f}%
  </div>
  <div class="info-card-sub">{timeframe}</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with mc2:
        st.markdown(
            f"""
<div class="info-card card-anim" style="animation-delay:0.1s;">
  <div class="info-card-accent-top"></div>
  <div class="info-card-label">Movement Description</div>
  <p class="info-card-body">{move_desc}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Executive summary ─────────────────────────────────────────────────────
    st.markdown(
        f"""
<div class="summary-card card-anim" style="animation-delay:0.15s;">
  <div class="summary-label">◆ Executive Summary</div>
  <p class="summary-text">{summary}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Contributing factors ──────────────────────────────────────────────────
    factor_count = len(factors)
    st.markdown(
        f"""
<div class="section-label" style="margin-bottom:1rem;">
  <span class="dot">◆</span> Contributing Factors
  <span style="padding:0.15rem 0.55rem;background:rgba(0,255,179,0.08);border-radius:3px;
               color:#00FFB3;font-family:'JetBrains Mono',monospace;font-size:0.65rem;">{factor_count}</span>
</div>
""",
        unsafe_allow_html=True,
    )

    if factors:
        for i, factor in enumerate(factors, 1):
            st.markdown(render_factor(factor, i), unsafe_allow_html=True)
    else:
        st.warning("No contributing factors were identified.")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ── Risk + Outlook ────────────────────────────────────────────────────────
    rc, oc = st.columns(2)
    with rc:
        st.markdown(
            f"""
<div class="risk-card card-anim" style="animation-delay:0.2s;">
  <div class="card-section-label">
    <span style="color:#F43F5E;">◆</span> Risk Assessment
  </div>
  <p class="card-section-body">{risk}</p>
</div>
""",
            unsafe_allow_html=True,
        )
    with oc:
        st.markdown(
            f"""
<div class="outlook-card card-anim" style="animation-delay:0.25s;">
  <div class="card-section-label">
    <span style="color:#10B981;">◆</span> Outlook
  </div>
  <p class="card-section-body">{outlook}</p>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Data quality note ─────────────────────────────────────────────────────
    st.markdown(
        f"""
<div class="dq-note">
  <div class="dq-label">Data<br>Note</div>
  <div class="dq-body">{dq_note}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Download ──────────────────────────────────────────────────────────────
    st.download_button(
        label="⬇  Download Report (JSON)",
        data=json.dumps(report, indent=2, default=str),
        file_name=f"mira_report_{ticker_sym}.json",
        mime="application/json",
    )


# ── Input widgets ─────────────────────────────────────────────────────────────
analyze_btn = st.button(
    "⬡  Run Analysis",
    type="primary",
    use_container_width=True,
)

if analyze_btn:
    if not ticker or not ticker.isalpha() or len(ticker) > 5:
        st.error("Please enter a valid ticker symbol (1–5 uppercase letters).")
    else:
        with st.spinner("Gathering market intelligence…"):
            try:
                if mode == "API (FastAPI)":
                    report = call_api(ticker, query, period, include_filings)
                else:
                    report = call_direct(ticker, query, period, include_filings)

                st.session_state["report"] = report
            except httpx.ConnectError:
                st.error(
                    "Cannot reach the API server. "
                    "Ensure the FastAPI backend is running on port 8000, "
                    "or switch to Direct mode in the sidebar."
                )
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")


# ── Display ───────────────────────────────────────────────────────────────────
if "report" in st.session_state:
    st.markdown(
        """<hr>
<div class="section-label">
  <span class="dot">◆</span> Analysis Report
</div>""",
        unsafe_allow_html=True,
    )
    render_report(st.session_state["report"])
