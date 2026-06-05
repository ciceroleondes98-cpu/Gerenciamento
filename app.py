import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Gerenciador de Banca", page_icon="🪙", layout="centered")

# ============================================
# VALORES PADRÃO DE SEGURANÇA
# ============================================
val_saldo = 200.0
val_meta_f = 500.0
val_meta_d = 10.0
val_dias = 30

# ============================================
# LEITURA DA ABA 'config' DO GOOGLE SHEETS
# ============================================
@st.cache_data(ttl=300)
def carregar_config_gsheets():
    """Carrega valores da aba 'config' do Google Sheets."""
    try:
        from streamlit_gsheets import GSheetsConnection
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_config = conn.read(worksheet="config", usecols=[0, 1], ttl=300)
        
        # Remove linhas vazias
        df_config = df_config.dropna(how="all")
        
        # Converte para dicionário (coluna 0 = chave, coluna 1 = valor)
        config_dict = dict(zip(
            df_config.iloc[:, 0].astype(str).str.strip().str.lower(),
            df_config.iloc[:, 1]
        ))
        
        return config_dict
    except Exception as e:
        st.warning(f"⚠️ Não foi possível ler a planilha de configuração: {e}")
        return None

# Tenta carregar configurações do Google Sheets
config = carregar_config_gsheets()

if config is not None:
    try:
        val_saldo = float(config.get("saldo_inicial", val_saldo))
        val_meta_f = float(config.get("meta_final", val_meta_f))
        val_meta_d = float(config.get("meta_diaria", val_meta_d))
        val_dias = int(float(config.get("qtd_dias", val_dias)))
    except (ValueError, TypeError) as e:
        st.warning(f"⚠️ Erro ao converter valores da planilha. Usando padrões: {e}")

# ============================================
# INTERFACE PRINCIPAL
# ============================================
st.title("🪙 Controle de Rendimentos Pro")

st.subheader("⚙️ Configuração da Banca e Período")
col1, col2, col3, col4 = st.columns(4)

with col1:
    saldo_banca_inicial = st.number_input(
        "Saldo Inicial (R$):",
        value=val_saldo,
        step=10.0
    )

with col2:
    meta_final = st.number_input(
        "Meta Final Geral (R$):",
        value=val_meta_f,
        step=50.0
    )

with col3:
    meta_diaria = st.number_input(
        "Meta Diária (R$):",
        value=val_meta_d,
        step=1.0
    )

with col4:
    quantidade_dias = st.number_input(
        "Qtd de Dias:",
        value=val_dias,
        step=1
    )

# ============================================
# ESTRUTURA DAS 3 ABAS (INTACTA)
# ============================================
tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📋 Visão Geral", "📊 Gráfico de Evolução"])

with tab1:
    st.subheader("Novo Registro Diário")
    # Conteúdo dos lançamentos...
    st.info("Insira aqui o conteúdo da aba de Lançamentos.")

with tab2:
    st.subheader("📋 Tabela Geral de Acompanhamento")
    # Conteúdo da tabela...
    st.info("Insira aqui o conteúdo da Visão Geral.")

with tab3:
    st.subheader("📊 Gráfico de Performance Operacional")
    # Conteúdo do gráfico...
    st.info("Insira aqui o conteúdo do Gráfico de Evolução.")
