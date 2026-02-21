import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa 2026", layout="wide", initial_sidebar_state="collapsed")

if 'atualizador' not in st.session_state:
    st.session_state['atualizador'] = 0

# --- 2. CONSTANTES ---
COLUNAS_OBRIGATORIAS = ['Data', 'Funcionária', 'Dinheiro', 'Débito', 'Crédito', 'PIX', 'Quebra', 'Retirada', 'Justificativa']

# --- 3. CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(ttl="0s")
        if df is None or df.empty:
            return pd.DataFrame(columns=COLUNAS_OBRIGATORIAS)
        
        # BLINDAGEM: Garante que todas as colunas existam, independente do que está no Google
        for col in COLUNAS_OBRIGATORIAS:
            if col not in df.columns:
                df[col] = 0.0
        
        return df[COLUNAS_OBRIGATORIAS] # Garante a ordem correta
    except:
        return pd.DataFrame(columns=COLUNAS_OBRIGATORIAS)

def salvar_dados(df_novo):
    try:
        df_salvar = df_novo.copy()
        df_salvar['Funcionária'] = df_salvar['Funcionária'].fillna('').astype(str)
        # Salva apenas quem tem nome de funcionária
        df_salvar = df_salvar[df_salvar['Funcionária'].str.strip() != '']
        
        conn.update(data=df_salvar)
        st.cache_data.clear()
        st.success("✅ Sincronizado com o Google Sheets!")
    except Exception as e:
        st.error("❌ Erro de permissão. Verifique se a conta de serviço é 'Editor' na planilha.")

