import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca Pro", page_icon="💰", layout="centered")

# 2. Estilização visual premium
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #1f2937 0%, #111827 100%); color: #ffffff; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #10b981 !important; font-weight: 700; }
    .stWidgetForm label, div[data-testid="stMarkdownContainer"] p { color: #e5e7eb; }
    .banca-card { background-color: #ffffff; padding: 20px; border-radius: 12px; color: #111827; margin-bottom: 20px; }
    .banca-card h3, .banca-card p, .banca-card span { color: #111827 !important; }
    .stButton>button { background-color: #10b981; color: white; border-radius: 8px; border: none; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #059669; color: white; }
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #f87171; font-weight: bold; font-size: 18px; }
    .stTabs [data-baseweb="tab"] { color: #9ca3af; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #10b981; border-bottom-color: #10b981; }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Controle de Rendimentos Pro")

# --- CONEXÃO COM O GOOGLE SHEETS ---
try:
    # Cria a conexão utilizando o segredo configurado no Streamlit (.streamlit/secrets.toml)
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Carrega as configurações (Aba: config)
    df_conf = conn.read(worksheet="config", ttl=0)
    val_saldo = float(df_conf['saldo_inicial'].iloc[0])
    val_meta_f = float(df_conf['meta_final'].iloc[0])
    val_meta_d = float(df_conf['meta_diaria'].iloc[0])
    val_dias = int(df_conf['qtd_dias'].iloc[0])
    
    # Carrega os rendimentos históricos (Aba: rendimentos)
    df_rend_sheets = conn.read(worksheet="rendimentos", ttl=0)
    df_rend_sheets['Rendimento'] = pd.to_numeric(df_rend_sheets['Rendimento'], errors='coerce').fillna(0.0)
except Exception as e:
    # Valores padrão de segurança caso a planilha ainda esteja sem dados ou desconectada
    val_saldo, val_meta_f, val_meta_d, val_dias = 200.0, 500.0, 10.0, 30
    df_rend_sheets = pd.DataFrame(columns=['Data', 'Rendimento', 'Preenchido'])

# Interface de Configurações na Tela
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

# Botão para salvar parâmetros de configuração diretamente no Sheets
if st.button("💾 Salvar Parâmetros da Banca"):
    df_salvar_conf = pd.DataFrame({
        'saldo_inicial': [saldo_banca_inicial],
        'meta_final': [meta_final],
        'meta_diaria': [meta_diaria],
        'qtd_dias': [quantidade_dias]
    })
    conn.update(worksheet="config", data=df_salvar_conf)
    st.success("Configurações da banca atualizadas no Google Sheets!")
    st.rerun()

# --- ESTRUTURAÇÃO DO BANCO DE MEMÓRIA ---
datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]

# Se a planilha veio vazia, monta a estrutura inicial de dias
if df_rend_sheets.empty or len(df_rend_sheets) != quantidade_dias:
    df_base = pd.DataFrame({
        'Data': datas_fixas,
        'Rendimento': [0.0] * quantidade_dias,
        'Preenchido': ['Não'] * quantidade_dias
    })
    # Sincroniza os dias gerados para o Sheets na primeira execução
    if df_rend_sheets.empty:
        conn.update(worksheet="rendimentos", data=df_base)
    df_rend_sheets = df_base.copy()

# Sincroniza a tabela carregada com o estado de sessão do Streamlit
st.session_state.tabela_memoria = df_rend_sheets.copy()

# --- LÓGICA DE CÁLCULO EM CASCATA ---
def calcular_tabela_dinamica():
    df = st.session_state.tabela_memoria.copy()
    saldos_iniciais, metas_do_dia, saldos_finais, progressos = [], [], [], []
    saldo_atual = saldo_banca_inicial
    
    for idx, row in df.iterrows():
        saldos_iniciais.append(saldo_atual)
        meta_dia_calculada = saldo_banca_inicial + (meta_diaria * (idx + 1))
        metas_do_dia.append(meta_dia_calculada)
        
        rendimento = float(row['Rendimento'])
        saldo_final_dia = saldo_atual + rendimento
        saldos_finais.append(saldo_final_dia)
        
        prog_porc = (saldo_final_dia / meta_final) * 100
        progressos.append(f"{prog_porc:.1f}%")
        saldo_atual = saldo_final_dia
        
    df['Saldo Inicial (R$)'] = saldos_iniciais
    df['🎯 Meta do Dia (R$)'] = metas_do_dia
    df['Saldo Final (R$)'] = saldos_finais
    df['Progresso (%)'] = progressos
    return df

df_calculado = calcular_tabela_dinamica()
df_preenchidos = df_calculado[df_calculado['Preenchido'] == 'Sim']
ultimo_saldo = df_preenchidos['Saldo Final (R$)'].iloc[-1] if not df_preenchidos.empty else saldo_banca_inicial
progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)

# Card informativo superior
st.markdown(f"""
<div class="banca-card">
    <span style="color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase;">Resumo do Objetivo</span>
    <h3 style="margin: 5px 0 10px 0;">🎯 Meta Diária Definida: R$ {meta_diaria:,.2f}</h3>
    <p style="font-size: 16px; margin: 0;">
        <b>Saldo Atualizado:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f} | <b>Período:</b> {quantidade_dias} dias
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown(f"**Progresso Geral:** {progresso_porcentagem:.1f}%")
st.progress(min(max(ultimo_saldo / meta_final, 0.0), 1.0))

tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Tabela Geral", "📈 Evolução"])

# --- TAB 1: REGISTROS ---
with tab1:
    st.subheader("Novo Registro Diário")
    lista_datas = st.session_state.tabela_memoria['Data'].tolist()
    data_selecionada = st.selectbox("Escolha a Data para Registrar/Alterar:", lista_datas)
    valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
    
    if valor_rendimento < meta_diaria:
        st.markdown(f"<p class='meta-abaixo'>⚠️ Abaixo da meta! Faltam R$ {(meta_diaria - valor_rendimento):,.2f}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
        
    if st.button("🚀 Salvar Registro na Planilha"):
        idx_data = st.session_state.tabela_memoria[st.session_state.tabela_memoria['Data'] == data_selecionada].index[0]
        st.session_state.tabela_memoria.at[idx_data, 'Rendimento'] = valor_rendimento
        st.session_state.tabela_memoria.at[idx_data, 'Preenchido'] = 'Sim'
        
        # Envia a tabela atualizada de volta para o Google Sheets
        conn.update(worksheet="rendimentos", data=st.session_state.tabela_memoria)
        st.success("Dados salvos e sincronizados com sucesso no Google Sheets!")
        st.rerun()

    st.markdown("---")
    st.subheader("Histórico de Alterações")
    if not df_preenchidos.empty:
        for idx, row in df_preenchidos.iterrows():
            col_hist1, col_hist2, col_hist3 = st.columns([3, 3, 1])
            with col_hist1: st.markdown(f"📅 **{row['Data']}**")
            with col_hist2: st.markdown(f"💰 Rendimento: **R$ {float(row['Rendimento']):,.2f}**")
            with col_hist3:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.tabela_memoria.at[idx, 'Rendimento'] = 0.0
                    st.session_state.tabela_memoria.at[idx, 'Preenchido'] = 'Não'
                    conn.update(worksheet="rendimentos", data=st.session_state.tabela_memoria)
                    st.rerun()

# --- TAB 2: TABELA GERAL ---
with tab2:
    st.subheader("Tabela Geral")
    st.dataframe(df_calculado[['Data', 'Saldo Inicial (R$)', 'Rendimento', '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)']], hide_index=True, use_container_width=True)

# --- TAB 3: GRÁFICO ---
with tab3:
    st.subheader("Gráfico de Evolução")
    if not df_preenchidos.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['Saldo Final (R$)'], name='Saldo Final', marker_color='#10b981'))
        fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['🎯 Meta do Dia (R$)'], name='Meta do Dia', marker_color='#3b82f6'))
        fig.add_trace(go.Scatter(x=df_preenchidos['Data'], y=[meta_final]*len(df_preenchidos), mode='lines', name='Meta Final', line=dict(color='#f87171', width=3, dash='dash')))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insira lançamentos para visualizar o gráfico de evolução.")
