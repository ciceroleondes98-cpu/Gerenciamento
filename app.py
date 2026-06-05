import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import requests

# 1. Configuração da página
st.set_page_config(page_title="Gerenciador de Banca", page_icon="🪙", layout="centered")

# Estilização BETOU
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #030f26 0%, #081633 100%); color: #ffffff; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #f1b813 !important; font-weight: 700; }
    .stWidgetForm label, div[data-testid="stMarkdownContainer"] p { color: #e2e8f0; }
    .banca-card { background-color: #0a1d37; padding: 20px; border-radius: 12px; color: #ffffff; margin-bottom: 20px; border-left: 5px solid #f1b813; }
    .banca-card h3, .banca-card p, .banca-card span { color: #ffffff !important; }
    .stButton>button { background-color: #f1b813; color: #030f26; border-radius: 8px; border: none; font-weight: bold; transition: 0.3s; width: 100%; }
    .stButton>button:hover { background-color: #d6a10b; color: #030f26; }
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #ef4444; font-weight: bold; font-size: 18px; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #f1b813; border-bottom-color: #f1b813; }
    </style>
    """, unsafe_allow_html=True)

st.title("🪙 Controle de Rendimentos Pro")

# 2. Conexão direta via URL dos Secrets antigos
try:
    # Resgata o link direto configurado nos seus secrets
    url_planilha = st.secrets["connections"]["gsheets"]["spreadsheet"]
    
    # Links de exportação para Pandas ler as abas
    url_config = url_planilha.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=config")
    url_rendimentos = url_planilha.replace("/edit?usp=sharing", "/gviz/tq?tqx=out:csv&sheet=rendimentos")
    
    dados_config = pd.read_csv(url_config)
    dados_rendimentos = pd.read_csv(url_rendimentos)
    conexao_ok = True
except Exception as e:
    conexao_ok = False

if not conexao_ok:
    st.error("❌ Erro de conexão. Verifique se o link da sua planilha está cadastrado corretamente na aba Secrets do Streamlit.")
else:
    # Capturando parâmetros da aba 'config'
    if not dados_config.empty and 'saldo_inicial' in dados_config.columns:
        val_saldo = float(dados_config['saldo_inicial'].iloc[0])
        val_meta_f = float(dados_config['meta_final'].iloc[0])
        val_meta_d = float(dados_config['meta_diaria'].iloc[0])
        val_dias = int(dados_config['qtd_dias'].iloc[0])
    else:
        val_saldo, val_meta_f, val_meta_d, val_dias = 250.0, 650.0, 12.0, 33

    # Interface de Configurações
    st.subheader("⚙️ Configuração da Banca e Período")
    col_banca1, col_banca2, col_banca3, col_banca4 = st.columns(4)
    with col_banca1: saldo_banca_inicial = st.number_input("Saldo Inicial (R$):", min_value=0.0, value=val_saldo, step=10.0)
    with col_banca2: meta_final = st.number_input("Meta Final Geral (R$):", min_value=1.0, value=val_meta_f, step=50.0)
    with col_banca3: meta_diaria = st.number_input("Meta Diária (R$):", min_value=0.0, value=val_meta_d, step=1.0)
    with col_banca4: quantidade_dias = st.number_input("Qtd de Dias:", min_value=1, max_value=365, value=val_dias, step=1)

    # Link de suporte para edição manual se necessário
    st.markdown(f"[🔗 Abrir Planilha Google Sheets para checagem rápida]({url_planilha})")

    # Estruturação das datas
    datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]
    
    # Processando aba de rendimentos
    dict_rendimentos = {}
    if not dados_rendimentos.empty and 'Data' in dados_rendimentos.columns and 'Rendimento' in dados_rendimentos.columns:
        dados_rendimentos['Data'] = dados_rendimentos['Data'].astype(str).str.strip()
        dados_rendimentos['Rendimento'] = pd.to_numeric(dados_rendimentos['Rendimento'], errors='coerce').fillna(0.0)
        dict_rendimentos = dict(zip(dados_rendimentos['Data'], dados_rendimentos['Rendimento']))

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
        'Data': datas_fixas, 'Saldo Inicial (R$)': saldos_iniciais, '📈 Rendimento (R$)': rendimentos_col,
        '🏆 Meta do Dia (R$)': metas_do_dia, 'Saldo Final (R$)': saldos_finais, 'Progresso (%)': progressos, 'Preenchido': preenchidos
    })

    df_preenchidos = df_calculado[df_calculado['Preenchido'] == 1]
    ultimo_saldo = df_preenchidos['Saldo Final (R$)'].iloc[-1] if not df_preenchidos.empty else saldo_banca_inicial
    progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)

    # Card Principal
    st.markdown(f"""
    <div class="banca-card">
        <span style="color: #94a3b8; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">🚀 RESUMO DA OPERAÇÃO</span>
        <h3 style="margin: 8px 0 12px 0;">🎯 Meta Diária: R$ {meta_diaria:,.2f}</h3>
        <p style="font-size: 16px; margin: 0; color: #f1b813;"><b>Saldo Atual:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f} | <b>Período:</b> {quantidade_dias} dias</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Progresso Geral para o Alvo:** {progresso_porcentagem:.1f}%")
    st.progress(min(ultimo_saldo / meta_final, 1.0))

    tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📋 Visão Geral", "📈 Gráfico de Evolução"])

    with tab1:
        st.subheader("Novo Registro Diário")
        data_selecionada = st.selectbox("Escolha a Data para lançamento:", df_calculado['Data'].tolist())
        valor_rendimento = st.number_input("Valor do Rendimento do Dia (R$):", min_value=0.0, value=0.0, step=1.0)
        
        if valor_rendimento >= meta_diaria:
            st.markdown("<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='meta-abaixo'>⚠️ Abaixo da meta!</p>", unsafe_allow_html=True)
            
        st.info("💡 Como sua planilha está integrada como Editor público, você pode usar o link acima para lançar direto nela e ver o app atualizar ao dar F5!")

    with tab2:
        st.subheader("📋 Tabela Geral de Acompanhamento")
        st.dataframe(df_calculado[['Data', 'Saldo Inicial (R$)', '📈 Rendimento (R$)', '🏆 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)']], hide_index=True, use_container_width=True)

    with tab3:
        st.subheader("📊 Gráfico de Performance Operacional")
        if not df_preenchidos.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['Saldo Final (R$)'], name='Saldo Atual', marker_color='#f1b813'))
            fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['🏆 Meta do Dia (R$)'], name='Meta Esperada', marker_color='#3b82f6'))
            fig.add_trace(go.Scatter(x=df_preenchidos['Data'], y=[meta_final] * len(df_preenchidos), mode='lines', name='Alvo Final', line=dict(color='#ef4444', width=3, dash='dash')))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), barmode='group')
            st.plotly_chart(fig, use_container_width=True)
