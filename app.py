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

# Painel Lateral para definir os valores com segurança (Previne erros de leitura do Sheets)
st.sidebar.header("⚙️ Parâmetros da Banca")
saldo_banca_inicial = st.sidebar.number_input("Banca Inicial (R$):", min_value=0.0, value=200.0, step=10.0)
meta_final = st.sidebar.number_input("Meta Objetivo Final (R$):", min_value=0.0, value=500.0, step=50.0)
meta_diaria = st.sidebar.number_input("Meta Fixa por Dia (R$):", min_value=0.0, value=10.0, step=1.0)

# Inicialização segura da conexão
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_raw = conn.read(worksheet="🎯 Meta Diária", ttl=0)
except Exception as e:
    st.error(f"❌ Erro de conexão com o Google Sheets: {e}")
    st.stop()

# --- DISPOSITIVO DE ISOLAMENTO ANTIFALHAS ---
try:
    # Varredura inteligente para achar a linha da tabela de dados
    linha_cabecalho = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains('Dia').any():
            linha_cabecalho = i
            break
            
    if linha_cabecalho is None:
        st.error("❌ A coluna 'Dia' não foi localizada na planilha. Certifique-se de que a tabela não foi apagada.")
        st.stop()
        
    # Recorta a tabela a partir do cabeçalho encontrado
    df_sheets = df_raw.iloc[linha_cabecalho + 1:].copy()
    df_sheets.columns = df_raw.iloc[linha_cabecalho].tolist()
    df_sheets = df_sheets.reset_index(drop=True)
    
    # Isola estritamente as 3 primeiras colunas vitais (Dia, Saldo Inicial, Rendimento)
    df_sheets = df_sheets.iloc[:, :3]
    df_sheets.columns = ['Dia', 'Saldo_Inicial_Original', 'Rendimento_Original']
    
    # Limpa linhas fantasmas do fim do arquivo
    df_sheets = df_sheets.dropna(subset=['Dia'])
    df_sheets = df_sheets[df_sheets['Dia'].astype(str).str.strip() != '']
    
    # Função ultra robusta de conversão de moeda/texto para número puro
    def limpar_valores_monentarios(val):
        if pd.isna(val) or str(val).strip() == '' or str(val).strip() == 'nan':
            return 0.0
        val_str = str(val).replace('R$', '').replace(' ', '').strip()
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
    st.error(f"❌ Erro no processamento interno dos dados: {e}")
    st.stop()


# --- 📊 PROCESSAMENTO AUTOMÁTICO EM CASCATA ---
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

# Separação dos dias que contêm rendimentos válidos (> 0) para o cálculo do resumo
df_preenchidos = df_final[df_final['Rendimento_Limpo'] > 0]
ultimo_saldo = df_final['Calc_Saldo_Final'].iloc[len(df_preenchidos)-1] if not df_preenchidos.empty else saldo_banca_inicial

# Card de Resumo Visual no Topo
st.markdown(f"""
<div class="banca-card">
    <span style="color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase;">Resumo em Tempo Real (Planilha Conectada)</span>
    <h3 style="margin: 5px 0 10px 0;">🎯 Meta Diária do Plano: R$ {meta_diaria:,.2f}</h3>
    <p style="font-size: 16px; margin: 0;">
        <b>Sua Banca Atual:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final do Ciclo:</b> R$ {meta_final:,.2f}
    </p>
</div>
""", unsafe_allow_html=True)
st.progress(min(max(ultimo_saldo / meta_final, 0.0), 1.0))

tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📊 Tabela Sincronizada", "📈 Evolução Gráfica"])

# --- ABA 1: LANÇAMENTOS ---
with tab1:
    st.subheader("Registrar Rendimento")
    
    lista_dias = df_final['Dia'].astype(str).tolist()
    dia_selecionado = st.selectbox("Selecione o Dia para Atualizar:", lista_dias)
    valor_rendimento = st.number_input("Digite o Rendimento deste dia (R$):", min_value=0.0, step=1.0)
    
    if st.button("🚀 Confirmar e Salvar na Planilha"):
        col_rend_original_nome = df_raw.iloc[linha_cabecalho].tolist()[2]
        idx_planilha = df_raw[df_raw.iloc[:, 0].astype(str) == dia_selecionado].index[0]
        
        # Altera diretamente o valor na planilha original mantendo o layout intacto
        df_raw.at[idx_planilha, col_rend_original_nome] = valor_rendimento
        
        conn.update(worksheet="🎯 Meta Diária", data=df_raw)
        st.success(f"Dados salvos com sucesso no Google Sheets para o dia {dia_selecionado}!")
        st.rerun()

    st.markdown("---")
    st.subheader("Histórico de Ganhos Identificados")
    if not df_preenchidos.empty:
        for idx, row in df_preenchidos.iterrows():
            c1, c2, c3 = st.columns([2, 3, 1])
            with c1: st.markdown(f"📅 **Dia {row['Dia']}**")
            with c2: st.markdown(f"💰 Ganho: **R$ {row['Rendimento_Limpo']:,.2f}**")
            with c3:
                if st.button("🗑️", key=f"del_{idx}"):
                    col_rend_original_nome = df_raw.iloc[linha_cabecalho].tolist()[2]
                    idx_mudar = df_raw[df_raw.iloc[:, 0].astype(str) == str(row['Dia'])].index[0]
                    df_raw.at[idx_mudar, col_rend_original_nome] = 0.0
                    conn.update(worksheet="🎯 Meta Diária", data=df_raw)
                    st.rerun()

# --- ABA 2: TABELA GERAL ---
with tab2:
    st.subheader("Visualização dos Dados Tratados")
    df_visual = pd.DataFrame({
        'Dia': df_final['Dia'],
        'Saldo Inicial (R$)': df_final['Calc_Saldo_Inicial'],
        'Rendimento Registrado': df_final['Rendimento_Limpo'],
        'Meta Acumulada do Dia': df_final['Calc_Meta_Dia'],
        'Saldo Final Real': df_final['Calc_Saldo_Final'],
        'Progresso Geral': df_final['Calc_Progresso'],
        'Meta Batida?': df_final['Calc_Atingida']
    })
    st.dataframe(df_visual, hide_index=True, use_container_width=True)

# --- ABA 3: GRÁFICO ---
with tab3:
    st.subheader("Análise Gráfica Progressiva")
    if not df_preenchidos.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_preenchidos['Dia'], y=df_preenchidos['Calc_Saldo_Final'], name='Seu Saldo Final', marker_color='#10b981'))
        fig.add_trace(go.Bar(x=df_preenchidos['Dia'], y=df_preenchidos['Calc_Meta_Dia'], name='Meta Acumulada', marker_color='#3b82f6'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insira lançamentos para gerar gráficos de evolução.")
