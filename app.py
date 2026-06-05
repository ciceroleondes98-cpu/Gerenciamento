import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página e identidade visual
st.set_page_config(page_title="Gerenciador de Banca", page_icon="🪙", layout="centered")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #030f26 0%, #081633 100%); color: #ffffff; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #f1b813 !important; font-weight: 700; }
    .stWidgetForm label, div[data-testid="stMarkdownContainer"] p { color: #e2e8f0; }
    .banca-card { background-color: #0a1d37; padding: 20px; border-radius: 12px; color: #ffffff; margin-bottom: 20px; border-left: 5px solid #f1b813; }
    .banca-card h3, .banca-card p, .banca-card span { color: #ffffff !important; }
    .stButton>button { background-color: #f1b813; color: #030f26; border-radius: 8px; border: none; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #d6a10b; color: #030f26; }
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #ef4444; font-weight: bold; font-size: 18px; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #f1b813; border-bottom-color: #f1b813; }
    </style>
    """, unsafe_allow_html=True)

st.title("🪙 Controle de Rendimentos Pro")

# Valores padrão de segurança
val_saldo, val_meta_f, val_meta_d, val_dias = 200.0, 500.0, 10.0, 30
dados_rendimentos = pd.DataFrame()
url_planilha = ""

# 2. Leitura segura dos Secrets e tabelas do Google Sheets
try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        url_planilha = st.secrets["connections"]["gsheets"]["spreadsheet"]
        url_config = url_planilha.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=config")
        url_rendimentos = url_planilha.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=rendimentos")
        
        dados_config = pd.read_csv(url_config)
        dados_rendimentos = pd.read_csv(url_rendimentos)
        
        if not
