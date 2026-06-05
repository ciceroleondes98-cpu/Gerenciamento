import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca", page_icon="💰", layout="centered")

# 2. Estilização com a paleta de cores (Gradiente escuro, textos esmeralda e cards brancos)
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

# --- LINK DA SUA PLANILHA FIXADO PARA EVITAR ERROS ---
url_planilha = "https://docs.google.com/spreadsheets/d/1TFuTu0izBqCxrEnNEDXsEohmjPFqwEQbA0Jh5kTOAx4/edit"

try:
    # Ajustando o link para puxar os dados brutos da aba "🎯 Meta Diária" em formato CSV
    base_url = url_planilha.split("/edit")[0]
    # Codifica o nome da aba com caracteres especiais para o formato de URL
    url_rendimentos = f"{base_url}/gviz/tq?tqx=out:csv&sheet=%F0%9F%8E%AF%20Meta%20Di%C3%A1ria"
    
    # 3. CARREGAR DADOS DIRETO DA PLANILHA REAL
    # skiprows=6 pula as 6 primeiras linhas de decorações do Sheets e vai direto pro cabeçalho "Dia"
    df_sheet_raw = pd.read_csv(url_rendimentos, skiprows=6).fillna("")
    
    # Limpa linhas fantasmas e pega apenas as 3 primeiras colunas essenciais
    df_sheet_raw = df_sheet_raw[df_sheet_raw['Dia'].astype(str).str.strip() != '']
    df_sheet_raw = df_sheet_raw.iloc[:, :3]
    df_sheet_raw.columns = ['Data', 'Saldo Inicial (R$)', 'Rendimento_Original']

    # Função para limpar pontos, vírgulas e R$ dos valores que vêm da planilha
    def limpar_valores_moeda(val):
        if not val or pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
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

    df_sheet_raw['Rendimento_Limpo'] = df_sheet_raw['Rendimento_Original'].apply(limpar_valores_moeda)

    # Valores base recuperados da estratégia padrão da sua planilha
    saldo_banca_inicial = 200.0
    meta_final = 500.0
    meta_diaria = 10.0
    quantidade_dias = len(df_sheet_raw)

    # Interface de visualização dos parâmetros fixos
    st.subheader("Configuração da Banca Ativa")
    col_banca1, col_banca2, col_banca3, col_banca4 = st.columns(4)
    with col_banca1: st.metric("Saldo Inicial", f"R$ {saldo_banca_inicial:,.2f}")
    with col_banca2: st.metric("Meta Final Geral", f"R$ {meta_final:,.2f}")
    with col_banca3: st.metric("Meta Diária Perseguida", f"R$ {meta_diaria:,.2f}")
    with col_banca4: st.metric("Total de Período", f"{quantidade_dias} Dias")

    # 4. MEMÓRIA DE SESSÃO LOCAL (Sincronizada com o que está escrito no Sheets)
    if 'tabela_memoria' not in st.session_state or st.sidebar.button("🔄 Atualizar Dados do Sheets"):
        # Se o rendimento for maior que zero na planilha, consideramos como "Preenchido"
        preenchidos = [True if x > 0 else False for x in df_sheet_raw['Rendimento_Limpo']]
        st.session_state.tabela_memoria = pd.DataFrame({
            'Data': df_sheet_raw['Data'].astype(str).tolist(),
            '✏️ Rendimento (R$)': df_sheet_raw['Rendimento_Limpo'].tolist(),
            'Preenchido': preenchidos
        })

    # Função interna para gerar o cálculo dinâmico em cascata
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
            
            prog_porc = (saldo_final_dia / meta_final) * 100
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

    # Card informativo de progresso real
    st.markdown(f"""
    <div class="banca-card">
        <span style="color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase;">Resumo do Objetivo</span>
        <h3 style="margin: 5px 0 10px 0;">🎯 Meta Diária Definida: R$ {meta_diaria:,.2f}</h3>
        <p style="font-size: 16px; margin: 0;">
            <b>Saldo Atualizado:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f} | <b>Dias Ativos:</b> {len(df_preenchidos)} de {quantidade_dias}
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"**Progresso Geral:** {progresso_porcentagem:.1f}%")
    st.progress(min(max(ultimo_saldo / meta_final, 0.0), 1.0))

    tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Tabela Geral", "📈 Evolução"])

    with tab1:
        st.subheader("Novo Registro Diário")
        datas_lista = st.session_state.tabela_memoria['Data'].tolist()
        data_selecionada = st.selectbox("Escolha a Data para Registrar/Alterar:", datas_lista)
        valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
        
        if valor_rendimento < meta_diaria:
            st.markdown(f"<p class='meta-abaixo'>⚠️ Abaixo da meta! Faltam R$ {(meta_diaria - valor_rendimento):,.2f}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
            
        if st.button("Salvar Registro Localmente"):
            idx_data = st.session_state.tabela_memoria[st.session_state.tabela_memoria['Data'] == data_selecionada].index[0]
            st.session_state.tabela_memoria.at[idx_data, '✏️ Rendimento (R$)'] = valor_rendimento
            st.session_state.tabela_memoria.at[idx_data, 'Preenchido'] = True
            st.success("Gravado na memória do aplicativo! Note: No modo leitura de link direto, as alterações locais servem para simulação na tela.")
            st.rerun()

        st.markdown("---")
        st.subheader("Histórico de Alterações Locais")
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
        st.subheader("Tabela Geral Sincronizada")
        st.dataframe(df_calculado[['Data', 'Saldo Inicial (R$)', '✏️ Rendimento (R$)', '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)']], hide_index=True, use_container_width=True)

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
            st.info("Os dados preenchidos na planilha aparecerão graficamente aqui.")

except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}. Certifique-se de que a aba se chama '🎯 Meta Diária' e está compartilhada como pública (Qualquer pessoa com o link).")
