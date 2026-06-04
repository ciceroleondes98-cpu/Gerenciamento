import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca", page_icon="💰", layout="centered")

# 2. Estilização com a paleta de cores (Gradiente escuro, textos esmeralda e cards brancos)
st.markdown("""
    <style>
    /* Fundo da página com gradiente escuro moderno */
    .stApp {
        background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
        color: #ffffff;
    }
    
    /* Títulos em verde esmeralda */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #10b981 !important;
        font-weight: 700;
    }
    
    /* Labels secundários em cinza médio */
    .stWidgetForm label, div[data-testid="stMarkdownContainer"] p {
        color: #e5e7eb;
    }
    small, .secondary-label {
        color: #6b7280;
    }
    
    /* Estilização dos Cards em Branco */
    .banca-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: #111827;
        margin-bottom: 20px;
    }
    .banca-card h3, .banca-card p, .banca-card span {
        color: #111827 !important;
    }
    
    /* Botões personalizados */
    .stButton>button {
        background-color: #10b981;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #059669;
        color: white;
    }
    
    /* Cores do Indicativo Inteligente */
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #f87171; font-weight: bold; font-size: 18px; }
    
    /* Abas customizadas */
    .stTabs [data-baseweb="tab"] {
        color: #9ca3af;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #10b981;
        border-bottom-color: #10b981;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Controle de Rendimentos")

# --- PARAMETRIZAÇÃO DA BANCA INICIAL ---
st.subheader("Configuração da Banca e Período")
col_banca1, col_banca2, col_banca3 = st.columns(3)

with col_banca1:
    saldo_banca_inicial = st.number_input("Saldo Inicial Geral (R$):", min_value=0.0, value=200.0, step=10.0)

with col_banca2:
    meta_final = st.number_input("Meta Final Geral (R$):", min_value=1.0, value=500.0, step=50.0)

# NOVO CAMPO: Quantidade de dias totalmente dinâmica
with col_banca3:
    quantidade_dias = st.number_input("Quantidade de Dias:", min_value=1, max_value=365, value=30, step=1)

meta_diaria = 10.0

# Inicializar ou reajustar a estrutura de dados baseada na quantidade de dias escolhida
if 'tabela_fixa' not in st.session_state or len(st.session_state.tabela_fixa) != quantidade_dias:
    datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]
    st.session_state.tabela_fixa = pd.DataFrame({
        'Data': datas_fixas,
        '✏️ Rendimento (R$)': [0.0] * quantidade_dias,
        'Preenchido': [False] * quantidade_dias
    })
else:
    # Caso os dias continuem os mesmos, garante que as datas estejam certas (útil se mudar algo)
    datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]
    st.session_state.tabela_fixa['Data'] = datas_fixas

# Função para calcular toda a tabela em cascata baseada nos rendimentos salvos
def calcular_tabela_dinamica():
    df = st.session_state.tabela_fixa.copy()
    saldos_iniciais = []
    metas_do_dia = []
    saldos_finais = []
    progressos = []
    
    saldo_atual = saldo_banca_inicial
    
    for idx, row in df.iterrows():
        # O saldo inicial do dia atual é o saldo final do dia anterior
        saldos_iniciais.append(saldo_atual)
        
        # Meta do dia calculada em progressão acumulada perfeita
        meta_dia_calculada = saldo_banca_inicial + (meta_diaria * (idx + 1))
        metas_do_dia.append(meta_dia_calculada)
        
        # Se o usuário preencheu o rendimento, acumula. Senão, mantém estável.
        rendimento = row['✏️ Rendimento (R$)']
        saldo_final_dia = saldo_atual + rendimento
        saldos_finais.append(saldo_final_dia)
        
        # Progresso baseado na meta final geral
        prog_porc = min((saldo_final_dia / meta_final) * 100, 100.0)
        progressos.append(f"{prog_porc:.1f}%")
        
        # Atualiza a variável de controle para a próxima linha
        saldo_atual = saldo_final_dia
        
    df['Saldo Inicial (R$)'] = saldos_iniciais
    df['🎯 Meta do Dia (R$)'] = metas_do_dia
    df['Saldo Final (R$)'] = saldos_finais
    df['Progresso (%)'] = progressos
    return df

# Gerar tabela calculada em tempo de execução
df_calculado = calcular_tabela_dinamica()

# Buscar dados do último dia preenchido para o card informativo do topo
df_preenchidos = df_calculado[st.session_state.tabela_fixa['Preenchido'] == True]
if not df_preenchidos.empty:
    ultimo_saldo = df_preenchidos['Saldo Final (R$)'].iloc[-1]
else:
    ultimo_saldo = saldo_banca_inicial

progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)
progresso_barra = min(ultimo_saldo / meta_final, 1.0)

# Card informativo
st.markdown(f"""
<div class="banca-card">
    <span style="color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase;">Resumo do Objetivo</span>
    <h3 style="margin: 5px 0 10px 0;">🎯 Meta Diária: R$ {meta_diaria:,.2f} (Acumulativa)</h3>
    <p style="font-size: 16px; margin: 0;">
        <b>Saldo Atualizado:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f} | <b>Período:</b> {quantidade_dias} dias
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**Progresso Geral:** {progresso_porcentagem:.1f}%")
st.progress(progresso_barra)

