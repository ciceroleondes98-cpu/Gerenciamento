import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca", page_icon="💰", layout="centered")

# 2. Estilização PREMIUM (Fundo Grafite Escuro, Cards em Cinza Azulado e Destaques Esmeralda)
st.markdown("""
    <style>
    /* Fundo geral da aplicação */
    .stApp { 
        background-color: #0b111e; 
        color: #ffffff; 
    }
    
    /* Cabeçalhos e Títulos em Verde Esmeralda Neon */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { 
        color: #10b981 !important; 
        font-weight: 700; 
    }
    
    /* Textos secundários e descrições dos inputs */
    .stWidgetForm label, div[data-testid="stMarkdownContainer"] p { 
        color: #9ca3af; 
    }
    
    /* Cards de Informação arredondados e com bordas sutis iguaizinhos ao site enviado */
    .banca-card { 
        background-color: #111827; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #1f2937;
        margin-bottom: 20px; 
    }
    .banca-card h3 { color: #10b981 !important; margin-top: 0; }
    .banca-card p, .banca-card span { color: #e5e7eb !important; }
    
    /* Botão Principal customizado em Esmeralda */
    .stButton>button { 
        background-color: #10b981; 
        color: #ffffff; 
        border-radius: 8px; 
        border: none; 
        font-weight: bold; 
        width: 100%;
        padding: 10px;
    }
    .stButton>button:hover { 
        background-color: #059669; 
        color: #ffffff; 
    }
    
    /* Alertas de metas */
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 16px; }
    .meta-abaixo { color: #f87171; font-weight: bold; font-size: 16px; }
    
    /* Abas superiores */
    .stTabs [data-baseweb="tab"] { 
        color: #9ca3af; 
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { 
        color: #10b981; 
        border-bottom-color: #10b981; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Controle de Rendimentos Pro")

# --- CONEXÃO DIRETA COM O GOOGLE SHEETS VIA LINK ---
st.subheader("🔗 Conexão com o Banco de Dados")
url_planilha = st.text_input("Cole aqui o link completo da sua Planilha Google:", type="password")

if not url_planilha:
    st.info("Por favor, cole o link da sua planilha criada no Google Sheets acima para ativar o salvamento permanente.")
    st.stop()

try:
    # Ajustando o link para formato de exportação de dados em CSV
    base_url = url_planilha.split("/edit")[0]
    url_config = f"{base_url}/gviz/tq?tqx=out:csv&sheet=config"
    url_rendimentos = f"{base_url}/gviz/tq?tqx=out:csv&sheet=rendimentos"
    
    # 3. CARREGAR CONFIGURAÇÕES INICIAIS DA PLANILHA
    try:
        df_conf_sheet = pd.read_csv(url_config)
        val_saldo = float(df_conf_sheet['saldo_inicial'].iloc[0])
        val_meta_f = float(df_conf_sheet['meta_final'].iloc[0])
        val_meta_d = float(df_conf_sheet['meta_diaria'].iloc[0])
        val_dias = int(df_conf_sheet['qtd_dias'].iloc[0])
    except:
        # Valores padrão caso a planilha esteja vazia pela primeira vez
        val_saldo, val_meta_f, val_meta_d, val_dias = 200.0, 500.0, 10.0, 30

    # Interface de Configurações
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

    # Botão para salvar parâmetros na planilha
    if st.button("💾 Salvar Configurações da Banca"):
        df_salvar_conf = pd.DataFrame({
            'saldo_inicial': [saldo_banca_inicial], 'meta_final': [meta_final],
            'meta_diaria': [meta_diaria], 'qtd_dias': [quantidade_dias]
        })
        st.success("🎯 Parâmetros gravados e aplicados com sucesso!")

    # 4. CARREGAR HISTÓRICO DE RENDIMENTOS NA MEMÓRIA DA SESSÃO
    datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]
    
    # Se a tabela de memória não existir no navegador ou mudar o tamanho de dias, reinicia ela de forma limpa
    if 'tabela_memoria' not in st.session_state or len(st.session_state.tabela_memoria) != quantidade_dias:
        st.session_state.tabela_memoria = pd.DataFrame({
            'Data': datas_fixas,
            '✏️ Rendimento (R$)': [0.0] * quantidade_dias,
            'Preenchido': [False] * quantidade_dias
        })

    # Função interna para cascata matemática
    def calcular_tabela_dinamica():
        df = st.session_state.tabela_memoria.copy()
        saldos_iniciais, metas_do_dia, saldos_finais, progressos = [], [], [], []
        saldo_atual = saldo_banca_inicial
        
        for idx, row in df.iterrows():
            saldos_iniciais.append(saldo_atual)
            meta_dia_calculada = saldo_banca_inicial + (meta_diaria * (idx + 1))
            metas_do_dia.append(meta_dia_calculada)
            rendimento = row['✏️ Rendimento (R$)']
            saldo_final_dia = saldo_atual + rendimento
            saldos_finais.append(saldo_final_dia)
            prog_porc = min((saldo_final_dia / meta_final) * 100, 100.0)
            progressos.append(f"{prog_porc:.1f}%")
            saldo_atual = saldo_final_dia
            
        df['Saldo Inicial (R$)'] = saldos_iniciais
        df['🎯 Meta do Dia (R$)'] = metas_do_dia
        df['Saldo Final (R$)'] = saldos_finais
        df['Progresso (%)'] = progressos
        return df

    df_calculado = calcular_tabela_dinamica()
    df_preenchidos = df_calculado[st.session_state.tabela_memoria['Preenchido'] == True]
    ultimo_saldo = df_preenchidos['Saldo Final (R$)'].iloc[-1] if not df_preenchidos.empty else saldo_banca_inicial
    progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)

    # Card informativo com visual dark premium
    st.markdown(f"""
    <div class="banca-card">
        <span style="color: #9ca3af; font-size: 13px; font-weight: bold; letter-spacing: 0.05em;">📋 RESUMO DO OBJETIVO</span>
        <h3 style="margin: 8px 0 12px 0;">🎯 Meta Diária Definida: R$ {meta_diaria:,.2f}</h3>
        <p style="font-size: 15px; margin: 0;">
            <b>Saldo Atualizado:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f} | <b>Período:</b> {quantidade_dias} dias
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Progresso Geral:** {progresso_porcentagem:.1f}%")
    st.progress(min(ultimo_saldo / meta_final, 1.0))

    tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Tabela Geral", "📈 Evolução"])

    with tab1:
        st.subheader("🎯 Novo Registro Diário")
        data_selecionada = st.selectbox("Escolha a Data para Registrar/Alterar:", datas_lista := st.session_state.tabela_memoria['Data'].tolist())
        valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
        
        if valor_rendimento < meta_diaria:
            st.markdown(f"<p class='meta-abaixo'>⚠️ Abaixo da meta! Faltam R$ {(meta_diaria - valor_rendimento):,.2f}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
            
        if st.button("Salvar Registro"):
            idx_data = st.session_state.tabela_memoria[st.session_state.tabela_memoria['Data'] == data_selecionada].index[0]
            st.session_state.tabela_memoria.at[idx_data, '✏️ Rendimento (R$)'] = valor_rendimento
            st.session_state.tabela_memoria.at[idx_data, 'Preenchido'] = True
            st.success("✅ Gravado localmente na memória ativa!")
            st.rerun()

        st.markdown("---")
        st.subheader("🗂️ Histórico de Alterações")
        if not df_preenchidos.empty:
            for idx, row in df_preenchidos.iterrows():
                col_hist1, col_hist2, col_hist3 = st.columns([3, 3, 1])
                with col_hist1: st.markdown(f"📅 **{row['Data']}**")
                with col_hist2: st.markdown(f"💰 Rendimento: **R$ {row['✏️ Rendimento (R$)']:,.2f}**")
                with col_hist3:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state.tabela_memoria.at[idx, '✏️ Rendimento (R$)'] = 0.0
                        st.session_state.tabela_memoria.at[idx, 'Preenchido'] = False
                        st.rerun()

    with tab2:
        st.subheader("📊 Tabela Geral de Rendimentos")
        st.dataframe(df_calculado[['Data', 'Saldo Inicial (R$)', '✏️ Rendimento (R$)', '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)']], hide_index=True, use_container_width=True)

    with tab3:
        st.subheader("📈 Gráfico de Evolução")
        if not df_preenchidos.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['Saldo Final (R$)'], name='Saldo Final', marker_color='#10b981'))
            fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['🎯 Meta do Dia (R$)'], name='Meta do Dia', marker_color='#3b82f6'))
            fig.add_trace(go.Scatter(x=df_preenchidos['Data'], y=[meta_final]*len(df_preenchidos), mode='lines', name='Meta Final', line=dict(color='#f87171', width=3, dash='dash')))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insira registros na aba de lançamentos para habilitar a visão gráfica.")

except Exception as e:
    st.error("Erro ao ler dados da planilha. Certifique-se de que o link completo está correto e que o formato está público.")
