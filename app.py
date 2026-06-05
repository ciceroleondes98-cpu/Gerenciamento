import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da página
st.set_page_config(page_title="Gerenciador de Banca Pro", page_icon="💰", layout="centered")

# Estilização visual premium
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #1f2937 0%, #111827 100%); color: #ffffff; }
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #10b981 !important; font-weight: 700; }
    .banca-card { background-color: #ffffff; padding: 20px; border-radius: 12px; color: #111827; margin-bottom: 20px; }
    .banca-card h3, .banca-card p, .banca-card span { color: #111827 !important; }
    .stButton>button { background-color: #10b981; color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #059669; color: white; }
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #f87171; font-weight: bold; font-size: 18px; }
    .stTabs [data-baseweb="tab"] { color: #9ca3af; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #10b981; border-bottom-color: #10b981; }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Controle de Rendimentos Conectado")

# Inicializando a conexão oficial com o Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lendo os dados brutos da planilha em tempo real
    df_raw = conn.read(worksheet="🎯 Meta Diária", ttl=0)
    
    # --- CAPTURA DINÂMICA DE PARÂMETROS DIRETO DA SUA PLANILHA ---
    try:
        # Puxa o saldo inicial da célula A5 e meta final da célula G5 (ajustado pelo índice do pandas)
        saldo_banca_inicial = float(df_raw.iloc[3, 0]) 
        meta_final = float(df_raw.iloc[3, 6])
    except:
        # Valores de segurança caso a leitura falhe
        saldo_banca_inicial = 200.0
        meta_final = 500.0

    # Identificar a linha exata do cabeçalho da tabela (onde tem a palavra 'Dia')
    linha_cabecalho = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains('Dia').any():
            linha_cabecalho = i
            break
            
    if linha_cabecalho is not None:
        colunas_reais = df_raw.iloc[linha_cabecalho].tolist()
        df_sheets = df_raw.iloc[linha_cabecalho + 1:].copy()
        df_sheets.columns = colunas_reais
        df_sheets = df_sheets.reset_index(drop=True)
    else:
        df_sheets = df_raw.copy()

    # Limpando linhas que não possuem a identificação do Dia
    df_sheets = df_sheets.dropna(subset=['Dia']).reset_index(drop=True)
    
    # Trata e limpa a coluna de Rendimento transformando em número puro
    col_rendimento_nome = '✏️ Rendimento (R$)' if '✏️ Rendimento (R$)' in df_sheets.columns else 'Rendimento'
    df_sheets[col_rendimento_nome] = pd.to_numeric(df_sheets[col_rendimento_nome].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip(), errors='coerce').fillna(0.0)

except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

# Meta diária padrão do projeto
meta_diaria = 10.0

# --- CÁLCULO AUTOMÁTICO EM CASCATA ---
def processar_cascata_financeira(df):
    df_calculado = df.copy()
    saldos_iniciais, metas_do_dia, saldos_finais, progressos, meta_atingida = [], [], [], [], []
    saldo_atual = saldo_banca_inicial
    
    for idx, row in df_calculado.iterrows():
        saldos_iniciais.append(saldo_atual)
        meta_dia_calculada = saldo_banca_inicial + (meta_diaria * (idx + 1))
        metas_do_dia.append(meta_dia_calculada)
        
        rendimento = float(row[col_rendimento_nome])
        saldo_final_dia = saldo_atual + rendimento
        saldos_finais.append(saldo_final_dia)
        
        prog_porc = (saldo_final_dia / meta_final) * 100
        progressos.append(f"{prog_porc:.1f}%")
        meta_atingida.append("✅ SIM" if rendimento >= meta_diaria else "❌ NÃO")
        
        saldo_atual = saldo_final_dia
        
    df_calculado['Saldo Inicial (R$)'] = saldos_iniciais
    df_calculado['🎯 Meta do Dia (R$)'] = metas_do_dia
    df_calculado['Saldo Final (R$)'] = saldos_finais
    df_calculado['Progresso (%)'] = progressos
    df_calculado['Meta Atingida?'] = meta_atingida
    return df_calculado

df_final = processar_cascata_financeira(df_sheets)

# Busca o progresso atual baseado nos dias que você já preencheu valor maior que 0
df_preenchidos = df_final[df_final[col_rendimento_nome] > 0]
ultimo_saldo = df_final['Saldo Final (R$)'].iloc[len(df_preenchidos)-1] if not df_preenchidos.empty else saldo_banca_inicial
progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)

# Card de Resumo Visual no Topo
st.markdown(f"""
<div class="banca-card">
    <span style="color: #6b7280; font-size: 14px; font-weight: bold; text-transform: uppercase;">Resumo em Tempo Real (Planilha Ativa)</span>
    <h3 style="margin: 5px 0 10px 0;">🎯 Meta Diária do Plano: R$ {meta_diaria:,.2f}</h3>
    <p style="font-size: 16px; margin: 0;">
        <b>Banca Atualizada:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f}
    </p>
</div>
""", unsafe_allow_html=True)
st.progress(min(ultimo_saldo / meta_final, 1.0))

tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📊 Tabela Integrada", "📈 Gráfico de Evolução"])

# --- ABA 1: LANÇAMENTOS ---
with tab1:
    st.subheader("Registrar Rendimento Direto no Google Sheets")
    
    # Criando a lista de dias de forma correta e isolada para evitar o erro de referência
    datas_lista = df_final['Dia'].astype(str).tolist()
    dia_selecionado = st.selectbox("Selecione o Dia para Atualizar:", datas_lista)
    
    valor_rendimento = st.number_input("Digite o Rendimento deste dia (R$):", min_value=0.0, step=1.0)
    
    if st.button("🚀 Confirmar e Salvar na Planilha"):
        idx_planilha = df_sheets[df_sheets['Dia'].astype(str) == dia_selecionado].index[0]
        df_sheets.at[idx_planilha, col_rendimento_nome] = valor_rendimento
        
        # Reconstrói a tabela inteira recolocando os cabeçalhos decorativos antes de enviar pro Drive
        df_salvar = df_raw.copy()
        for idx, row in df_sheets.iterrows():
            df_salvar.iloc[linha_cabecalho + 1 + idx] = row.tolist()
            
        conn.update(worksheet="🎯 Meta Diária", data=df_salvar)
        st.success(f"Planilha Google Atualizada com Sucesso para o dia {dia_selecionado}!")
        st.rerun()

    st.markdown("---")
    st.subheader("Histórico de Ganhos Registrados")
    if not df_preenchidos.empty:
        for idx, row in df_preenchidos.iterrows():
            c1, c2, c3 = st.columns([2, 3, 1])
            with c1: st.markdown(f"📅 **Dia {row['Dia']}**")
            with c2: st.markdown(f"💰 Rendimento: **R$ {row[col_rendimento_nome]:,.2f}**")
            with c3:
                if st.button("🗑️", key=f"del_{idx}"):
                    df_sheets.at[idx, col_rendimento_nome] = 0.0
                    df_salvar = df_raw.copy()
                    for i_salve, r_salve in df_sheets.iterrows():
                        df_salvar.iloc[linha_cabecalho + 1 + i_salve] = r_salve.tolist()
                    conn.update(worksheet="🎯 Meta Diária", data=df_salvar)
                    st.rerun()

# --- ABA 2: TABELA GERAL ---
with tab2:
    st.subheader("Dados Sincronizados com o Google Sheets")
    colunas_exibir = ['Dia', 'Saldo Inicial (R$)', col_rendimento_nome, '🎯 Meta do Dia (R$)', 'Saldo Final (R$)', 'Progresso (%)', 'Meta Atingida?']
    st.dataframe(df_final[colunas_exibir], hide_index=True, use_container_width=True)

# --- ABA 3: EVOLUÇÃO ---
with tab3:
    st.subheader("Gráfico Progressivo de Evolução")
    if not df_preenchidos.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_preenchidos['Dia'], y=df_preenchidos['Saldo Final (R$)'], name='Seu Saldo Final', marker_color='#10b981'))
        fig.add_trace(go.Bar(x=df_preenchidos['Dia'], y=df_preenchidos['🎯 Meta do Dia (R$)'], name='Meta Acumulada', marker_color='#3b82f6'))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), barmode='group')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Preencha dados na aba de lançamentos para visualizar o gráfico.")