# Criando as 3 Abas
tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Tabela Geral", "📈 Evolução"])

# --- ABA 1: REGISTRO ---
with tab1:
    st.subheader("Novo Registro Diário")
    
    datas_lista = st.session_state.tabela_fixa['Data'].tolist()
    data_selecionada = st.selectbox("Escolha a Data para Registrar/Alterar:", datas_lista)
    
    valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
    
    if valor_rendimento < meta_diaria:
        falta = meta_diaria - valor_rendimento
        st.markdown(f"<p class='meta-abaixo'>⚠️ Abaixo da meta! Faltam R$ {falta:,.2f} para atingir o objetivo mínimo do dia.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
        
    if st.button("Salvar Registro"):
        idx_data = st.session_state.tabela_fixa[st.session_state.tabela_fixa['Data'] == data_selecionada].index[0]
        st.session_state.tabela_fixa.at[idx_data, '✏️ Rendimento (R$)'] = valor_rendimento
        st.session_state.tabela_fixa.at[idx_data, 'Preenchido'] = True
        st.success(f"Dados de {data_selecionada} gravados com sucesso!")
        st.rerun()

    st.markdown("---")
    st.subheader("Histórico de Registros Modificados")
    
    if not df_preenchidos.empty:
        for idx, row in df_preenchidos.iterrows():
            col_hist1, col_hist2, col_hist3 = st.columns([3, 3, 1])
            with col_hist1:
                st.markdown(f"📅 **{row['Data']}**")
            with col_hist2:
                st.markdown(f"💰 Rendimento: **R$ {row['✏️ Rendimento (R$)']:,.2f}**")
            with col_hist3:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.tabela_fixa.at[idx, '✏️ Rendimento (R$)'] = 0.0
                    st.session_state.tabela_fixa.at[idx, 'Preenchido'] = False
                    st.success("Registro limpo!")
                    st.rerun()
            st.markdown("<hr style='margin:0 0 10px 0; border-color: #374151;' />", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #9ca3af;'>Nenhum rendimento lançado ainda.</p>", unsafe_allow_html=True)

# --- ABA 2: TABELA GERAL (ORGANIZADA DE FORMA FIXA DINÂMICA) ---
with tab2:
    st.subheader(f"Tabela de Movimentações Automática ({quantidade_dias} Dias)")
    colunas_ordenadas = ['Data', 'Saldo Inicial (R$)', '✏️ Rendimento (R$)', '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)']
    st.dataframe(df_calculado[colunas_ordenadas], hide_index=True, use_container_width=True)

# --- ABA 3: EVOLUÇÃO ---
with tab3:
    st.subheader("Gráfico de Evolução da Banca")
    if not df_preenchidos.empty:
        fig = go.Figure()
        
        # Barra de Saldo Final Verde com texto interno
        fig.add_trace(go.Bar(
            x=df_preenchidos['Data'],
            y=df_preenchidos['Saldo Final (R$)'],
            name='Saldo Final Realizado',
            marker_color='#10b981',
            text=df_preenchidos['Saldo Final (R$)'].apply(lambda x: f"R${x:,.0f}"),
            textposition='inside',
            textfont=dict(size=11, color='white')
        ))
        
        # Barra da Meta do Dia Azul com texto interno
        fig.add_trace(go.Bar(
            x=df_preenchidos['Data'],
            y=df_preenchidos['🎯 Meta do Dia (R$)'],
            name='Meta do Dia Cumulativa',
            marker_color='#3b82f6',
            text=df_preenchidos['🎯 Meta do Dia (R$)'].apply(lambda x: f"R${x:,.0f}"),
            textposition='inside',
            textfont=dict(size=11, color='white')
        ))
        
        # Linha da Meta Final Dinâmica
        fig.add_trace(go.Scatter(
            x=df_preenchidos['Data'],
            y=[meta_final] * len(df_preenchidos),
            mode='lines',
            name='Meta Final Definida',
            line=dict(color='#f87171', width=3, dash='dash')
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            xaxis_title="Dias",
            yaxis_title="Valores (R$)",
            barmode='group',
            bargap=0.3,
            bargroupgap=0.08,
            legend=dict(font=dict(color='#ffffff'))
        )
        
        fig.update_xaxes(showgrid=True, gridcolor='#374151')
        fig.update_yaxes(showgrid=True, gridcolor='#374151')
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<p style='color: #9ca3af;'>Insira dados de rendimento para visualizar as barras de evolução.</p>", unsafe_allow_html=True)
