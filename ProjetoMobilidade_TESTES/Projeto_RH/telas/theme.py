"""Configuração de tema e CSS do Streamlit."""

import streamlit as st


def aplicar_tema():
    """Aplica o tema institucional RENAPSI."""
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background: #FFFFFF !important;
        font-size: 18px !important;
    }

    [data-testid="stSidebar"] {
        background: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }

    [data-testid="stSidebar"] .stRadio > label {
        color: #1E293B !important;
        font-size: 20px !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #333333 !important;
        font-size: 19px !important;
    }

    [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
        color: #64748B;
        font-size: 20px !important;
        transition: color 0.2s;
    }

    [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p:hover {
        color: #f8ae28;
    }

    div[data-testid="metric-container"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-size: 19px !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f8ae28 !important;
        font-size: 2.6rem !important;
        font-weight: 700;
    }

    div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
        background: #f8ae28 !important;
        color: #FFFFFF !important;
        padding: 4px 8px !important;
        border-radius: 6px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }

    div[data-testid="metric-container"] [data-testid="stMetricDelta"] svg {
        display: none !important;
    }

    h1, h2, h3 { color: #1E293B !important; font-size: 1.5em !important; }
    h4 { color: #333333 !important; font-size: 1.3em !important; }

    p, span, div, label, input, textarea, select {
        color: #333333 !important;
        font-size: 19px !important;
    }

    .stButton > button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background: #f8ae28 !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 20px !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(248,174,40,0.3) !important;
        transition: background 0.2s, transform 0.1s !important;
    }

    .stButton > button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background: #e09a1f !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(248,174,40,0.4) !important;
    }

    .stButton > button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background: #444c9b !important;
        border: none !important;
        color: #FFFFFF !important;
        font-size: 20px !important;
        border-radius: 8px !important;
        transition: background 0.2s, box-shadow 0.2s !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #363d7f !important;
        box-shadow: 0 2px 6px rgba(68,76,155,0.3) !important;
    }

    .stButton > button:not([kind]),
    button[data-testid="baseButton-minimal"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        color: #333333 !important;
        font-size: 20px !important;
        border-radius: 8px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }

    .stButton > button:not([kind]):hover,
    button[data-testid="baseButton-minimal"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        background: #F8FAFC !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #F8FAFC;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #E2E8F0;
    }

    .stTabs [data-baseweb="tab"] {
        color: #64748B !important;
        font-size: 20px !important;
        border-radius: 8px;
    }

    .stTabs [aria-selected="true"] {
        background: #f8ae28 !important;
        color: #FFFFFF !important;
        border-bottom: 2px solid #f8ae28 !important;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #333333 !important;
        font-size: 19px !important;
        border-radius: 8px !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #f8ae28 !important;
        box-shadow: 0 0 0 2px rgba(248,174,40,0.1) !important;
    }

    .stDataFrame {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        font-size: 19px !important;
    }

    [data-testid="stExpander"] details summary {
        background-color: var(--background-color, #FFFFFF) !important;
        color: var(--text-color, #1E293B) !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }

    [data-testid="stExpander"] details summary:hover,
    [data-testid="stExpander"] details summary:focus,
    [data-testid="stExpander"] details summary:active {
        background-color: #F8FAFC !important;
        outline: none !important;
    }

    [data-testid="stExpander"] details summary p,
    [data-testid="stExpander"] details summary span,
    [data-testid="stExpander"] details summary svg {
        color: #1E293B !important;
        fill: #1E293B !important;
        font-weight: 600 !important;
        font-size: 18px !important;
    }

    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
    }

    hr { border-color: #E2E8F0 !important; }

    .stSpinner > div { border-top-color: #f8ae28 !important; }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #F8FAFC; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

    .stButton > button[kind="secondary"] p,
    .stButton > button[kind="secondary"] span,
    .stButton > button[kind="secondary"] div,
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span,
    .stButton > button[kind="primary"] div {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] img {
        background: transparent !important;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
