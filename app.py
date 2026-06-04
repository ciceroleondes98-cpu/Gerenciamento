import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca", page_icon="💰", layout="centered")

# 2. Estilização com a nova paleta de cores (Gradiente escuro, textos esmeralda e cards brancos)
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

# 3. Inicialização do Banco de Dados e Variáveis na memória do App
if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=[
        'Data', 'Saldo Inicial (R$)', '✏️ Rendimento (R$)', '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)'
    ])

# --- TELA INICIAL: CONFIGURAÇÃO DINÂMICA ---
st.subheader("Configuração da Banca")

# Ajuste 2: Lado a lado para Saldo Inicial e Meta Final
col_banca1, col_banca2 = st.columns(2)

with col_banca1:
    saldo_banca_inicial = st.number_input("Digite o Saldo Inicial Geral (R$):", min_value=0.0, value=200.0, step=10.0)

with col_banca2:
    meta_final = st.number_input("Digite a Meta Final Geral (R$):", min_value=1.0, value=500.0, step=50.0)

# Cálculo automático baseado no histórico
meta_diaria = 10.0
ultimo_saldo = st.session_state.historico['Saldo Final (R$)'].iloc[-1] if not st.session_state.historico.empty else saldo_banca_inicial
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

# Ajuste 1: Barra de progresso com a porcentagem indicada textualmente acima/ao lado
st.markdown(f"**Progresso Geral:** {progresso_porcentagem:.1f}%")
st.progress(progresso_barra)

# Criando as 3 Abas
tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Tabela Geral", "📈 Evolução"])

# --- ABA 1: REGISTRO ---
with tab1:
    st.subheader("Novo Registro Diário")
    
    data_registro = st.date_input("Data:", datetime.date.today())
    valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
    
    # Indicativo Inteligente
    if valor_rendimento < meta_diaria:
        falta = meta_diaria - valor_rendimento
        st.markdown(f"<p class='meta-abaixo'>⚠️ Abaixo da meta! Faltam R$ {falta:,.2f} para atingir a meta do dia.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
        
    if st.button("Salvar Registro"):
        saldo_inicial_linha = ultimo_saldo
        meta_dia_linha = saldo_inicial_linha + meta_diaria
        saldo_final_linha = saldo_inicial_linha + valor_rendimento
        progresso_linha = min((saldo_final_linha / meta_final) * 100, 100.0)
        
        nova_linha = {
            'Data': data_registro.strftime('%d/%m/%Y'),
            'Saldo Inicial (R$)': saldo_inicial_linha,
            '✏️ Rendimento (R$)': valor_rendimento,
            '🎯 Meta do Dia (R$)': meta_dia_linha,
            'Saldo Final (R$)': saldo_final_linha,
            'Progresso (%)': f"{progresso_linha:.1f}%"
        }
        
        st.session_state.historico = pd.concat([st.session_state.historico, pd.DataFrame([nova_linha])], ignore_index=True)
        st.success("Registrado com sucesso!")
        st.rerun()

    st.markdown("---")
    st.subheader("Histórico de Registros")
    
    # Ajuste 3: Histórico com opção de Excluir usando uma lixeira de forma limpa
    if not st.session_state.historico.empty:
        for idx, row in st.session_state.historico.iterrows():
            col_hist1, col_hist2, col_hist3 = st.columns([3, 3, 1])
            with col_hist1:
                st.markdown(f"📅 **{row['Data']}**")
            with col_hist2:
                st.markdown(f"💰 Rendimento: **R$ {row['✏️ Rendimento (R$)']:,.2f}**")
            with col_hist3:
                # Botão de excluir com identificador único da linha
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.historico = st.session_state.historico.drop(idx).reset_index(drop=True)
                    st.success("Registro removido!")
                    st.rerun()
            st.markdown("<hr style='margin:0 0 10px 0; border-color: #374151;' />", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #9ca3af;'>Nenhum registro feito ainda.</p>", unsafe_allow_html=True)

# --- ABA 2: TABELA GERAL ---
with tab2:
    st.subheader("Tabela de Movimentações Automática")
    if not st.session_state.historico.empty:
        st.dataframe(st.session_state.historico, hide_index=True)
    else:
        st.markdown("<p style='color: #9ca3af;'>Preencha o rendimento na Aba 1 para gerar os dados automáticos.</p>", unsafe_allow_html=True)

# --- ABA 3: EVOLUÇÃO ---
with tab3:
    st.subheader("Gráfico de Evolução da Banca")
    if not st.session_state.historico.empty:
        fig = go.Figure()
        
        # Ajuste Gráfico: Barra do Saldo Final em Verde (#10b981)
        fig.add_trace(go.Bar(
            x=st.session_state.historico['Data'],
            y=st.session_state.historico['Saldo Final (R$)'],
            name='Saldo Final Realizado',
            marker_color='#10b981'
        ))
        
        # Ajuste Gráfico: Barra da Meta do Dia em Azul (#3b82f6)
        fig.add_trace(go.Bar(
            x=st.session_state.historico['Data'],
            y=st.session_state.historico['🎯 Meta do Dia (R$)'],
            name='Meta do Dia',
            marker_color='#3b82f6'
        ))
        
        # Ajuste Gráfico: Linha da Meta Final Dinâmica em Vermelho Suave (#f87171)
        fig.add_trace(go.Scatter(
            x=st.session_state.historico['Data'],
            y=[meta_final] * len(st.session_state.historico),
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
            legend=dict(font=dict(color='#ffffff'))
        )
        
        # Ajustando grades para não quebrar o visual escuro
        fig.update_xaxes(showgrid=True, gridcolor='#374151')
        fig.update_yaxes(showgrid=True, gridcolor='#374151')
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<p style='color: #9ca3af;'>Adicione dados para visualizar o gráfico de evolução.</p>", unsafe_allow_html=True)
