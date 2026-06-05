import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca", page_icon="🪙", layout="centered")

# 2. Estilização baseada no design BETOU (Azul Escuro, Amarelo Ouro e Texto Branco)
st.markdown("""
    <style>
    /* Fundo Geral do App */
    .stApp { 
        background: linear-gradient(180deg, #030f26 0%, #081633 100%); 
        color: #ffffff; 
    }
    
    /* Títulos em Amarelo Ouro Betou */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { 
        color: #f1b813 !important; 
        font-weight: 700; 
    }
    
    /* Labels dos inputs e textos normais */
    .stWidgetForm label, div[data-testid="stMarkdownContainer"] p { 
        color: #e2e8f0; 
    }
    
    /* Cards de Informação (Estilo Menu Lateral da Imagem) */
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
    
    /* Botões em Amarelo com texto Escuro (Igual ao botão Depositar) */
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
    
    /* Feedbacks de Meta */
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #ef4444; font-weight: bold; font-size: 18px; }
    
    /* Estilização das Abas (Tabs) */
    .stTabs [data-baseweb="tab"] { 
        color: #94a3b8; 
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { 
        color: #f1b813; 
        border-bottom-color: #f1b813; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🪙 Controle de Rendimentos Pro")

# --- CONEXÃO DIRETA COM O GOOGLE SHEETS VIA LINK ---
st.subheader("🔗 Conexão com o Banco de Dados")
url_planilha = st.text_input("Cole aqui o link completo da sua Planilha Google:", type="password")

if not url_planilha:
    st.info("Por favor, cole o link da sua planilha criada no Google Sheets acima para ativar o salvamento permanente.")
    st.stop()

try:
    # Ajustando o link para formato de exportação de dados em CSV
    base_url = url_planilha.split("/edit")[0]
    url_config = f"{base_url}/gviz/tq?tqx=out:csv&sheet=config"
    url_rendimentos = f"{base_url}/gviz/tq?tqx=out:csv&sheet=rendimentos"
    
    # 3. CARREGAR CONFIGURAÇÕES INICIAIS DA PLANILHA
    try:
        df_conf_sheet = pd.read_csv(url_config)
        val_saldo = float(df_conf_sheet['saldo_inicial'].iloc[0])
        val_meta_f = float(df_conf_sheet['meta_final'].iloc[0])
        val_meta_d = float(df_conf_sheet['meta_diaria'].iloc[0])
        val_dias = int(df_conf_sheet['qtd_dias'].iloc[0])
    except:
        # Valores padrão caso a planilha esteja vazia pela primeira vez
        val_saldo, val_meta_f, val_meta_d, val_dias = 200.0, 500.0, 10.0, 30

    # Interface de Configurações
    st.subheader("⚙️ Configuração da Banca e Período")
    col_banca1, col_banca2, col_banca3, col_banca4 = st.columns(4)
