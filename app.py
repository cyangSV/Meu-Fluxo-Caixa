import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa 2026", layout="wide", initial_sidebar_state="collapsed")

# Memória para forçar atualização da tabela quando necessário
if 'atualizador' not in st.session_state:
    st.session_state['atualizador'] = 0

# --- 2. CONSTANTES (ESTRUTURA DAS COLUNAS) ---
# Definido no topo para nunca dar erro de "não definido"
COLUNAS = ['Data', 'Funcionária', 'Dinheiro', 'Débito', 'Crédito', 'PIX', 'Quebra', 'Retirada', 'Justificativa']

# --- 3. CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(ttl="0s")
        if df is None or df.empty or 'Data' not in df.columns:
            return pd.DataFrame(columns=COLUNAS)
        return df
    except:
        return pd.DataFrame(columns=COLUNAS)

def salvar_dados(df_novo):
    try:
        # Filtra apenas linhas que têm nome de funcionária preenchido
        df_salvar = df_novo.copy()
        df_salvar['Funcionária'] = df_salvar['Funcionária'].fillna('').astype(str)
        df_salvar = df_salvar[df_salvar['Funcionária'].str.strip() != '']
        
        # Envia para a planilha
        conn.update(data=df_salvar)
        st.cache_data.clear()
        st.success("✅ Sincronizado com o Google Sheets!")
    except Exception as e:
        st.error("❌ Erro de permissão: Verifique se a conta de serviço é 'Editor' na planilha.")

# --- 4. ESTILOS VISUAIS (CSS) ---
st.markdown("""
    <style>
    .caixa-vermelha { background-color: #FFF0F0; color: #D32F2F; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #FFCDD2; margin-bottom: 10px; display: flex; justify-content: space-between;}
    .caixa-laranja { background-color: #FFF3E0; color: #E65100; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #FFE0B2; margin-bottom: 10px; display: flex; justify-content: space-between;}
    .caixa-roxa { background-color: #F3E5F5; color: #4A148C; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #E1BEE7; margin-bottom: 10px; display: flex; justify-content: space-between;}
    .caixa-verde { background-color: #E8F5E9; color: #1B5E20; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #C8E6C9; margin-bottom: 10px; display: flex; justify-content: space-between;}
    .texto-cinza { color: #78909C; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .valor-grande { font-size: 24px; font-weight: bold; color: #1E1E1E; }
    </style>
""", unsafe_allow_html=True)

# Inicializa carregamento
df_completo = carregar_dados()

# Configuração de exibição das colunas
config_view = {
    "Data": st.column_config.TextColumn("DATA", disabled=True),
    "Funcionária": st.column_config.TextColumn("FUNCIONÁRIA"),
    "Dinheiro": st.column_config.NumberColumn("DINHEIRO", format="%.2f"),
    "Débito": st.column_config.NumberColumn("DÉBITO", format="%.2f"),
    "Crédito": st.column_config.NumberColumn("CRÉDITO", format="%.2f"),
    "PIX": st.column_config.NumberColumn("PIX", format="%.2f"),
    "Quebra": st.column_config.NumberColumn("QUEBRA", format="%.2f"),
    "Retirada": st.column_config.NumberColumn("RETIRADA", format="%.2f"),
    "Esperado": st.column_config.NumberColumn("ESPERADO", format="R$ %.2f"),
    "Total Dia": st.column_config.NumberColumn("TOTAL DIA", format="R$ %.2f")
}

aba_diario, aba_mensal = st.tabs(["❖ Diário", "📅 Mensal"])

