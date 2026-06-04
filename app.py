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
st.subheader("Configuração da Banca")
col_banca1, col_banca2 = st.columns(2)

with col_banca1:
    saldo_banca_inicial = st.number_input("Digite o Saldo Inicial Geral (R$):", min_value=0.0, value=200.0, step=10.0)

with col_banca2:
    meta_final = st.number_input("Digite a Meta Final Geral (R$):", min_value=1.0, value=500.0, step=50.0)

meta_diaria = 10.0

# AJUSTE 3: Criar uma estrutura fixa de 30 dias a partir de 01/06/2026 se não existir na memória
if 'tabela_fixa' not in st.session_state:
    datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(30)]
    st.session_state.tabela_fixa = pd.DataFrame({
        'Data': datas_fixas,
        '✏️ Rendimento (R$)': [0.0] * 30,
        'Preenchido': [False] * 30  # Marcador interno para saber se você já digitou aquele dia
    })

# AJUSTE 1 & 3: Função inteligente para calcular toda a tabela em cascata baseada nos rendimentos salvos
def calcular_tabela_dinamica():
    df = st.session_state.tabela_fixa.copy()
    saldos_iniciais = []
    metas_do_dia = []
    saldos_finais = []
    progressos = []
    
    saldo_atual = saldo_banca_inicial
    
    for idx, row in df.iterrows():
        # O saldo inicial do dia atual é o saldo final do dia anterior (saldo_atual acumulado)
        saldos_iniciais.append(saldo_atual)
        metas_do_dia.append(saldo_atual + meta_diaria)
        
        # Se o usuário preencheu o rendimento, calcula o ganho real. Caso contrário, mantém o saldo.
        rendimento = row['✏️ Rendimento (R$)']
        saldo_final_dia = saldo_atual + rendimento
        saldos_finais.append(saldo_final_dia)
        
        # Progresso baseado na meta final geral
        prog_porc = min((saldo_final_dia / meta_final) * 100, 100.0)
        progressos.append(f"{prog_porc:.1f}%")
        
        # O saldo final deste dia vira o inicial do próximo ciclo
        saldo_atual = saldo_final_dia
        
    df['Saldo Inicial (R$)'] = saldos_iniciais
    df['🎯 Meta do Dia (R$)'] = metas_do_dia
    df['Saldo Final (R$)'] = saldos_finais
    df['Progresso (%)'] = progressos
    return df

# Gerar tabela calculada
df_calculado = calcular_tabela_dinamica()

# Encontrar os dados consolidados do último dia preenchido para exibir no topo
df_preenchidos = df_calculado[st.session_state.tabela_fixa['Preenchido'] == True]
if not df_preenchidos.empty:
    ultimo_saldo = df_preenchidos['Saldo Final (R$)'].iloc[-1]
else:
    ultimo_saldo = saldo_banca_inicial

progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)
progresso_barra = min(ultimo_saldo / meta_final, 1.0)

# Renderização do Card Inicial em Branco com informações automáticas
st.markdown(f"""
<div class="banca-card">
    <span style="color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase;">Resumo do Objetivo</span>
    <h3 style="margin: 5px 0 10px 0;">🎯 Meta Diária: R$ {meta_diaria:,.2f}</h3>
    <p style="font-size: 16px; margin: 0;">
        <b>Saldo Atualizado:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f}
    </p>
</div>
""", unsafe_allow_html=True)

# Barra de progresso com a porcentagem indicada
st.markdown(f"**Progresso Geral:** {progresso_porcentagem:.1f}%")
st.progress(progresso_barra)

# Criando as 3 Abas
tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Tabela Geral", "📈 Evolução"])

