def calcular_tabela_dinamica():
    df = st.session_state.tabela_memoria.copy()
    df = df[df['Data'].isin(datas_fixas)].reset_index(drop=True)
    
    saldos_iniciais = []
    metas_do_dia = []
    saldos_finais = []
    progressos = []
    saldo_atual = saldo_banca_inicial
    
    for idx, row in df.iterrows():
        saldos_iniciais.append(saldo_atual)
        meta_dia_calculada = saldo_banca_inicial + (meta_diaria * (idx + 1))
        metas_do_dia.append(meta_dia_calculada)
        rendimento = float(row['Rendimento']) if pd.notna(row['Rendimento']) else 0.0
        saldo_final_dia = saldo_atual + rendimento
        saldos_finais.append(saldo_final_dia)
        prog_porc = min((saldo_final_dia / meta_final) * 100, 100.0)
        progressos.append(f"{prog_porc:.1f}%")
        saldo_atual = saldo_final_dia
        
    df['Saldo Inicial (R$)'] = saldos_iniciais
    df['Meta do Dia (R$)'] = metas_do_dia
    df['Saldo Final (R$)'] = saldos_finais
    df['Progresso (%)'] = progressos
    return df
