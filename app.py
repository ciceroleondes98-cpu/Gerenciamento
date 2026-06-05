import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca", page_icon="🪙", layout="centered")

# Estilização baseada no design BETOU (Azul Escuro, Amarelo Ouro e Texto Branco)
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
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #d6a10b;
        color: #030f26;
    }
    .meta-atingida {
        color: #10b981;
        font-weight: bold;
        font-size: 18px;
    }
    .meta-abaixo {
        color: #ef4444;
        font-weight: bold;
        font-size: 18px;
    }
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

# Valores padrão de contingência caso a planilha falhe ao carregar
val_saldo, val_meta_f, val_meta_d, val_dias = 200.0, 500.0, 10.0, 30
conexao_ok = False
url_planilha = ""

# 2. Conexão direta via URL obtida do painel de Secrets
try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        url_planilha = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Links de exportação direta em CSV para leitura rápida das abas
        url_config = url_planilha.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=config")
        url_rendimentos = url_planilha.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=rendimentos")
        
        dados_config = pd.read_csv(url_config)
        dados_rendimentos = pd.read_csv(url_rendimentos)
        conexao_ok = True
    else:
        dados_config = pd.DataFrame()
        dados_rendimentos = pd.DataFrame()
except Exception as e:
    dados_config = pd.DataFrame()
    dados_rendimentos = pd.DataFrame()

# Se a planilha foi lida com sucesso, tenta capturar as configurações reais dela
if conexao_ok and not dados_config.empty:
    try:
        if 'saldo_inicial' in dados_config.columns:
            val_saldo = float(dados_config['saldo_inicial'].iloc[0])
        if 'meta_final' in dados_config.columns:
            val_meta_f = float(dados_config['meta_final'].iloc[0])
        if 'meta_diaria' in dados_config.columns:
            val_meta_d = float(dados_config['meta_diaria'].iloc[0])
        if 'qtd_dias' in dados_config.columns:
            val_dias = int(dados_config['qtd_dias'].iloc[0])
    except:
        pass

# Mostra aviso amigável se estiver usando dados locais temporários
if not conexao_ok:
    st.warning("⚠️ Nota: Exibindo dados locais. Para conectar com sua planilha do Google Sheets, configure o link corretamente nas 'Secrets' do Streamlit Cloud.")

# 3. Interface de Configurações Básicas
st.subheader("⚙️ Configuração da Banca e Período")
col_banca1, col_banca2, col_banca3, col_banca4 = st.columns(4)
with col_banca1:
    saldo_banca_inicial = st.number_input("Saldo Inicial (R$):", min_value=0.0, value=val_saldo, step=10.0)
with col_banca2:
    meta_final = st.number_input("Meta Final Geral (R$):", min_value=1.0, value=val_meta_f, step=50.0)
with col_banca3:
    meta_diaria = st.number_input("Meta Diária (R$):", min_value=0.0, value=val_meta_d, step=1.0)
with col_banca4:
    quantidade_dias = st.number_input("Qtd de Dias:", min_value=1, max_value=365, value=val_dias, step=1)

if url_planilha:
    st.markdown(f"[🔗 Abrir Planilha Google Sheets para checagem rápida]({url_planilha})")

# 4. Estruturação e cálculo dinâmico de datas iniciando em 01/06/2026
datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]

# Mapeando os rendimentos gravados da planilha
dict_rendimentos = {}
if conexao_ok and not dados_rendimentos.empty and 'Data' in dados_rendimentos.columns and 'Rendimento' in dados_rendimentos.columns:
    try:
        dados_rendimentos['Data'] = dados_rendimentos['Data'].astype(str).str.strip()
        dados_rendimentos['Rendimento'] = pd.to_numeric(dados_rendimentos['Rendimento'], errors='coerce').fillna(0.0)
        dict_rendimentos = dict(zip(dados_rendimentos['Data'], dados_rendimentos['Rendimento']))
    except:
        pass

# Geração das colunas do DataFrame de cálculo de forma encadeada pura
saldos_iniciais, metas_do_dia, rendimentos_col, saldos_finais, progressos, preenchidos = [], [], [], [], [], []
saldo_atual = saldo_banca_inicial

for idx, data in enumerate(datas_fixas):
    saldos_iniciais.append(saldo_atual)
    metas_do_dia.append(saldo_banca_inicial + (meta_diaria * (idx + 1)))
    
    rend = float(dict_rendimentos.get(data, 0.0))
    rendimentos_col.append(rend)
    
    foi_p = 1 if data in dict_rendimentos else 0
    preenchidos.append(foi_p)
    
    saldo_final_dia = saldo_atual + rend
    saldos_finais.append(saldo_final_dia)
    progressos.append(f"{min((saldo_final_dia / meta_final) * 100, 100.0):.1f}%")
    saldo_atual = saldo_final_dia

df_calculado = pd.DataFrame({
    'Data': datas_fixas,
    'Saldo Inicial (R
