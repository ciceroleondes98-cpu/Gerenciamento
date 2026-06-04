import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# Configuração da página para um visual limpo e moderno
st.set_page_config(page_title="Gerenciador de Banca", page_icon="💰", layout="centered")

# Estilização minimalista via CSS (Corrigido para a versão atual do Streamlit)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #2c3e50; color: white; border-radius: 8px; }
    .meta-atingida { color: #2ecc71; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #e74c3c; font-weight: bold; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Controle de Rendimentos")

# Inicializando o banco de dados interno na memória do App se não existir
if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=[
        'Data', 'Saldo Inicial (R$)', '✏️ Rendimento (R$)', '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)'
    ])

# --- TELA INICIAL & CONFIGURAÇÕES ---
st.subheader("Configuração da Banca")
saldo_banca_inicial = st.number_input("Digite o Saldo Inicial Geral (R$):", min_value=0.0, value=200.0, step=10.0)

st.markdown("### **Meta Diária:** R$ 10,00")
meta_final = 500.0

# Progresso Geral da Meta de R$ 500,00
ultimo_saldo = st.session_state.historico['Saldo Final (R$)'].iloc[-1] if not st.session_state.historico.empty else saldo_banca_inicial
progresso_geral = min(ultimo_saldo / meta_final, 1.0)

st.markdown(f"**Progresso Geral:** R$ {ultimo_saldo:,.2f} ➔ R$ {meta_final:,.2f}")
st.progress(progresso_geral)

# Criando as 3 Abas pedidas
tab1, tab2, tab3 = st.tabs(["📝 Registro", "📊 Tabela Geral", "📈 Evolução"])

# --- ABA 1: REGISTRO ---
with tab1:
    st.subheader("Novo Registro Diário")
    
    data_registro = st.date_input("Data:", datetime.date.today())
    valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
    
    # Indicativo Inteligente
    meta_diaria = 10.0
    if valor_rendimento < meta_diaria:
        falta = meta_diaria - valor_rendimento
        st.markdown(f"<p class='meta-abaixo'>⚠️ Abaixo da meta! Faltam R$ {falta:,.2f} para atingir a meta do dia.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p class='meta-atingida'>✅ Meta atingida!</p>", unsafe_allow_html=True)
        
    if st.button("Salvar Registro"):
        # Lógica de preenchimento automático para a Aba 2
        saldo_inicial_linha = ultimo_saldo
        meta_dia_linha = saldo_inicial_linha + meta_diaria
        saldo_final_linha = saldo_inicial_linha + valor_rendimento
        progresso_linha = min((saldo_final_linha / meta_final) * 100, 100.0)
        
        # Adicionando nova linha ao histórico
        nova_linha = {
            'Data': data_registro.strftime('%d/%m/%Y'),
            'Saldo Inicial (R$)': saldo_inicial_linha,
            '✏️ Rendimento (R$)': valor_rendimento,
            '🎯 Meta do Dia (R$)': meta_dia_linha,
            'Saldo Final (R$)': saldo_final_linha,
            'Progresso (%)': f"{progresso_linha:.1f}%"
        }
        
        st.session_state.historico = pd.concat([st.session_state.historico, pd.DataFrame([nova_linha])], ignore_index=True)
        st.success("Registrado com sucesso! Dados atualizados na Aba 2 e 3.")
        st.rerun()

    st.markdown("---")
    st.subheader("Histórico de Registros")
    if not st.session_state.historico.empty:
        st.dataframe(st.session_state.historico[['Data', '✏️ Rendimento (R$)']], hide_index=True)
    else:
        st.info("Nenhum registro feito ainda.")

# --- ABA 2: TABELA GERAL ---
with tab2:
    st.subheader("Tabela de Movimentações Automática")
    if not st.session_state.historico.empty:
        st.dataframe(st.session_state.historico, hide_index=True)
    else:
        st.info("Preencha o rendimento na Aba 1 para gerar a tabela automaticamente.")

# --- ABA 3: EVOLUÇÃO ---
with tab3:
    st.subheader("Gráfico de Evolução da Banca")
    if not st.session_state.historico.empty:
        # Criando o gráfico de barras moderno
        fig = go.Figure()
        
        # Barra do Saldo Atual
        fig.add_trace(go.Bar(
            x=st.session_state.historico['Data'],
            y=st.session_state.historico['Saldo Final (R$)'],
            name='Saldo Final Realizado',
            marker_color='#2c3e50'
        ))
        
        # Linha da Meta Final de R$ 500
        fig.add_trace(go.Scatter(
            x=st.session_state.historico['Data'],
            y=[500.0] * len(st.session_state.historico),
            mode='lines',
            name='Meta Final (R$ 500,00)',
            line=dict(color='#e74c3c', width=3, dash='dash')
        ))
        
        fig.update_layout(
            template='plotly_white',
            xaxis_title="Dias",
            yaxis_title="Valor em Conta (R$)",
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Adicione dados para visualizar o gráfico de evolução.")
