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

# 2. Leitura dos Secrets e Planilha
try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        url_planilha = st.secrets["connections"]["gsheets"]["spreadsheet"]
        url_config = url_planilha.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=config")
        url_rendimentos = url_planilha.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=rendimentos")
        
        dados_config = pd.read_csv(url_config)
        dados_rendimentos = pd.read_csv(url_rendimentos)
        
        if not dados_config.empty:
            val_saldo = float(dados_config['saldo_inicial'].iloc[0])
            val_meta_f = float(dados_config['meta_final'].iloc[0])
            val_meta_d = float(dados_config['meta_diaria'].iloc[0])
            val_dias = int(dados_config['qtd_dias'].iloc[0])
except Exception as e:
    st.error(f"Erro ao carregar dados da planilha: {e}")

# 3. Inputs na tela (buscando os valores direto da aba 'config' da sua planilha)
st.subheader("⚙️ Configuração da Banca e Período")
col1, col2, col3, col4 = st.columns(4)
with col1: saldo_banca_inicial = st.number_input("Saldo Inicial (R$):", value=val_saldo, step=10.0)
with col2: meta_final = st.number_input("Meta Final Geral (R$):", value=val_meta_f, step=50.0)
with col3: meta_diaria = st.number_input("Meta Diária (R$):", value=val_meta_d, step=1.0)
with col4: quantidade_dias = st.number_input("Qtd de Dias:", value=val_dias,
