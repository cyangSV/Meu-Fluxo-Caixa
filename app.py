import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Online", layout="wide", initial_sidebar_state="collapsed")

# Memória para forçar atualização da tabela
if 'atualizador' not in st.session_state:
    st.session_state['atualizador'] = 0

# --- 2. CONSTANTES (A estrutura do seu banco de dados) ---
COLUNAS = ['Data', 'Funcionária', 'Dinheiro', 'Débito', 'Crédito', 'Pix', 'Quebra', 'Retirada', 'Justificativa']

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
        # Remove linhas onde a funcionária não foi preenchida para não sujar o Google Sheets
        df_salvar = df_novo.dropna(subset=['Funcionária'])
        df_salvar = df_salvar[df_salvar['Funcionária'].astype(str).str.strip() != '']
        
        # Envia para a nuvem
        conn.update(data=df_salvar)
        st.cache_data.clear()
        st.success("✅ Dados sincronizados com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao salvar: Verifique se a conta de serviço tem permissão de 'Editor'.")

# --- 4. DESIGN E ESTILOS (CSS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .caixa-vermelha { background-color: #FFF0F0; color: #D32F2F; padding: 15px; border-radius: 8px; font-weight: bold; display: flex; justify-content: space-between; margin-bottom: 10px; border: 1px solid #FFCDD2; }
    .caixa-laranja { background-color: #FFF3E0; color: #E65100; padding: 15px; border-radius: 8px; font-weight: bold; display: flex; justify-content: space-between; margin-bottom: 10px; border: 1px solid #FFE0B2; }
    .caixa-roxa { background-color: #F3E5F5; color: #4A148C; padding: 15px; border-radius: 8px; font-weight: bold; display: flex; justify-content: space-between; margin-bottom: 10px; border: 1px solid #E1BEE7; }
    .caixa-verde-clara { background-color: #E8F5E9; color: #1B5E20; padding: 15px; border-radius: 8px; font-weight: bold; display: flex; justify-content: space-between; border: 1px solid #C8E6C9; }
    .texto-cinza { color: #78909C; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .valor-grande { font-size: 24px; font-weight: bold; color: #1E1E1E; }
    .valor-vermelho { color: #F44336; font-size: 20px; font-weight: bold; }
    .valor-laranja { color: #FF9800; font-size: 20px; font-weight: bold; }
    .valor-verde { color: #4CAF50; font-size: 20px; font-weight: bold; }
    .valor-cinza { color: #78909C; font-size: 20px; font-weight: bold; }
    @media print { .stButton, .stTabs, .nao-imprimir { display: none !important; } }
    </style>
""", unsafe_allow_html=True)

# Carrega os dados globais
df_completo = carregar_dados()

# Configuração visual das colunas da tabela
config_tab = {
    "Data": st.column_config.TextColumn("DATA", disabled=True),
    "Funcionária": st.column_config.TextColumn("FUNCIONÁRIA"),
    "Dinheiro": st.column_config.NumberColumn("DINHEIRO", format="%.2f", min_value=0.0),
    "Débito": st.column_config.NumberColumn("DÉBITO", format="%.2f", min_value=0.0),
    "Crédito": st.column_config.NumberColumn("CRÉDITO", format="%.2f", min_value=0.0),
    "Pix": st.column_config.NumberColumn("PIX", format="%.2f", min_value=0.0),
    "Quebra": st.column_config.NumberColumn("QUEBRA", format="%.2f", min_value=0.0),
    "Retirada": st.column_config.NumberColumn("RETIRADA", format="%.2f", min_value=0.0),
    "Total Dia": st.column_config.NumberColumn("TOTAL DIA", format="%.2f")
}

# --- 5. INTERFACE DO USUÁRIO ---
aba_diario, aba_mensal = st.tabs(["❖ Diário", "📅 Mensal"])

# ==========================================
# ABA 1: DIÁRIO (LANÇAMENTOS)
# ==========================================
with aba_diario:
    col_t, col_v, col_d = st.columns([2, 1, 1])
    with col_t:
        st.markdown("<h2 style='margin-bottom: 0px;'>Fluxo de Caixa</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #757575;'>Gestão de fechamentos diários</p>", unsafe_allow_html=True)
    with col_d:
        data_sel = st.date_input("Data:", format="DD/MM/YYYY", label_visibility="collapsed")
        data_str = data_sel.strftime("%Y-%m-%d")

    # Filtra dados do dia ou cria 8 linhas vazias
    df_dia = df_completo[df_completo['Data'] == data_str].copy()
    if df_dia.empty:
        df_dia = pd.DataFrame([{ 'Data': data_str, 'Funcionária': '', 'Dinheiro': 0.0, 'Débito': 0.0, 'Crédito': 0.0, 'Pix': 0.0, 'Quebra': 0.0, 'Retirada': 0.0, 'Justificativa': '' } for _ in range(8)])

    # Cards Superiores (Resumo do Dia)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dinheiro", f"R$ {df_dia['Dinheiro'].sum():.2f}")
    c2.metric("Débito", f"R$ {df_dia['Débito'].sum():.2f}")
    c3.metric("Crédito", f"R$ {df_dia['Crédito'].sum():.2f}")
    c4.metric("Pix", f"R$ {df_dia['Pix'].sum():.2f}")

    st.write("")

    # FORMULÁRIO PARA EVITAR TREMEDEIRA
    with st.form("caixa_form"):
        st.markdown("**📝 Lançamentos do Dia**")
        df_editado = st.data_editor(df_dia, use_container_width=True, hide_index=True, column_config=config_tab, key=f"ed_{data_str}_{st.session_state.atualizador}")
        
        submit = st.form_submit_button("💾 SALVAR NO GOOGLE SHEETS", type="primary", use_container_width=True)
        if submit:
            with st.spinner("Sincronizando..."):
                df_outros_dias = df_completo[df_completo['Data'] != data_str]
                df_final = pd.concat([df_outros_dias, df_editado], ignore_index=True)
                salvar_dados(df_final)
                st.session_state.atualizador += 1
                st.rerun()

    # Resumo Financeiro Inferior
    exp = df_editado['Dinheiro'].sum() + df_editado['Débito'].sum() + df_editado['Crédito'].sum() + df_editado['Pix'].sum()
    que = df_editado['Quebra'].sum()
    ret = df_editado['Retirada'].sum()
    liq = exp - que - ret

    col_res, col_que = st.columns([2.5, 1.5])
    with col_res:
        with st.container(border=True):
            st.markdown("<div class='texto-cinza'>LUCRO LÍQUIDO DO DIA</div>", unsafe_allow_html=True)
            r1, r2, r3, r4 = st.columns(4)
            r1.markdown(f"<small>ESPERADO</small><br><b style='color:gray'>R$ {exp:.2f}</b>", unsafe_allow_html=True)
            r2.markdown(f"<small>QUEBRA</small><br><b style='color:red'>R$ {que:.2f}</b>", unsafe_allow_html=True)
            r3.markdown(f"<small>RETIRADA</small><br><b style='color:orange'>R$ {ret:.2f}</b>", unsafe_allow_html=True)
            r4.markdown(f"<small>LÍQUIDO</small><br><b style='color:green'>R$ {liq:.2f}</b>", unsafe_allow_html=True)
    
    with col_que:
        with st.container(border=True):
            st.markdown(f"<div class='caixa-vermelha'><span>Quebra</span><span>R$ {que:.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='caixa-laranja'><span>Retirada</span><span>R$ {ret:.2f}</span></div>", unsafe_allow_html=True)

# ==========================================
# ABA 2: MENSAL (RELATÓRIOS)
# ==========================================
with aba_mensal:
    if not df_completo.empty:
        df_completo['Data_Obj'] = pd.to_datetime(df_completo['Data'], errors='coerce')
        df_completo['AnoMes'] = df_completo['Data_Obj'].dt.strftime('%m/%Y')
        meses = df_completo['AnoMes'].dropna().unique()
        
        if len(meses) > 0:
            col_m1, col_m2 = st.columns([1, 3])
            mes_sel = col_m1.selectbox("Selecione o Mês:", meses)
            
            df_mes = df_completo[df_completo['AnoMes'] == mes_sel].copy()
            df_mes['Total Dia'] = df_mes['Dinheiro'] + df_mes['Débito'] + df_mes['Crédito'] + df_mes['Pix']
            
            # Cards Mensais
            cm1, cm2, cm3, cm4 = st.columns(4)
            cm1.metric("Mensal Dinheiro", f"R$ {df_mes['Dinheiro'].sum():.2f}")
            cm2.metric("Mensal Débito", f"R$ {df_mes['Débito'].sum():.2f}")
            cm3.metric("Mensal Crédito", f"R$ {df_mes['Crédito'].sum():.2f}")
            cm4.metric("Mensal Pix", f"R$ {df_mes['Pix'].sum():.2f}")
            
            st.write("")
            st.markdown("**📋 Detalhamento do Mês**")
            st.dataframe(df_mes.drop(columns=['Data_Obj', 'AnoMes']), use_container_width=True, hide_index=True, column_config=config_tab)
            
            st.write("")
            # Rodapé Mensal
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                with st.container(border=True):
                    st.markdown("**⚠️ Relatório de Quebras**")
                    q_func = df_mes.groupby('Funcionária')['Quebra'].sum().reset_index()
                    st.table(q_func[q_func['Quebra'] > 0])
            with col_f2:
                with st.container(border=True):
                    dias = df_mes['Data'].nunique()
                    media = df_mes['Total Dia'].sum() / dias if dias > 0 else 0
                    st.markdown(f"<div class='caixa-roxa'><span>Dias com Registro</span><span>{dias}</span></div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='caixa-verde-clara'><span>Média por Dia</span><span>R$ {media:.2f}</span></div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum dado registrado para gerar relatórios.")
    else:
        st.info("Sua planilha está vazia. Comece a lançar dados na aba Diário!")
