import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import requests
import json
import base64

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
    .stButton>button { background-color: #f1b813; color: #030f26; border-radius: 8px; border: none; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { background-color: #d6a10b; color: #030f26; }
    .meta-atingida { color: #10b981; font-weight: bold; font-size: 18px; }
    .meta-abaixo { color: #ef4444; font-weight: bold; font-size: 18px; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #f1b813; border-bottom-color: #f1b813; }
    </style>
    """, unsafe_allow_html=True)

st.title("🪙 Controle de Rendimentos Pro")

# Integração de persistência via GitHub API
TOKEN = st.secrets.get("GITHUB_TOKEN", "").strip()
REPO = st.secrets.get("REPO_NAME", "").strip()
FILE_PATH = "dados_banca.json"
BRANCH = "main"  # Forçando o uso da branch correta vista no seu GitHub

def carregar_dados_github():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}?ref={BRANCH}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        conteudo = response.json()
        dados_decodificados = base64.b64decode(conteudo["content"]).decode("utf-8").strip()
        try:
            if not dados_decodificados or dados_decodificados == "{}":
                return {}, conteudo["sha"]
            return json.loads(dados_decodificados), conteudo["sha"]
        except:
            return {}, conteudo["sha"]
    return None, None

def salvar_dados_github(dados, sha=None):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    dados_json = json.dumps(dados, indent=4, ensure_ascii=False)
    dados_bytes = base64.b64encode(dados_json.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": "Atualizando dados da banca via app",
        "content": dados_bytes,
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
        
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

# Inicialização de segurança
dados_salvos, arquivo_sha = None, None
if TOKEN and REPO:
    try:
        dados_salvos, arquivo_sha = carregar_dados_github()
    except:
        pass

if dados_salvos and isinstance(dados_salvos, dict) and "saldo_inicial" in dados_salvos:
    val_saldo = dados_salvos.get("saldo_inicial", 250.0)
    val_meta_f = dados_salvos.get("meta_final", 650.0)
    val_meta_d = dados_salvos.get("meta_diaria", 12.0)
    val_dias = dados_salvos.get("qtd_dias", 33)
    historico_lista = dados_salvos.get("historico", [])
else:
    val_saldo, val_meta_f, val_meta_d, val_dias, historico_lista = 250.0, 650.0, 12.0, 33, []

# Inputs da interface
st.subheader("⚙️ Configuração da Banca e Período")
col_banca1, col_banca2, col_banca3, col_banca4 = st.columns(4)
with col_banca1: saldo_banca_inicial = st.number_input("Saldo Inicial (R$):", min_value=0.0, value=float(val_saldo), step=10.0)
with col_banca2: meta_final = st.number_input("Meta Final Geral (R$):", min_value=1.0, value=float(val_meta_f), step=50.0)
with col_banca3: meta_diaria = st.number_input("Meta Diária (R$):", min_value=0.0, value=float(val_meta_d), step=1.0)
with col_banca4: quantidade_dias = st.number_input("Qtd de Dias:", min_value=1, max_value=365, value=int(val_dias), step=1)

if st.button("💾 Salvar Parâmetros Operacionais"):
    novos_dados = {"saldo_inicial": saldo_banca_inicial, "meta_final": meta_final, "meta_diaria": meta_diaria, "qtd_dias": quantidade_dias, "historico": historico_lista}
    if salvar_dados_github(novos_dados, arquivo_sha):
        st.success("✅ Configurações salvas permanentemente no GitHub!")
        st.rerun()
    else:
        st.error("Erro ao conectar com o GitHub. Verifique as credenciais nos Segredos.")

# Estruturação de dados baseada em datas operacionais (Junho/2026)
datas_fixas = [(datetime.date(2026, 6, 1) + datetime.timedelta(days=i)).strftime('%d/%m/%Y') for i in range(quantidade_dias)]
dict_historico = {item['Data']: float(item['Rendimento']) for item in historico_lista}

saldos_iniciais, metas_do_dia, rendimentos_col, saldos_finais, progressos, preenchidos = [], [], [], [], [], []
saldo_atual = saldo_banca_inicial

for idx, data in enumerate(datas_fixas):
    saldos_iniciais.append(saldo_atual)
    metas_do_dia.append(saldo_banca_inicial + (meta_diaria * (idx + 1)))
    rend = dict_historico.get(data, 0.0)
    rendimentos_col.append(rend)
    foi_p = data in dict_historico
    preenchidos.append(foi_p)
    saldo_final_dia = saldo_atual + rend
    saldos_finais.append(saldo_final_dia)
    progressos.append(f"{min((saldo_final_dia / meta_final) * 100, 100.0):.1f}%")
    saldo_atual = saldo_final_dia

df_calculado = pd.DataFrame({'Data': datas_fixas, 'Saldo Inicial (R$)': saldos_iniciais, '📈 Rendimento (R$)': rendimentos_col, '🏆 Meta do Dia (R$)': metas_do_dia, 'Saldo Final (R$)': saldos_finais, 'Progresso (%)': progressos, 'Preenchido': preenchidos})
df_preenchidos = df_calculado[df_calculado['Preenchido'] == True]
ultimo_saldo = df_preenchidos['Saldo Final (R$)'].iloc[-1] if not df_preenchidos.empty else saldo_banca_inicial
progresso_porcentagem = min((ultimo_saldo / meta_final) * 100, 100.0)

st.markdown(f"""
<div class="banca-card">
    <span style="color: #94a3b8; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">🚀 RESUMO DA OPERAÇÃO</span>
    <h3 style="margin: 8px 0 12px 0;">🎯 Meta Diária: R$ {meta_diaria:,.2f}</h3>
    <p style="font-size: 16px; margin: 0; color: #f1b813;"><b>Saldo Atual:</b> R$ {ultimo_saldo:,.2f} ➔ <b>Alvo Final:</b> R$ {meta_final:,.2f} | <b>Período:</b> {quantidade_dias} dias</p>
</div>
""", unsafe_allow_html=True)
st.markdown(f"**Progresso Geral para o Alvo:** {progresso_porcentagem:.1f}%")
st.progress(min(ultimo_saldo / meta_final, 1.0))

tab1, tab2, tab3 = st.tabs(["📝 Lançamentos", "📊 Visão Geral", "📈 Gráfico de Evolução"])

with tab1:
    st.subheader("Novo Registro Diário")
    data_selecionada = st.selectbox("Escolha a Data:", df_calculado['Data'].tolist())
    valor_rendimento = st.number_input("Valor do Rendimento (R$):", min_value=0.0, value=0.0, step=1.0)
    st.markdown("<p class='meta-atingida'>✅ Meta atingida!</p>" if valor_rendimento >= meta_diaria else "<p class='meta-abaixo'>⚠️ Abaixo da meta!</p>", unsafe_allow_html=True)
    
    if st.button("Confirmar e Salvar Registro"):
        novo_hist = [item for item in historico_lista if item['Data'] != data_selecionada]
        novo_hist.append({"Data": data_selecionada, "Rendimento": valor_rendimento})
        novos_dados = {"saldo_inicial": saldo_banca_inicial, "meta_final": meta_final, "meta_diaria": meta_diaria, "qtd_dias": quantidade_dias, "historico": novo_hist}
        if salvar_dados_github(novos_dados, arquivo_sha):
            st.success("🔥 Lançamento gravado com sucesso no repositório!")
            st.rerun()
        else:
            st.error("Erro ao salvar lançamento no GitHub.")

    st.markdown("---")
    st.subheader("⏱️ Histórico Recente")
    for item in historico_lista:
        c1, c2, c3 = st.columns([3, 3, 1])
        c1.markdown(f"📅 **{item['Data']}**")
        c2.markdown(f"💰 Rendimento: <span style='color: #f1b813; font-weight: bold;'>R$ {float(item['Rendimento']):,.2f}</span>", unsafe_allow_html=True)
        if c3.button("🗑️", key=f"del_{item['Data']}"):
            novo_hist = [i for i in historico_lista if i['Data'] != item['Data']]
            novos_dados = {"saldo_inicial": saldo_banca_inicial, "meta_final": meta_final, "meta_diaria": meta_diaria, "qtd_dias": quantidade_dias, "historico": novo_hist}
            salvar_dados_github(novos_dados, arquivo_sha)
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
