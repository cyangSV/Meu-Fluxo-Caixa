import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Online", layout="wide", initial_sidebar_state="collapsed")

# Contador para forçar a atualização da tela
if 'atualizador' not in st.session_state:
    st.session_state['atualizador'] = 0

# --- 2. CONEXÃO COM GOOGLE SHEETS ---
# Esta parte conecta o app à sua planilha na nuvem
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # ttl="0s" obriga o app a buscar o dado mais novo no Google sem usar cache
        return conn.read(ttl="0s")
    except:
        # Se a planilha estiver vazia ou der erro, cria as colunas padrão
        return pd.DataFrame(columns=['Data', 'Funcionária', 'Dinheiro', 'Débito', 'Crédito', 'Pix', 'Quebra', 'Retirada', 'Justificativa'])

def salvar_dados(df_novo):
    # Envia a tabela inteira atualizada para o Google Sheets
    conn.update(data=df_novo)
    st.cache_data.clear()

# --- 3. ESTILOS VISUAIS (O design que você criou) ---
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

# --- 4. CONSTRUÇÃO DAS ABAS ---
aba_diario, aba_mensal = st.tabs(["❖ Diário", "📅 Mensal"])

# ==========================================
# ABA 1: DIÁRIO
# ==========================================
with aba_diario:
    col_titulo, col_vazia, col_data = st.columns([2, 1, 1])
    with col_titulo:
        st.markdown("<h2 style='margin-bottom: 0px; color: #1E1E1E;'>Fluxo de Caixa</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #757575; font-size: 14px;'>Gestão diária de fechamentos e turnos</p>", unsafe_allow_html=True)
    with col_data:
        data_escolhida = st.date_input("Escolha a data:", format="DD/MM/YYYY", label_visibility="collapsed")
        data_str = data_escolhida.strftime("%Y-%m-%d")

    # Filtra os dados do dia
    df_dia = df_completo[df_completo['Data'] == data_str].copy()
    if df_dia.empty:
        df_dia = pd.DataFrame([{
            'Data': data_str, 'Funcionária': '', 'Dinheiro': 0.0, 'Débito': 0.0, 
            'Crédito': 0.0, 'Pix': 0.0, 'Quebra': 0.0, 'Retirada': 0.0, 'Justificativa': ''
        } for _ in range(8)])

    # Correção de tipos
    df_dia['Funcionária'] = df_dia['Funcionária'].fillna('').astype(str)
    df_dia['Justificativa'] = df_dia['Justificativa'].fillna('').astype(str)

    st.write("")

    # Cards Superiores
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
        df_editado = st.data_editor(
            df_dia, use_container_width=True, hide_index=True, column_config=configuracao_tabela, key=chave_tabela
        )
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Salvar no Google Sheets", type="primary", use_container_width=True):
                df_completo = df_completo[df_completo['Data'] != data_str]
                df_completo = pd.concat([df_completo, df_editado], ignore_index=True)
                salvar_dados(df_completo)
                st.session_state['atualizador'] += 1
                st.rerun()
        with col_btn2:
            if st.button("🗑️ Apagar Dados deste Dia", use_container_width=True):
                df_completo = df_completo[df_completo['Data'] != data_str]
                salvar_dados(df_completo)
                st.session_state['atualizador'] += 1
                st.rerun()

    # Cálculos inferiores
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
            with sr1:
                st.markdown("<div class='texto-cinza'>TOTAL ESPERADO</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='valor-cinza'>R$ {total_esperado:.2f}</div>", unsafe_allow_html=True)
            with sr2:
                st.markdown("<div class='texto-cinza'>TOTAL QUEBRA</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='valor-vermelho'>R$ {total_quebra:.2f}</div>", unsafe_allow_html=True)
            with sr3:
                st.markdown("<div class='texto-cinza'>TOTAL RETIRADA</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='valor-laranja'>R$ {total_retiradas:.2f}</div>", unsafe_allow_html=True)
            with sr4:
                st.markdown("<div class='texto-cinza'>SALDO LÍQUIDO</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='valor-verde'>R$ {saldo_liquido:.2f}</div>", unsafe_allow_html=True)

    with col_quebras:
        with st.container(border=True):
            st.markdown("**⚠️ Resumo de Quebras**")
            st.markdown(f"<div class='caixa-vermelha'><span>Quebra Total</span><span>R$ {total_quebra:.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='caixa-laranja'><span>Retiradas</span><span>R$ {total_retiradas:.2f}</span></div>", unsafe_allow_html=True)

