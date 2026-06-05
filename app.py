import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da página e interface premium
st.set_page_config(page_title="Gerenciador de Banca Pro", page_icon="💰", layout="centered")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #1f2937 0%, #111827 100%); color: #ffffff; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #10b981 !important; font-weight: 700; }
    .banca-card { background-color: #ffffff; padding: 20px; border-radius: 12px; color: #111827; margin-bottom: 20px; }
    .banca-card h3, .banca-card p, .banca-card span { color: #111827 !important; }
    .stButton>button { background-color: #10b981; color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #059669; color: white; }
    .stTabs [data-baseweb="tab"] { color: #9ca3af; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #10b981; border-bottom-color: #10b981; }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Controle de Rendimentos Conectado")

# CONFIGURAÇÕES DA SUA BANCA (Fixas e Seguras)
saldo_banca_inicial = 200.0
meta_final = 500.0
meta_diaria = 10.0

# Inicialização segura da conexão
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_raw = conn.read(worksheet="🎯 Meta Diária", ttl=0)
except Exception as e:
    st.error(f"❌ Erro crítico de conexão com o Google Sheets: {e}")
    st.stop()

# --- 🛡️ SISTEMA DE CAPTURA E ISOLAMENTO INTEGRAL ---
try:
    # Localização dinâmica do início da tabela (Varredura de Cabeçalho pela palavra 'Dia')
    linha_cabecalho = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains('Dia').any():
            linha_cabecalho = i
            break
            
    if linha_cabecalho is None:
        st.error("❌ Erro de Estrutura: A coluna 'Dia' não foi encontrada na sua planilha.")
        st.stop()
        
    # Isolamento e reconstrução limpa da tabela de dados
    df_sheets = df_raw.iloc[linha_cabecalho + 1:].copy()
    df_sheets.columns = df_raw.iloc[linha_cabecalho].tolist()
    df_sheets = df_sheets.reset_index(drop=True)
    
    # Isola estritamente as 3 primeiras colunas necessárias (Dia, Saldo Inicial, Rendimento)
    df_sheets = df_sheets.iloc[:, :3]
    df_sheets.columns = ['Dia', 'Saldo_Inicial_Original', 'Rendimento_Original']
    
    # Remove qualquer linha fantasmas ou totalmente vazia da planilha
    df_sheets = df_sheets.dropna(subset=['Dia'])
    df_sheets = df_sheets[df_sheets['Dia'].astype(str).str.strip() != '']
    
    # TRATAMENTO DE VALORES MONETÁRIOS (Garante que texto vire número sem quebrar)
    def limpar_valores_monentarios(val):
        if pd.isna(val) or str(val).strip() == '':
            return 0.0
        val_str = str(val).replace('R$', '').strip()
        # Tratamento de pontuações e formatos decimais
        if ',' in val_str and '.' in val_str:
            val_str = val_str.replace('.', '').replace(',', '.')
        elif ',' in val_str:
            val_str = val_str.replace(',', '.')
        
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    df_sheets['Rendimento_Limpo'] = df_sheets['Rendimento_Original'].apply(limpar_valores_monentarios)

except Exception as e:
    st.error(f"❌ Erro ao processar a estrutura das linhas da planilha: {e}")
    st.stop()


# --- 📊 PROCESSAMENTO DA CASCATA DE VALORES ---
def processar_cascata_financeira(df):
    df_calculado = df.copy()
    saldos_iniciais, metas_do_dia, saldos_finais, progressos, metas_atingidas = [], [], [], [], []
    saldo_atual = saldo_banca_inicial
    
    for idx, row in df_calculado.iterrows():
        saldos_iniciais.append(saldo_atual)
        meta_dia_calculada = saldo_banca_inicial + (meta_diaria * (idx + 1))
        metas_do_dia.append(meta_dia_calculada)
        
        rendimento = row['Rendimento_Limpo']
        saldo_final_dia = saldo_atual + rendimento
        saldos_finais.append(saldo_final_dia)
        
        prog_porc = (saldo_final_dia / meta_final) * 100
        progressos.append(f"{prog_porc:.1f}%")
        metas_atingidas.append("✅ SIM" if rendimento >= meta_diaria else "❌ NÃO")
        
        saldo_atual = saldo_final_dia
        
    df_calculado['Calc_Saldo_Inicial'] = saldos_iniciais
    df_calculado['Calc_Meta_Dia'] = metas_do_dia
    df_calculado['Calc_Saldo_Final'] = saldos_finais
    df_calculado['Calc_Progresso'] = progressos
    df_calculado['Calc_Atingida'] = metas_atingidas
    return df_calculado

df_final = processar_cascata_financeira(df_sheets)

# Separação dos dias que contêm rendimentos válidos (> 0)
df_preenchidos = df_final[df_final['Rendimento_Limpo'] > 0]
ultimo_saldo = df_final['Calc_Saldo_Final'].iloc[len(df_preenchidos)-1] if not df_preenchidos.empty else saldo_banca_inicial
progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)

# Card Informativo Superior
st.markdown(f"""
<div class="banca-card">
    <span style="color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase;">Resumo Atualizado (Modo Totalmente Blindado)</span>
    <h3 style="margin: 5px 0 10px 0;">🎯 Meta Diária Progressiva: R$ {meta_diaria:,.2f}</h3>
    <p style="font-size: 16px; margin: 0;">
        <b>Banca Calculada:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f}
    </p>
</div>
""", unsafe_allow_html=True)
st.progress(min(ultimo_saldo / meta_final, 1.0))

tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📊 Tabela Sincronizada", "📈 Evolução Gráfica"])

# --- ABA 1: LANÇAMENTOS ---
with tab1:
    st.subheader("Registrar Rendimento")
    
    lista
