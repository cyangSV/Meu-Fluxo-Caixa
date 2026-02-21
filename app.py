import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Online", layout="wide", initial_sidebar_state="collapsed")

if 'atualizador' not in st.session_state:
    st.session_state['atualizador'] = 0

# --- 2. DEFINIÇÃO DAS COLUNAS (A Farinha do Bolo!) ---
COLUNAS = ['Data', 'Funcionária', 'Dinheiro', 'Débito', 'Crédito', 'Pix', 'Quebra', 'Retirada', 'Justificativa']

# --- 3. CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(ttl="0s")
        # Se a planilha for nova ou estiver sem a coluna Data, retorna estrutura vazia
        if df is None or df.empty or 'Data' not in df.columns:
            return pd.DataFrame(columns=COLUNAS)
        return df
    except:
        return pd.DataFrame(columns=COLUNAS)

def salvar_dados(df_novo):
    try:
        # Limpa linhas que não têm nome de funcionária antes de mandar pro Google
        df_limpo = df_novo.dropna(subset=['Funcionária'])
        df_limpo = df_limpo[df_limpo['Funcionária'].astype(str).str.strip() != '']
        
        # Envia a atualização
        conn.update(data=df_limpo)
        st.cache_data.clear()
        st.success("✅ Sincronizado com o Google Sheets!")
    except Exception as e:
        st.error("❌ Erro ao salvar. Verifique se a conta de serviço é 'Editor' na planilha.")