# ==========================================
# ABA 2: MENSAL
# ==========================================
with aba_mensal:
    df_completo['Data_Obj'] = pd.to_datetime(df_completo['Data'], errors='coerce')
    df_completo = df_completo.dropna(subset=['Data_Obj'])
    df_completo['AnoMes'] = df_completo['Data_Obj'].dt.strftime('%m/%Y')
    meses_disponiveis = df_completo['AnoMes'].unique()
    
    col_tit_mes, col_vazia_mes, col_sel_mes = st.columns([2, 1, 1])
    with col_tit_mes:
        st.markdown("<h2 style='margin-bottom: 0px; color: #1E1E1E;'>Fluxo de Caixa</h2>", unsafe_allow_html=True)
    with col_sel_mes:
        if len(meses_disponiveis) > 0:
            mes_selecionado = st.selectbox("Selecione o Mês:", meses_disponiveis, label_visibility="collapsed")
        else:
            mes_selecionado = None
            st.write("Sem dados.")

    if mes_selecionado:
        df_mes = df_completo[df_completo['AnoMes'] == mes_selecionado].copy()
        
        cm1, cm2, cm3, cm4 = st.columns(4)
        with cm1:
            with st.container(border=True):
                st.markdown("<div class='texto-cinza'>💲 MENSAL DINHEIRO</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='valor-grande'>R$ {df_mes['Dinheiro'].sum():.2f}</div>", unsafe_allow_html=True)
        # ... (Mantendo os outros 3 cards mensais conforme o design anterior)
        with cm2:
            with st.container(border=True):
                st.markdown("<div class='texto-cinza'>💳 MENSAL DÉBITO</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='valor-grande'>R$ {df_mes['Débito'].sum():.2f}</div>", unsafe_allow_html=True)
        with cm3:
            with st.container(border=True):
                st.markdown("<div class='texto-cinza'>💳 MENSAL CRÉDITO</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='valor-grande'>R$ {df_mes['Crédito'].sum():.2f}</div>", unsafe_allow_html=True)
        with cm4:
            with st.container(border=True):
                st.markdown("<div class='texto-cinza'>📱 MENSAL PIX</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='valor-grande'>R$ {df_mes['Pix'].sum():.2f}</div>", unsafe_allow_html=True)

        st.write("")
        df_mes['Total Dia'] = df_mes['Dinheiro'] + df_mes['Débito'] + df_mes['Crédito'] + df_mes['Pix']
        df_mes_tabela = df_mes[df_mes['Funcionária'].str.strip() != '']
        
        st.dataframe(df_mes_tabela.drop(columns=['Data_Obj', 'AnoMes', 'Justificativa']), use_container_width=True, hide_index=True, column_config=configuracao_tabela)
        
        # Resumos inferiores (Quebras e Médias)
        col_esq, col_dir = st.columns(2)
        with col_esq:
            with st.container(border=True):
                st.markdown("**⚠️ Relatório de Quebras**")
                quebras_por_func = df_mes_tabela.groupby('Funcionária')['Quebra'].sum().reset_index()
                st.dataframe(quebras_por_func[quebras_por_func['Quebra'] > 0], use_container_width=True, hide_index=True)
                st.markdown("<div class='caixa-aviso'>Nota sobre descontos...</div>", unsafe_allow_html=True)
        with col_dir:
            with st.container(border=True):
                st.markdown("**ℹ️ Resumo Mensal**")
                dias = df_mes_tabela['Data'].nunique()
                media = df_mes_tabela['Total Dia'].sum() / dias if dias > 0 else 0
                st.markdown(f"<div class='caixa-roxa'><span>Dias com Registro</span><span>{dias}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='caixa-verde-clara'><span>Média por Dia</span><span>R$ {media:.2f}</span></div>", unsafe_allow_html=True)