# --- 4. ESTILOS VISUAIS ---
st.markdown("""
    <style>
    .caixa-vermelha { background-color: #FFF0F0; color: #D32F2F; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #FFCDD2; margin-bottom: 10px; display: flex; justify-content: space-between;}
    .caixa-laranja { background-color: #FFF3E0; color: #E65100; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #FFE0B2; margin-bottom: 10px; display: flex; justify-content: space-between;}
    .caixa-roxa { background-color: #F3E5F5; color: #4A148C; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #E1BEE7; margin-bottom: 10px; display: flex; justify-content: space-between;}
    .caixa-verde { background-color: #E8F5E9; color: #1B5E20; padding: 15px; border-radius: 8px; font-weight: bold; border: 1px solid #C8E6C9; margin-bottom: 10px; display: flex; justify-content: space-between;}
    .texto-cinza { color: #78909C; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

df_completo = carregar_dados()

config_tab = {
    "Data": st.column_config.TextColumn("DATA", disabled=True),
    "Funcionária": st.column_config.TextColumn("FUNCIONÁRIA"),
    "Dinheiro": st.column_config.NumberColumn("DINHEIRO", format="%.2f"),
    "Débito": st.column_config.NumberColumn("DÉBITO", format="%.2f"),
    "Crédito": st.column_config.NumberColumn("CRÉDITO", format="%.2f"),
    "PIX": st.column_config.NumberColumn("PIX", format="%.2f"),
    "Quebra": st.column_config.NumberColumn("QUEBRA", format="%.2f"),
    "Retirada": st.column_config.NumberColumn("RETIRADA", format="%.2f"),
}

aba_diario, aba_mensal = st.tabs(["❖ Diário", "📅 Mensal"])

# ==========================================
# ABA 1: DIÁRIO
# ==========================================
with aba_diario:
    c_t, c_v, c_d = st.columns([2, 1, 1])
    data_sel = c_d.date_input("Data:", format="DD/MM/YYYY", label_visibility="collapsed")
    data_str = data_sel.strftime("%Y-%m-%d")
    
    df_dia = df_completo[df_completo['Data'] == data_str].copy()
    
    # Preenchimento automático de 8 linhas
    if len(df_dia) < 8:
        vazios = pd.DataFrame([{'Data': data_str, 'Funcionária': '', 'Dinheiro': 0.0, 'Débito': 0.0, 'Crédito': 0.0, 'PIX': 0.0, 'Quebra': 0.0, 'Retirada': 0.0, 'Justificativa': ''} for _ in range(8 - len(df_dia))])
        df_dia = pd.concat([df_dia, vazios], ignore_index=True)

    # Cards Resumo Topo
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Dinheiro", f"R$ {df_dia['Dinheiro'].sum():.2f}")
    r2.metric("Total Débito", f"R$ {df_dia['Débito'].sum():.2f}")
    r3.metric("Total Crédito", f"R$ {df_dia['Crédito'].sum():.2f}")
    r4.metric("Total PIX", f"R$ {df_dia['PIX'].sum():.2f}")

    with st.form("form_diario"):
        st.markdown(f"### Lançamentos: {data_sel.strftime('%d/%m/%Y')}")
        df_editado = st.data_editor(df_dia, use_container_width=True, hide_index=False, column_config=config_tab, num_rows="dynamic", key=f"ed_{data_str}_{st.session_state.atualizador}")
        
        if st.form_submit_button("💾 SALVAR TUDO", type="primary", use_container_width=True):
            df_restante = df_completo[df_completo['Data'] != data_str]
            df_final = pd.concat([df_restante, df_editado], ignore_index=True)
            salvar_dados(df_final)
            st.session_state.atualizador += 1
            st.rerun()

    # Totais inferiores
    t_exp = df_editado['Dinheiro'].sum() + df_editado['Débito'].sum() + df_editado['Crédito'].sum() + df_editado['PIX'].sum()
    t_que = df_editado['Quebra'].sum()
    t_ret = df_editado['Retirada'].sum()
    
    st.write("---")
    col_inf1, col_inf2 = st.columns([2, 1.5])
    with col_inf1:
        st.markdown("### Lucro Total do Dia")
        inf1, inf2, inf3, inf4 = st.columns(4)
        inf1.markdown(f"<div class='texto-cinza'>Esperado</div><b>R$ {t_exp:.2f}</b>", unsafe_allow_html=True)
        inf2.markdown(f"<div class='texto-cinza'>Quebra</div><b style='color:red'>R$ {t_que:.2f}</b>", unsafe_allow_html=True)
        inf3.markdown(f"<div class='texto-cinza'>Retirada</div><b style='color:orange'>R$ {t_ret:.2f}</b>", unsafe_allow_html=True)
        inf4.markdown(f"<div class='texto-cinza'>Líquido</div><b style='color:green'>R$ {t_exp - t_que - t_ret:.2f}</b>", unsafe_allow_html=True)

    with col_inf2:
        st.markdown("### Resumo de Quebras")
        st.markdown(f"<div class='caixa-vermelha'><span>Quebra Total</span><span>R$ {t_que:.2f}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='caixa-laranja'><span>Retiradas</span><span>R$ {t_ret:.2f}</span></div>", unsafe_allow_html=True)

# ==========================================
# ABA 2: MENSAL
# ==========================================
with aba_mensal:
    if not df_completo.empty:
        df_completo['Data_Obj'] = pd.to_datetime(df_completo['Data'], errors='coerce')
        df_completo['AnoMes'] = df_completo['Data_Obj'].dt.strftime('%m/%Y')
        meses = df_completo['AnoMes'].dropna().unique()
        
        if len(meses) > 0:
            m_col1, m_col2 = st.columns([1, 2])
            mes_sel = m_col1.selectbox("Selecione o Mês:", meses)
            df_mes = df_completo[df_completo['AnoMes'] == mes_sel].copy()
            
            # Cálculo do Total Dia (Garante que colunas existem e são números)
            for c in ['Dinheiro', 'Débito', 'Crédito', 'PIX']:
                df_mes[c] = pd.to_numeric(df_mes[c], errors='coerce').fillna(0)
            
            df_mes['Total Dia'] = df_mes['Dinheiro'] + df_mes['Débito'] + df_mes['Crédito'] + df_mes['PIX']

            # Cards Mensais
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mensal Dinheiro", f"R$ {df_mes['Dinheiro'].sum():.2f}")
            m2.metric("Mensal Débito", f"R$ {df_mes['Débito'].sum():.2f}")
            m3.metric("Mensal Crédito", f"R$ {df_mes['Crédito'].sum():.2f}")
            m4.metric("Mensal PIX", f"R$ {df_mes['PIX'].sum():.2f}")

            st.write("")
            st.markdown(f"### Lançamentos de {mes_sel}")
            st.dataframe(df_mes.drop(columns=['Data_Obj', 'AnoMes', 'Justificativa']), use_container_width=True, hide_index=False, column_config=config_tab)
            
            st.write("---")
            col_rel1, col_rel2 = st.columns(2)
            with col_rel1:
                st.markdown("### Relatório de Quebras por Funcionária")
                df_q_func = df_mes.groupby('Funcionária')['Quebra'].sum().reset_index()
                df_q_func = df_q_func[df_q_func['Quebra'] > 0]
                if not df_q_func.empty:
                    for _, row in df_q_func.iterrows():
                        st.markdown(f"<div class='caixa-vermelha'><span>{row['Funcionária']}</span><span>R$ {row['Quebra']:.2f}</span></div>", unsafe_allow_html=True)
                else:
                    st.info("Nenhuma quebra registrada este mês.")

            with col_rel2:
                st.markdown("### Resumo Mensal")
                d_reg = df_mes['Data'].nunique()
                t_faturamento = df_mes['Total Dia'].sum()
                media_d = t_faturamento / d_reg if d_reg > 0 else 0
                st.markdown(f"<div class='caixa-roxa'><span>Dias com Registro</span><span>{d_reg}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='caixa-verde'><span>Média por Dia</span><span>R$ {media_d:.2f}</span></div>", unsafe_allow_html=True)
        else:
            st.info("Aguardando lançamentos.")
    else:
        st.info("Planilha vazia.")