# ==========================================
# ABA 1: DIÁRIO
# ==========================================
with aba_diario:
    col_t, col_v, col_d = st.columns([2, 1, 1])
    data_sel = col_d.date_input("Data:", format="DD/MM/YYYY", label_visibility="collapsed")
    data_str = data_sel.strftime("%Y-%m-%d")
    
    col_t.markdown(f"## Fluxo de Caixa")
    col_t.markdown(f"Gestão diária de fechamentos e turnos")

    # Filtra dados do dia ou cria 8 linhas
    df_dia = df_completo[df_completo['Data'] == data_str].copy()
    if len(df_dia) < 8:
        sobrando = 8 - len(df_dia)
        vazios = pd.DataFrame([{ 'Data': data_str, 'Funcionária': '', 'Dinheiro': 0.0, 'Débito': 0.0, 'Crédito': 0.0, 'PIX': 0.0, 'Quebra': 0.0, 'Retirada': 0.0, 'Justificativa': '' } for _ in range(sobrando)])
        df_dia = pd.concat([df_dia, vazios], ignore_index=True)

    # Cálculo da coluna "Esperado" (Soma das entradas)
    df_dia['Esperado'] = df_dia['Dinheiro'] + df_dia['Débito'] + df_dia['Crédito'] + df_dia['PIX']

    # Cards de Resumo no Topo
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='texto-cinza'>Total Dinheiro</div><div class='valor-grande'>R$ {df_dia['Dinheiro'].sum():.2f}</div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='texto-cinza'>Total Débito</div><div class='valor-grande'>R$ {df_dia['Débito'].sum():.2f}</div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='texto-cinza'>Total Crédito</div><div class='valor-grande'>R$ {df_dia['Crédito'].sum():.2f}</div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='texto-cinza'>Total PIX</div><div class='valor-grande'>R$ {df_dia['PIX'].sum():.2f}</div>", unsafe_allow_html=True)

    st.write("")

    # FORMULÁRIO PARA EVITAR TREMEDEIRA
    with st.form("form_diario"):
        st.markdown(f"### Lançamentos de {data_sel.strftime('%d/%m/%Y')}")
        # Editor com lixeirinha ativada (num_rows="dynamic")
        df_editado = st.data_editor(
            df_dia, 
            use_container_width=True, 
            hide_index=False, 
            column_config=config_view,
            num_rows="dynamic",
            key=f"editor_{data_str}_{st.session_state.atualizador}"
        )
        
        salvar = st.form_submit_button("💾 SALVAR FECHAMENTO DO DIA", type="primary", use_container_width=True)
        
        if salvar:
            # Re-calcula esperado antes de salvar
            df_editado['Data'] = data_str
            df_restante = df_completo[df_completo['Data'] != data_str]
            df_final = pd.concat([df_restante, df_editado], ignore_index=True)
            salvar_dados(df_final)
            st.session_state.atualizador += 1
            st.rerun()

    # Resumo Final do Dia
    t_esperado = df_editado['Dinheiro'].sum() + df_editado['Débito'].sum() + df_editado['Crédito'].sum() + df_editado['PIX'].sum()
    t_quebra = df_editado['Quebra'].sum()
    t_retirada = df_editado['Retirada'].sum()
    s_liquido = t_esperado - t_quebra - t_retirada

    st.write("---")
    col_inf1, col_inf2 = st.columns([2, 1.5])
    
    with col_inf1:
        st.markdown("### Lucro Total do Dia")
        inf1, inf2, inf3, inf4 = st.columns(4)
        inf1.markdown(f"<div class='texto-cinza'>Esperado</div><b>R$ {t_esperado:.2f}</b>", unsafe_allow_html=True)
        inf2.markdown(f"<div class='texto-cinza'>Quebra</div><b style='color:red'>R$ {t_quebra:.2f}</b>", unsafe_allow_html=True)
        inf3.markdown(f"<div class='texto-cinza'>Retirada</div><b style='color:orange'>R$ {t_retirada:.2f}</b>", unsafe_allow_html=True)
        inf4.markdown(f"<div class='texto-cinza'>Líquido</div><b style='color:green'>R$ {s_liquido:.2f}</b>", unsafe_allow_html=True)

    with col_inf2:
        st.markdown("### Resumo de Quebras")
        st.markdown(f"<div class='caixa-vermelha'><span>Quebra Total</span><span>R$ {t_quebra:.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='caixa-laranja'><span>Retiradas</span><span>R$ {t_retirada:.2f}</span></div>", unsafe_allow_html=True)

# ==========================================
# ABA 2: MENSAL
# ==========================================
with aba_mensal:
    if not df_completo.empty:
        df_completo['Data_Obj'] = pd.to_datetime(df_completo['Data'], errors='coerce')
        df_completo['AnoMes'] = df_completo['Data_Obj'].dt.strftime('%m/%Y')
        meses_lista = df_completo['AnoMes'].dropna().unique()
        
        if len(meses_lista) > 0:
            m_col1, m_col2 = st.columns([1, 2])
            mes_sel = m_col1.selectbox("Selecione o Mês:", meses_lista)
            st.markdown(f"## Resumo Mensal - {mes_sel}")

            df_mes = df_completo[df_completo['AnoMes'] == mes_sel].copy()
            df_mes['Total Dia'] = df_mes['Dinheiro'] + df_mes['Débito'] + df_mes['Crédito'] + df_mes['PIX']

            # Cards Mensais
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='texto-cinza'>Mensal Dinheiro</div><div class='valor-grande'>R$ {df_mes['Dinheiro'].sum():.2f}</div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='texto-cinza'>Mensal Débito</div><div class='valor-grande'>R$ {df_mes['Débito'].sum():.2f}</div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='texto-cinza'>Mensal Crédito</div><div class='valor-grande'>R$ {df_mes['Crédito'].sum():.2f}</div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='texto-cinza'>Mensal PIX</div><div class='valor-grande'>R$ {df_mes['PIX'].sum():.2f}</div>", unsafe_allow_html=True)

            st.write("")
            # Tabela Mensal com Lixeirinha
            st.dataframe(df_mes.drop(columns=['Data_Obj', 'AnoMes', 'Justificativa']), use_container_width=True, hide_index=False, column_config=config_view)
            
            st.write("---")
            col_rel1, col_rel2 = st.columns(2)
            
            with col_rel1:
                st.markdown("### Relatório de Quebras por Funcionária")
                # Agrupa quebras por funcionária
                df_q_func = df_mes.groupby('Funcionária')['Quebra'].sum().reset_index()
                df_q_func = df_q_func[df_q_func['Quebra'] > 0]
                
                if not df_q_func.empty:
                    for _, row in df_q_func.iterrows():
                        st.markdown(f"<div class='caixa-vermelha'><span>{row['Funcionária']}</span><span>R$ {row['Quebra']:.2f}</span></div>", unsafe_allow_html=True)
                else:
                    st.info("Nenhuma quebra registrada este mês.")
                
                st.caption("Nota: Este relatório consolida todas as quebras. Os valores acima são sugestões de desconto.")

            with col_rel2:
                st.markdown("### Resumo Mensal")
                d_reg = df_mes['Data'].nunique()
                media_d = df_mes['Total Dia'].sum() / d_reg if d_reg > 0 else 0
                st.markdown(f"<div class='caixa-roxa'><span>Dias com Registro</span><span>{d_reg}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='caixa-verde'><span>Média por Dia</span><span>R$ {media_d:.2f}</span></div>", unsafe_allow_html=True)
        else:
            st.info("Aguardando lançamentos.")
    else:
        st.info("Planilha vazia.")