# --- 4. ESTILOS VISUAIS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .caixa-vermelha { background-color: #FFF0F0; color: #D32F2F; padding: 15px; border-radius: 8px; font-weight: bold; display: flex; justify-content: space-between; margin-bottom: 10px; border: 1px solid #FFCDD2; }
    .caixa-laranja { background-color: #FFF3E0; color: #E65100; padding: 15px; border-radius: 8px; font-weight: bold; display: flex; justify-content: space-between; margin-bottom: 10px; border: 1px solid #FFE0B2; }
    .caixa-roxa { background-color: #F3E5F5; color: #4A148C; padding: 15px; border-radius: 8px; font-weight: bold; display: flex; justify-content: space-between; margin-bottom: 10px; border: 1px solid #E1BEE7; }
    .caixa-verde-clara { background-color: #E8F5E9; color: #1B5E20; padding: 15px; border-radius: 8px; font-weight: bold; display: flex; justify-content: space-between; border: 1px solid #C8E6C9; }
    .caixa-aviso { background-color: #FFF0F0; color: #D32F2F; padding: 15px; border-radius: 8px; font-size: 13px; margin-top: 15px; border: 1px solid #FFCDD2; }
    .texto-cinza { color: #78909C; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .valor-grande { font-size: 24px; font-weight: bold; color: #1E1E1E; margin-top: 0px; }
    .valor-vermelho { color: #F44336; font-size: 20px; font-weight: bold; }
    .valor-laranja { color: #FF9800; font-size: 20px; font-weight: bold; }
    .valor-verde { color: #4CAF50; font-size: 20px; font-weight: bold; }
    .valor-cinza { color: #78909C; font-size: 20px; font-weight: bold; }
    @media print { .stButton, .stTabs, .nao-imprimir { display: none !important; } }
    </style>
""", unsafe_allow_html=True)

df_completo = carregar_dados()

configuracao_tabela = {
    "Data": st.column_config.TextColumn("DATA", disabled=True),
    "Funcionária": st.column_config.TextColumn("FUNCIONÁRIA"),
    "Dinheiro": st.column_config.NumberColumn("DINHEIRO", format="%.2f", min_value=0.0),
    "Débito": st.column_config.NumberColumn("DÉBITO", format="%.2f", min_value=0.0),
    "Crédito": st.column_config.NumberColumn("CRÉDITO", format="%.2f", min_value=0.0),
    "Pix": st.column_config.NumberColumn("PIX", format="%.2f", min_value=0.0),
    "Quebra": st.column_config.NumberColumn("QUEBRA", format="%.2f", min_value=0.0),
    "Retirada": st.column_config.NumberColumn("RETIRADA", format="%.2f", min_value=0.0),
    "Justificativa": st.column_config.TextColumn("JUSTIFICATIVA"),
    "Total Dia": st.column_config.NumberColumn("TOTAL DIA", format="%.2f")
}

aba_diario, aba_mensal = st.tabs(["❖ Diário", "📅 Mensal"])

# --- ABA DIÁRIO ---
with aba_diario:
    col_titulo, col_vazia, col_data = st.columns([2, 1, 1])
    with col_titulo:
        st.markdown("<h2 style='margin-bottom: 0px; color: #1E1E1E;'>Fluxo de Caixa</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #757575; font-size: 14px;'>Gestão diária de fechamentos e turnos</p>", unsafe_allow_html=True)
    with col_data:
        data_escolhida = st.date_input("Escolha a data:", format="DD/MM/YYYY", label_visibility="collapsed")
        data_str = data_escolhida.strftime("%Y-%m-%d")

    df_dia = df_completo[df_completo['Data'] == data_str].copy()
    if df_dia.empty:
        df_dia = pd.DataFrame([{
            'Data': data_str, 'Funcionária': '', 'Dinheiro': 0.0, 'Débito': 0.0, 
            'Crédito': 0.0, 'Pix': 0.0, 'Quebra': 0.0, 'Retirada': 0.0, 'Justificativa': ''
        } for _ in range(8)])

    df_dia['Funcionária'] = df_dia['Funcionária'].fillna('').astype(str)
    df_dia['Justificativa'] = df_dia['Justificativa'].fillna('').astype(str)

    st.write("")
    # Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.markdown("<div class='texto-cinza'>💲 TOTAL DINHEIRO</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='valor-grande'>R$ {df_dia['Dinheiro'].sum():.2f}</div>", unsafe_allow_html=True)
    with c2:
        with st.container(border=True):
            st.markdown("<div class='texto-cinza'>💳 TOTAL DÉBITO</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='valor-grande'>R$ {df_dia['Débito'].sum():.2f}</div>", unsafe_allow_html=True)
    with c3:
        with st.container(border=True):
            st.markdown("<div class='texto-cinza'>💳 TOTAL CRÉDITO</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='valor-grande'>R$ {df_dia['Crédito'].sum():.2f}</div>", unsafe_allow_html=True)
    with c4:
        with st.container(border=True):
            st.markdown("<div class='texto-cinza'>📱 TOTAL PIX</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='valor-grande'>R$ {df_dia['Pix'].sum():.2f}</div>", unsafe_allow_html=True)

    st.write("")
    with st.container(border=True):
        chave_tabela = f"tabela_{data_str}_{st.session_state['atualizador']}"
        df_editado = st.data_editor(df_dia, use_container_width=True, hide_index=True, column_config=configuracao_tabela, key=chave_tabela)
        
        if st.button("💾 Salvar no Google Sheets", type="primary", use_container_width=True):
            df_atualizado = df_completo[df_completo['Data'] != data_str]
            df_atualizado = pd.concat([df_atualizado, df_editado], ignore_index=True)
            salvar_dados(df_atualizado)
            st.session_state['atualizador'] += 1
            st.rerun()

    # Totais inferiores
    total_esperado = df_editado['Dinheiro'].sum() + df_editado['Débito'].sum() + df_editado['Crédito'].sum() + df_editado['Pix'].sum()
    total_quebra = df_editado['Quebra'].sum()
    total_retiradas = df_editado['Retirada'].sum()
    saldo_liquido = total_esperado - total_retiradas - total_quebra

    st.write("")
    col_resumo, col_quebras = st.columns([2.5, 1.5])
    with col_resumo:
        with st.container(border=True):
            st.markdown("<div class='texto-cinza' style='margin-bottom: 30px;'>LUCRO TOTAL DO DIA</div>", unsafe_allow_html=True)
            sr1, sr2, sr3, sr4 = st.columns(4)
            sr1.markdown(f"<div class='texto-cinza'>ESPERADO</div><div class='valor-cinza'>R$ {total_esperado:.2f}</div>", unsafe_allow_html=True)
            sr2.markdown(f"<div class='texto-cinza'>QUEBRA</div><div class='valor-vermelho'>R$ {total_quebra:.2f}</div>", unsafe_allow_html=True)
            sr3.markdown(f"<div class='texto-cinza'>RETIRADA</div><div class='valor-laranja'>R$ {total_retiradas:.2f}</div>", unsafe_allow_html=True)
            sr4.markdown(f"<div class='texto-cinza'>LÍQUIDO</div><div class='valor-verde'>R$ {saldo_liquido:.2f}</div>", unsafe_allow_html=True)

    with col_quebras:
        with st.container(border=True):
            st.markdown("**⚠️ Resumo**")
            st.markdown(f"<div class='caixa-vermelha'><span>Quebra</span><span>R$ {total_quebra:.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='caixa-laranja'><span>Retirada</span><span>R$ {total_retiradas:.2f}</span></div>", unsafe_allow_html=True)

# --- ABA MENSAL ---
with aba_mensal:
    if not df_completo.empty:
        df_completo['Data_Obj'] = pd.to_datetime(df_completo['Data'], errors='coerce')
        df_completo['AnoMes'] = df_completo['Data_Obj'].dt.strftime('%m/%Y')
        meses = df_completo['AnoMes'].dropna().unique()
        
        if len(meses) > 0:
            mes_sel = st.selectbox("Selecione o Mês:", meses)
            df_mes = df_completo[df_completo['AnoMes'] == mes_sel].copy()
            df_mes['Total Dia'] = df_mes['Dinheiro'] + df_mes['Débito'] + df_mes['Crédito'] + df_mes['Pix']
            
            # Cards Mensais
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Dinheiro", f"R$ {df_mes['Dinheiro'].sum():.2f}")
            m2.metric("Débito", f"R$ {df_mes['Débito'].sum():.2f}")
            m3.metric("Crédito", f"R$ {df_mes['Crédito'].sum():.2f}")
            m4.metric("Pix", f"R$ {df_mes['Pix'].sum():.2f}")
            
            st.dataframe(df_mes.drop(columns=['Data_Obj', 'AnoMes']), use_container_width=True, hide_index=True, column_config=configuracao_tabela)
        else:
            st.info("Aguardando dados...")
    else:
        st.info("Nenhum dado encontrado na planilha.")