# --- ABA 1: REGISTRO ---
with tab1:
    st.subheader("Novo Registro Diário")
    
    # Caixa de seleção com os 30 dias mapeados para ficar fácil de escolher qual preencher
    datas_lista = st.session_state.tabela_fixa['Data'].tolist()
    data_selecionada = st.selectbox("Escolha a Data para Registrar/Alterar:", datas_lista)
    
    valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
    
    # Indicativo Inteligente
    if valor_rendimento < meta_diaria:
        falta = meta_diaria - valor_rendimento
        st.markdown(f"<p class='meta-abaixo'>⚠️ Abaixo da meta! Faltam R$ {falta:,.2f} para atingir a meta do dia.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
        
    if st.button("Salvar Registro"):
        # Atualiza o rendimento na linha correspondente da tabela fixa na memória
        idx_data = st.session_state.tabela_fixa[st.session_state.tabela_fixa['Data'] == data_selecionada].index[0]
        st.session_state.tabela_fixa.at[idx_data, '✏️ Rendimento (R$)'] = valor_rendimento
        st.session_state.tabela_fixa.at[idx_data, 'Preenchido'] = True
        st.success(f"Dados de {data_selecionada} registrados! Tabela recalculada automaticamente.")
        st.rerun()

    st.markdown("---")
    st.subheader("Histórico de Registros Modificados")
    
    # Exibe apenas os dias que você já preencheu de fato, com a lixeira para zerar se quiser
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
                    st.success("Registro resetado!")
                    st.rerun()
            st.markdown("<hr style='margin:0 0 10px 0; border-color: #374151;' />", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #9ca3af;'>Nenhum rendimento lançado ainda.</p>", unsafe_allow_html=True)

# --- ABA 2: TABELA GERAL (ORGANIZADA DE FORMA FIXA) ---
with tab2:
    st.subheader("Tabela de Movimentações Automática (30 Dias)")
    
    # Organizando a ordem das colunas para bater com o solicitado
    colunas_ordenadas = ['Data', 'Saldo Inicial (R$)', '✏️ Rendimento (R$)', '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)']
    st.dataframe(df_calculado[colunas_ordenadas], hide_index=True, use_container_width=True)

# --- ABA 3: EVOLUÇÃO (GRÁFICO AJUSTADO) ---
with tab3:
    st.subheader("Gráfico de Evolução da Banca")
    
    # Exibe o gráfico se houver dados lançados
    if not df_preenchidos.empty:
        fig = go.Figure()
        
        # AJUSTE 2: Barra de Saldo Final Verde, mais fina (bargap/barmode) e com texto dentro
        fig.add_trace(go.Bar(
            x=df_preenchidos['Data'],
            y=df_preenchidos['Saldo Final (R$)'],
            name='Saldo Final Realizado',
            marker_color='#10b981',
            text=df_preenchidos['Saldo Final (R$)'].apply(lambda x: f"R${x:,.0f}"),
            textposition='inside', # Valor dentro da barra
            textfont=dict(size=12, color='white')
        ))
        
        # AJUSTE 2: Barra da Meta do Dia Azul, mais fina e com texto dentro
        fig.add_trace(go.Bar(
            x=df_preenchidos['Data'],
            y=df_preenchidos['🎯 Meta do Dia (R$)'],
            name='Meta do Dia',
            marker_color='#3b82f6',
            text=df_preenchidos['🎯 Meta do Dia (R$)'].apply(lambda x: f"R${x:,.0f}"),
            textposition='inside', # Valor dentro da barra
            textfont=dict(size=12, color='white')
        ))
        
        # Linha da Meta Final Dinâmica em Vermelho Suave
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
            bargap=0.3,       # AJUSTE 2: Deixa as colunas dos grupos mais finas e modernas
            bargroupgap=0.1,  # Ajuste fino entre as duas barras do mesmo dia
            legend=dict(font=dict(color='#ffffff'))
        )
        
        # Customização das grades de fundo do gráfico
        fig.update_xaxes(showgrid=True, gridcolor='#374151')
        fig.update_yaxes(showgrid=True, gridcolor='#374151')
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<p style='color: #9ca3af;'>Insira dados de rendimento para visualizar as barras de evolução.</p>", unsafe_allow_html=True)
