import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Online", layout="wide", initial_sidebar_state="collapsed")

# Memória para forçar atualização visual quando necessário
if 'atualizador' not in st.session_state:
    st.session_state['atualizador'] = 0

# --- 2. CONSTANTES (Estrutura fixa do sistema) ---
COLUNAS = ['Data', 'Funcionária', 'Dinheiro', 'Débito', 'Crédito', 'Pix', 'Quebra', 'Retirada', 'Justificativa']

# --- 3. CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(ttl="0s")
        if df is None or df.empty or 'Data' not in df.columns:
            return pd.DataFrame(columns=COLUNAS)
        return df
    except Exception:
        return pd.DataFrame(columns=COLUNAS)

def salvar_dados(df_novo):
    try:
        # Só envia para o Google o que tiver nome de funcionária preenchido
        df_salvar = df_novo.copy()
        df_salvar['Funcionária'] = df_salvar['Funcionária'].fillna('').astype(str)
        df_salvar = df_salvar[df_salvar['Funcionária'].str.strip() != '']
        
        # Envia a atualização completa
        conn.update(data=df_salvar)
        st.cache_data.clear()
        st.success("✅ Tudo pronto! Os dados já estão na nuvem.")
    except Exception as e:
        st.error(f"❌ Erro de conexão. Verifique os 'Secrets' e as permissões da planilha.")

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
    .valor-cinza { color: #78909C; font-size: 20px; font-weight: bold; }
    @media print { .stButton, .stTabs { display: none !important; } }
    </style>
""", unsafe_allow_html=True)

# Carregamento inicial
df_completo = carregar_dados()

config_tab = {
    "Data": st.column_config.TextColumn("DATA", disabled=True),
    "Funcionária": st.column_config.TextColumn("FUNCIONÁRIA"),
    "Dinheiro": st.column_config.NumberColumn("DINHEIRO", format="R$ %.2f", min_value=0.0),
    "Débito": st.column_config.NumberColumn("DÉBITO", format="R$ %.2f", min_value=0.0),
    "Crédito": st.column_config.NumberColumn("CRÉDITO", format="R$ %.2f", min_value=0.0),
    "Pix": st.column_config.NumberColumn("PIX", format="R$ %.2f", min_value=0.0),
    "Quebra": st.column_config.NumberColumn("QUEBRA", format="R$ %.2f", min_value=0.0),
    "Retirada": st.column_config.NumberColumn("RETIRADA", format="R$ %.2f", min_value=0.0),
    "Justificativa": st.column_config.TextColumn("JUSTIFICATIVA")
}

# --- 5. INTERFACE ---
aba_diario, aba_mensal = st.tabs(["❖ Diário", "📅 Mensal"])

with aba_diario:
    c_t, c_v, c_d = st.columns([2, 1, 1])
    data_sel = c_d.date_input("Data:", format="DD/MM/YYYY", label_visibility="collapsed")
    data_str = data_sel.strftime("%Y-%m-%d")
    
    c_t.markdown(f"## Fluxo de Caixa")
    c_t.markdown(f"Gestão de Lançamentos: {data_sel.strftime('%d/%m/%Y')}")

    # LÓGICA DE MANUTENÇÃO DAS 8 LINHAS
    df_dia = df_completo[df_completo['Data'] == data_str].copy()
    
    # Se tiver menos que 8 linhas, completa com o que falta
    if len(df_dia) < 8:
        sobrando = 8 - len(df_dia)
        vazios = pd.DataFrame([{ 
            'Data': data_str, 'Funcionária': '', 'Dinheiro': 0.0, 'Débito': 0.0, 
            'Crédito': 0.0, 'Pix': 0.0, 'Quebra': 0.0, 'Retirada': 0.0, 'Justificativa': '' 
        } for _ in range(sobrando)])
        df_dia = pd.concat([df_dia, vazios], ignore_index=True)

    # Cards do Dia
    st.write("")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Dinheiro", f"R$ {df_dia['Dinheiro'].sum():.2f}")
    r2.metric("Total Débito", f"R$ {df_dia['Débito'].sum():.2f}")
    r3.metric("Total Crédito", f"R$ {df_dia['Crédito'].sum():.2f}")
    r4.metric("Total Pix", f"R$ {df_dia['Pix'].sum():.2f}")

    # FORMULÁRIO (Trava a tela para não tremer)
    with st.form("form_estavel"):
        df_editado = st.data_editor(
            df_dia, 
            use_container_width=True, 
            hide_index=True, 
            column_config=config_tab,
            key=f"ed_{data_str}_{st.session_state.atualizador}"
        )
        
        salvar = st.form_submit_button("💾 SALVAR TODOS OS FUNCIONÁRIOS", type="primary", use_container_width=True)
        
        if salvar:
            with st.spinner("Sincronizando com a nuvem..."):
                # Remove o dia antigo e coloca o editado
                df_outros = df_completo[df_completo['Data'] != data_str]
                df_final = pd.concat([df_outros, df_editado], ignore_index=True)
                salvar_dados(df_final)
                st.session_state.atualizador += 1
                st.rerun()

    # Totais inferiores
    exp = df_editado['Dinheiro'].sum() + df_editado['Débito'].sum() + df_editado['Crédito'].sum() + df_editado['Pix'].sum()
    que = df_editado['Quebra'].sum()
    ret = df_editado['Retirada'].sum()
    liq = exp - que - ret

    col_res, col_que = st.columns([2.5, 1.5])
    with col_res:
        with st.container(border=True):
            st.markdown("<div class='texto-cinza'>RESUMO FINANCEIRO DO DIA</div>", unsafe_allow_html=True)
            sr1, sr2, sr3, sr4 = st.columns(4)
            sr1.markdown(f"<small>ESPERADO</small><br><b style='color:gray'>R$ {exp:.2f}</b>", unsafe_allow_html=True)
            sr2.markdown(f"<small>QUEBRA</small><br><b style='color:red'>R$ {que:.2f}</b>", unsafe_allow_html=True)
            sr3.markdown(f"<small>RETIRADA</small><br><b style='color:orange'>R$ {ret:.2f}</b>", unsafe_allow_html=True)
            sr4.markdown(f"<small>LÍQUIDO</small><br><b style='color:green'>R$ {liq:.2f}</b>", unsafe_allow_html=True)
    
    with col_que:
        with st.container(border=True):
            st.markdown(f"<div class='caixa-vermelha'><span>Quebra</span><span>R$ {que:.2f}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='caixa-laranja'><span>Retirada</span><span>R$ {ret:.2f}</span></div>", unsafe_allow_html=True)

with aba_mensal:
    if not df_completo.empty:
        df_completo['Data_Obj'] = pd.to_datetime(df_completo['Data'], errors='coerce')
        df_completo['AnoMes'] = df_completo['Data_Obj'].dt.strftime('%m/%Y')
        lista_meses = df_completo['AnoMes'].dropna().unique()
        
        if len(lista_meses) > 0:
            mes_sel = st.selectbox("Selecione o Mês:", lista_meses)
            df_mes = df_completo[df_completo['AnoMes'] == mes_sel].copy()
            df_mes['Total Dia'] = df_mes['Dinheiro'] + df_mes['Débito'] + df_mes['Crédito'] + df_mes['Pix']
            
            # Cards Mensais
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mensal Dinheiro", f"R$ {df_mes['Dinheiro'].sum():.2f}")
            m2.metric("Mensal Débito", f"R$ {df_mes['Débito'].sum():.2f}")
            m3.metric("Mensal Crédito", f"R$ {df_mes['Crédito'].sum():.2f}")
            m4.metric("Mensal Pix", f"R$ {df_mes['Pix'].sum():.2f}")
            
            st.write("")
            st.dataframe(df_mes.drop(columns=['Data_Obj', 'AnoMes']), use_container_width=True, hide_index=True, column_config=config_tab)
        else:
            st.info("Nenhum dado encontrado para gerar o relatório mensal.")
    else:
        st.info("Aguardando lançamentos na aba Diário.")
