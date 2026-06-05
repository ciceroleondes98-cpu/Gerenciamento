import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# 1. Configuração da página
st.set_page_config(page_title="Gerenciador de Banca Pro", page_icon="💰", layout="centered")

# Estilização visual (Fundo escuro, cards brancos)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #1f2937 0%, #111827 100%); color: #ffffff; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #10b981 !important; font-weight: 700; }
    .banca-card { background-color: #ffffff; padding: 20px; border-radius: 12px; color: #111827; margin-bottom: 20px; }
    .banca-card h3, .banca-card p, .banca-card span { color: #111827 !important; }
    .stButton>button { background-color: #10b981; color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #f87171; font-weight: bold; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Controle de Rendimentos Pro")

# --- CONEXÃO INTELIGENTE COM O GOOGLE SHEETS ---
st.subheader("🔗 Vinculação do Banco de Dados")
url_planilha = st.text_input("Cole o link de compartilhamento da sua Planilha Google:", type="password")

if not url_planilha:
    st.info("Aguardando o link da planilha para ativar o salvamento automático...")
    st.stop()

# Trata a URL para o formato de leitura do pandas
try:
    base_url = url_planilha.split("/edit")[0]
    url_config = f"{base_url}/gviz/tq?tqx=out:csv&sheet=config"
    url_rendimentos = f"{base_url}/gviz/tq?tqx=out:csv&sheet=rendimentos"
    
    # Tenta ler as configurações. Se estiver vazia, usa os valores padrão automaticamente
    try:
        df_conf = pd.read_csv(url_config)
        if not df_conf.empty and 'saldo_inicial' in df_conf.columns:
            val_saldo = float(df_conf['saldo_inicial'].iloc[0])
            val_meta_f = float(df_conf['meta_final'].iloc[0])
            val_meta_d = float(df_conf['meta_diaria'].iloc[0])
            val_dias = int(df_conf['qtd_dias'].iloc[0])
        else:
            raise ValueError
    except:
        # Valores padrão caso a planilha esteja zerada
        val_saldo, val_meta_f, val_meta_d, val_dias = 200.0, 500.0, 10.0, 30

    # --- REFEITO AUTOMATICAMENTE ---
    st.subheader("Configuração da Banca")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        saldo_banca_inicial = st.number_input("Saldo Inicial (R$):", min_value=0.0, value=val_saldo, step=10.0)
    with col2:
        meta_final = st.number_input("Meta Final Geral (R$):", min_value=1.0, value=val_meta_f, step=50.0)
    with col3:
        meta_diaria = st.number_input("Meta Diária (R$):", min_value=0.0, value=val_meta_d, step=1.0)
    with col4:
        quantidade_dias = st.number_input("Qtd de Dias:", min_value=1, max_value=365, value=val_dias, step=1)

    # Cria as datas automáticas baseadas na quantidade de dias informada
    datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]

    # Tenta ler a aba de rendimentos do Sheets, se estiver limpa, cria a estrutura na memória
    if 'tabela_memoria' not in st.session_state:
        try:
            df_rend_sheet = pd.read_csv(url_rendimentos)
            if not df_rend_sheet.empty and 'Data' in df_rend_sheet.columns:
                # Sincroniza o que já tem na planilha com o app
                st.session_state.tabela_memoria = df_rend_sheet
            else:
                raise ValueError
        except:
            # Estrutura inicial automática se a planilha estiver limpa
            st.session_state.tabela_memoria = pd.DataFrame({
                'Data': datas_fixas,
                '✏️ Rendimento (R$)': [0.0] * quantidade_dias,
                'Preenchido': [False] * quantidade_dias
            })

    # Força ajuste caso o usuário mude a quantidade de dias no botão
    if len(st.session_state.tabela_memoria) != quantidade_dias:
        st.session_state.tabela_memoria = pd.DataFrame({
            'Data': datas_fixas,
            '✏️ Rendimento (R$)': [0.0] * quantidade_dias,
            'Preenchido': [False] * quantidade_dias
        })

    # Função que faz o cálculo em cascata dos saldos
    def calcular_tabela_dinamica():
        df = st.session_state.tabela_memoria.copy()
        saldos_iniciais, metas_do_dia, saldos_finais, progressos = [], [], [], []
        saldo_atual = saldo_banca_inicial
        
        for idx, row in df.iterrows():
            saldos_iniciais.append(saldo_atual)
            meta_dia_calculada = saldo_banca_inicial + (meta_diaria * (idx + 1))
            metas_do_dia.append(meta_dia_calculada)
            
            rendimento = float(row['✏️ Rendimento (R$)'])
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
    df_preenchidos = df_calculado[df_calculado['Preenchido'] == True]
    ultimo_saldo = df_preenchidos['Saldo Final (R$)'].iloc[-1] if not df_preenchidos.empty else saldo_banca_inicial
    progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)

    # Card informativo superior
    st.markdown(f"""
    <div class="banca-card">
        <span style="color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase;">Resumo do Objetivo</span>
        <h3 style="margin: 5px 0 10px 0;">🎯 Meta Diária Acumulativa: R$ {meta_diaria:,.2f}</h3>
        <p style="font-size: 16px; margin: 0;">
            <b>Saldo Atual:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f} | <b>Dias:</b> {quantidade_dias}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(min(ultimo_saldo / meta_final, 1.0))

    tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📊 Tabela Geral", "📈 Gráfico"])

    with tab1:
        st.subheader("Registrar Rendimento")
        data_selecionada = st.selectbox("Escolha o Dia:", st.session_state.tabela_memoria['Data'].tolist())
        valor_rendimento = st.number_input("Rendimento do Dia (R$):", min_value=0.0, value=0.0, step=1.0)
        
        if valor_rendimento < meta_diaria:
            st.markdown(f"<p class='meta-abaixo'>⚠️ Faltam R$ {(meta_diaria - valor_rendimento):,.2f} para a meta individual deste dia.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='meta-atingida'>✅ Meta do dia batida!</p>", unsafe_allow_html=True)
            
        if st.button("Confirmar e Salvar Dados"):
            idx_data = st.session_state.tabela_memoria[st.session_state.tabela_memoria['Data'] == data_selecionada].index[0]
            st.session_state.tabela_memoria.at[idx_data, '✏️ Rendimento (R$)'] = valor_rendimento
            st.session_state.tabela_memoria.at[idx_data, 'Preenchido'] = True
            st.success("Registrado! Os dados estão salvos na sessão do seu navegador.")
            st.rerun()

        st.markdown("---")
        st.subheader("Histórico Recente")
        if not df_preenchidos.empty:
            for idx, row in df_preenchidos.iterrows():
                c1, c2, c3 = st.columns([3, 3, 1])
                with c1: st.markdown(f"📅 **{row['Data']}**")
                with c2: st.markdown(f"💰 Ganho: **R$ {row['✏️ Rendimento (R$)']:,.2f}**")
                with c3:
                    if st.button("🗑️", key=f"del_{idx}"):
                        st.session_state.tabela_memoria.at[idx, '✏️ Rendimento (R$)'] = 0.0
                        st.session_state.tabela_memoria.at[idx, 'Preenchido'] = False
                        st.rerun()

    with tab2:
        st.subheader("Movimentações Completas")
        st.dataframe(df_calculado[['Data', 'Saldo Inicial (R$)', '✏️ Rendimento (R$)', '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)']], hide_index=True, use_container_width=True)

    with tab3:
        st.subheader("Evolução Visual")
        if not df_preenchidos.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['Saldo Final (R$)'], name='Seu Saldo', marker_color='#10b981'))
            fig.add_trace(go.Bar(x=df_preenchidos['Data'], y=df_preenchidos['🎯 Meta do Dia (R$)'], name='Meta Esperada', marker_color='#3b82f6'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insira lançamentos para gerar o gráfico.")

except Exception as e:
    st.error("Link inválido ou permissão pendente. Lembre-se de colocar 'Qualquer pessoa com o link' como Leitor no botão Compartilhar do Sheets.")
