import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuracao da pagina
st.set_page_config(page_title="Gerenciador de Banca", page_icon="🪙", layout="centered")

# 2. Estilizacao BETOU
st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(180deg, #030f26 0%, #081633 100%); 
        color: #ffffff; 
    }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { 
        color: #f1b813 !important; 
        font-weight: 700; 
    }
    .stWidgetForm label, div[data-testid="stMarkdownContainer"] p { 
        color: #e2e8f0; 
    }
    .banca-card { 
        background-color: #0a1d37; 
        padding: 20px; 
        border-radius: 12px; 
        color: #ffffff; 
        margin-bottom: 20px;
        border-left: 5px solid #f1b813;
    }
    .banca-card h3, .banca-card p, .banca-card span { 
        color: #ffffff !important; 
    }
    .stButton>button { 
        background-color: #f1b813; 
        color: #030f26; 
        border-radius: 8px; 
        border: none; 
        font-weight: bold; 
        transition: 0.3s;
    }
    .stButton>button:hover { 
        background-color: #d6a10b; 
        color: #030f26; 
    }
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #ef4444; font-weight: bold; font-size: 18px; }
    .stTabs [data-baseweb="tab"] { 
        color: #94a3b8; 
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { 
        color: #f1b813; 
        border-bottom-color: #f1b813; 
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# CONEXAO COM GOOGLE SHEETS
# ============================================
from streamlit_gsheets import GSheetsConnection

def get_connection():
    """Retorna a conexao com o Google Sheets."""
    return st.connection("gsheets", type=GSheetsConnection)

def carregar_config():
    """Carrega configuracoes da aba 'config'."""
    defaults = {
        "saldo_inicial": 200.0,
        "meta_final": 500.0,
        "meta_diaria": 10.0,
        "qtd_dias": 30
    }
    try:
        conn = get_connection()
        df = conn.read(worksheet="config", usecols=[0, 1], ttl=5)
        df = df.dropna(how="all")
        config_dict = dict(zip(
            df.iloc[:, 0].astype(str).str.strip().str.lower(),
            df.iloc[:, 1]
        ))
        return {
            "saldo_inicial": float(config_dict.get("saldo_inicial", defaults["saldo_inicial"])),
            "meta_final": float(config_dict.get("meta_final", defaults["meta_final"])),
            "meta_diaria": float(config_dict.get("meta_diaria", defaults["meta_diaria"])),
            "qtd_dias": int(float(config_dict.get("qtd_dias", defaults["qtd_dias"])))
        }
    except Exception as e:
        st.warning(f"Erro ao ler config: {e}")
        return defaults

def salvar_config(saldo_inicial, meta_final, meta_diaria, qtd_dias):
    """Salva configuracoes na aba 'config'."""
    try:
        conn = get_connection()
        df_config = pd.DataFrame({
            "parametro": ["saldo_inicial", "meta_final", "meta_diaria", "qtd_dias"],
            "valor": [saldo_inicial, meta_final, meta_diaria, qtd_dias]
        })
        conn.update(worksheet="config", data=df_config)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar config: {e}")
        return False

def carregar_rendimentos():
    """Carrega rendimentos da aba 'rendimentos'."""
    try:
        conn = get_connection()
        df = conn.read(worksheet="rendimentos", ttl=5)
        if df is not None and not df.empty:
            df = df.dropna(how="all")
            return df
        return None
    except Exception as e:
        return None

def salvar_rendimentos(df):
    """Salva rendimentos na aba 'rendimentos'."""
    try:
        conn = get_connection()
        conn.update(worksheet="rendimentos", data=df)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar rendimentos: {e}")
        return False

# ============================================
# CARREGAR DADOS INICIAIS DO GOOGLE SHEETS
# ============================================
config = carregar_config()

if 'config_loaded' not in st.session_state:
    st.session_state.saldo_inicial = config["saldo_inicial"]
    st.session_state.meta_final = config["meta_final"]
    st.session_state.meta_diaria = config["meta_diaria"]
    st.session_state.qtd_dias = config["qtd_dias"]
    st.session_state.config_loaded = True

st.title("🪙 Controle de Rendimentos Pro")

# Interface de Configuracoes
st.subheader("⚙️ Configuracao da Banca e Periodo")
col_banca1, col_banca2, col_banca3, col_banca4 = st.columns(4)

with col_banca1:
    saldo_banca_inicial = st.number_input(
        "Saldo Inicial (R$):",
        min_value=0.0,
        value=st.session_state.saldo_inicial,
        step=10.0
    )
with col_banca2:
    meta_final = st.number_input(
        "Meta Final Geral (R$):",
        min_value=1.0,
        value=st.session_state.meta_final,
        step=50.0
    )
with col_banca3:
    meta_diaria = st.number_input(
        "Meta Diaria (R$):",
        min_value=0.0,
        value=st.session_state.meta_diaria,
        step=1.0
    )
with col_banca4:
    quantidade_dias = st.number_input(
        "Qtd de Dias:",
        min_value=1,
        max_value=365,
        value=st.session_state.qtd_dias,
        step=1
    )

if st.button("💾 Salvar Parametros Operacionais"):
    if salvar_config(saldo_banca_inicial, meta_final, meta_diaria, quantidade_dias):
        st.session_state.saldo_inicial = saldo_banca_inicial
        st.session_state.meta_final = meta_final
        st.session_state.meta_diaria = meta_diaria
        st.session_state.qtd_dias = quantidade_dias
        st.success("Configuracoes salvas na planilha!")
        st.cache_data.clear()
        st.rerun()

# ============================================
# HISTORICO DE RENDIMENTOS
# ============================================
datas_fixas = [
    (datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y')
    for i in range(quantidade_dias)
]

# Carregar ou criar tabela de rendimentos
df_sheets = carregar_rendimentos()

if df_sheets is not None and 'Data' in df_sheets.columns:
    st.session_state.tabela_memoria = df_sheets.copy()
    # Garantir que tem todas as datas
    datas_existentes = st.session_state.tabela_memoria['Data'].tolist()
    for data in datas_fixas:
        if data not in datas_existentes:
            nova_linha = pd.DataFrame({
                'Data': [data],
                'Rendimento': [0.0],
                'Preenchido': [False]
            })
            st.session_state.tabela_memoria = pd.concat(
                [st.session_state.tabela_memoria, nova_linha],
                ignore_index=True
            )
else:
    st.session_state.tabela_memoria = pd.DataFrame({
        'Data': datas_fixas,
        'Rendimento': [0.0] * quantidade_dias,
        'Preenchido': [False] * quantidade_dias
    })
    # Salvar estrutura inicial na planilha
    salvar_rendimentos(st.session_state.tabela_memoria)

def calcular_tabela_dinamica():
    df = st.session_state.tabela_memoria.copy()
    # Filtrar apenas datas do periodo atual
    df = df[df['Data'].isin(datas_fixas)].reset_index(drop=True)
    
    saldos_iniciais = []
    metas_do_dia = []
    saldos_finais = []
    progressos = []
    saldo_atual = saldo_banca_inicial
    
    for idx, row in df.iterrows():
        saldos_iniciais.append(saldo_atual)
        meta_dia_calculada = saldo_banca_inicial + (meta_diaria
