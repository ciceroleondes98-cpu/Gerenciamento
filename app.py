import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca", page_icon="🪙", layout="centered")

# 2. Estilização baseada no design BETOU (Azul Escuro, Amarelo Ouro e Texto Branco)
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

st.title("🪙 Controle de Rendimentos Pro")

# --- GERENCIAMENTO DE BANCO DE DADOS LOCAL EM CACHE (BLINDADO) ---
if 'saldo_inicial' not in st.session_state:
    st.session_state.saldo_inicial = 200.0
if 'meta_final' not in st.session_state:
    st.session_state.meta_final = 500.0
if 'meta_diaria' not in st.session_state:
    st.session_state.meta_diaria = 10.0
if 'qtd_dias' not in st.session_state:
    st.session_state.qtd_dias = 30

# Interface de Configurações
st.subheader("⚙️ Configuração da Banca e Período")
col_banca1, col_banca2, col_banca3, col_banca4 = st.columns(4)

with col_banca1:
    saldo_banca_inicial = st.number_input("Saldo Inicial (R$):", min_value=0.0, value=st.session_state.saldo_inicial, step=10.0)
with col_banca2:
    meta_final = st.number_input("Meta Final Geral (R$):", min_value=1.0, value=st.session_state.meta_final, step=50.0)
with col_banca3:
    meta_diaria = st.number_input("Meta Diária (R$):", min_value=0.0, value=st.session_state.meta_diaria, step=1.0)
with col_banca4:
    quantidade_dias = st.number_input("Qtd de Dias:", min_value=1, max_value=365, value=st.session_state.qtd_dias, step=1)

if st.button("💾 Salvar Parâmetros Operacionais"):
    st.session_state.saldo_inicial = saldo_banca_inicial
    st.session_state.meta_final = meta_final
    st.session_state.meta_diaria = meta_diaria
    st.session_state.qtd_dias = quantidade_dias
    st.success("✅ Configurações salvas no painel com sucesso!")
    st.rerun()

# 4. HISTÓRICO DE RENDIMENTOS
datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]

if 'tabela_memoria' not in st.session_state or len(st.session_state.tabela_memoria) != quantidade_dias:
    st.session_state.tabela_memoria = pd.DataFrame({
        'Data': datas_fixas,
        '📈 Rendimento (R$)': [0.0] * quantidade_dias,
        'Preenchido': [False] * quantidade_dias
    })

def calcular_tabela_dinamica():
    df = st.session_state.tabela_memoria.copy()
    saldos_iniciais, metas_do_dia, saldos_finais, progressos = [], [], [], []
    saldo_atual = saldo_banca_inicial
    
    for idx, row in df.iterrows():
        saldos_iniciais.append(saldo_atual)
        meta_dia_calculada = saldo_banca_inicial + (meta_diaria * (idx + 1))
        metas_do_dia.append(meta_dia_calculada)
        rendimento = float(row['📈 Rendimento (R$)'])
        saldo_final_dia = saldo_atual + rendimento
        saldos_finais.append(saldo_final_dia)
        prog_porc = min((saldo_final_dia / meta_final) * 100, 100.0)
        progressos.append(f"{prog_porc:.1f}%")
        saldo_atual = saldo_final_dia
        
    df['Saldo Inicial (R$)'] = saldos_iniciais
    df['🏆 Meta do Dia (R$)'] = metas_do_dia
    df['Saldo Final (R$)'] = saldos_finais
    df['Progresso (%)'] = progressos
    return df

df_calculado = calcular_tabela_dinamica()
df_preenchidos = df_calculado[df_calculado['Preenchido'] == True]
ultimo_saldo = df_preenchidos['Saldo Final (R$)'].iloc[-1] if not df_preenchidos.empty else saldo_banca_inicial
progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)

st.markdown(f"""
<div class="banca-card">
    <span style="color: #94a3b8; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">🚀 RESUMO DA OPERAÇÃO</span>
    <h3 style="margin: 8px 0 12px 0;">🎯 Meta Diária: R$ {meta_diaria:,.2f}</h3>
    <p style="font-size: 16px; margin: 0; color: #f1b813;">
        <b>Saldo Atual:</b> R$ {ultimo_saldo:,.2f} <span style="color: #fff;">➔</span> <b>Alvo Final:</b> R$ {meta_final:,.2f} | <b>Período:</b> {quantidade_dias} dias
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**Progresso Geral para o Alvo:** {progresso_porcentagem:.1f}%")
st.progress(min(ultimo_saldo / meta_final, 1.0))

tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📊 Visão Geral", "📈 Gráfico de Evolução"])

with tab1:
    st.subheader("Novo Registro Diário")
    data_selecionada = st.selectbox("Escolha a Data:", df_calculado['Data'].tolist())
    valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
    
    if valor_rendimento < meta_diaria:
        st.markdown("<p class='meta-abaixo'>⚠️ Abaixo da meta!</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
        
    if st.button("Confirmar e Salvar Registro"):
        idx_data = st.session_state.tabela_memoria[st.session_state.tabela_memoria['Data'] == data_selecionada].index[0]
        st.session_state.tabela_memoria.at[idx_data, '📈 Rendimento (R$)'] = valor_rendimento
        st.session_state.tabela_memoria.at[idx_data, 'Preenchido'] = True
        st.success("🔥 Lançamento salvo com sucesso no painel!")
        st.rerun()

    st.markdown("---")
    st.subheader("⏱️ Histórico Recente")
    if not df_preenchidos.empty:
        for idx, row in df_preenchidos.iterrows():
            col_hist1, col_hist2, col_hist3 = st.columns([3, 3, 1])
            with col_hist1: st.markdown(f"📅 **{row['Data']}**")
            with col_hist2: st.markdown(f"💰 Rendimento: <span style='color: #f1b813; font-weight: bold;'>R$ {float(row['📈 Rendimento (R$)']):,.2f}</span>", unsafe_allow_html=True)
            with col_hist3:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.tabela_memoria.at[idx, '📈 Rendimento (R$)'] = 0.0
                    st.session_state.tabela_memoria.at[idx, 'Preenchido'] = False
                    st.rerun()

with tab2:
    st.subheader("📋 Tabela Geral")
    st.dataframe(df_calculado[['Data', 'Saldo Inicial (R$)', '📈 Rendimento (R$)', '🏆 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)']], hide_index=True, use_container_width=True)

with tab3:
    st.subheader("📊 Gráfico de Performance")
    if not df_preenchidos.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['Saldo Final (R$)'], name='Saldo Atual', marker_color='#f1b813'))
        fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['🏆 Meta do Dia (R$)'], name='Meta Esperada', marker_color='#3b82f6'))
        fig.add_trace(go.Scatter(x=df_preenchidos['Data'], y=[meta_final]*len(df_preenchidos), mode='lines', name='Alvo Final', line=dict(color='#ef4444', width=3, dash='dash')))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), barmode='group')
        st.plotly_chart(fig, use_container_width=True)
