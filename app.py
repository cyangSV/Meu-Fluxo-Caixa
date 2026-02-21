import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Online", layout="wide", initial_sidebar_state="collapsed")

if 'atualizador' not in st.session_state:
    st.session_state['atualizador'] = 0

# --- 2. CONSTANTES ---
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
        # Filtra apenas linhas que têm nome de funcionária
        df_salvar = df_novo.copy()
        df_salvar['Funcionária'] = df_salvar['Funcionária'].fillna('').astype(str)
        df_salvar = df_salvar[df_salvar['Funcionária'].str.strip() != '']
        
        conn.update(data=df_salvar)
        st.cache_data.clear()
        st.success("✅ Sincronizado com o Google Sheets!")
    except Exception as e:
        st.error("❌ Erro ao salvar. Verifique as permissões da planilha.")

# --- 4. ESTILOS VISUAIS ---
st.markdown("""
    <style>
    .caixa-vermelha { background-color: #FFF0F0; color: #D32F2F; padding: 10px; border-radius: 5px; font-weight: bold; border: 1px solid #FFCDD2; margin-bottom: 5px; }
    .caixa-laranja { background-color: #FFF3E0; color: #E65100; padding: 10px; border-radius: 5px; font-weight: bold; border: 1px solid #FFE0B2; margin-bottom: 5px; }
    .caixa-roxa { background-color: #F3E5F5; color: #4A148C; padding: 10px; border-radius: 5px; font-weight: bold; border: 1px solid #E1BEE7; }
    .caixa-verde { background-color: #E8F5E9; color: #1B5E20; padding: 10px; border-radius: 5px; font-weight: bold; border: 1px solid #C8E6C9; }
    </style>
""", unsafe_allow_html=True)

df_completo = carregar_dados()

config_tab = {
    "Data": st.column_config.TextColumn("DATA", disabled=True),
    "Funcionária": st.column_config.TextColumn("FUNCIONÁRIA"),
    "Dinheiro": st.column_config.NumberColumn("DINHEIRO", format="%.2f"),
    "Débito": st.column_config.NumberColumn("DÉBITO", format="%.2f"),
    "Crédito": st.column_config.NumberColumn("CRÉDITO", format="%.2f"),
    "Pix": st.column_config.NumberColumn("PIX", format="%.2f"),
    "Quebra": st.column_config.NumberColumn("QUEBRA", format="%.2f"),
    "Retirada": st.column_config.NumberColumn("RETIRADA", format="%.2f"),
}

aba_diario, aba_mensal = st.tabs(["❖ Diário", "📅 Mensal"])

# ==========================================
# ABA 1: DIÁRIO
# ==========================================
with aba_diario:
    c1, c2, c3 = st.columns([2, 1, 1])
    data_sel = c3.date_input("Data:", format="DD/MM/YYYY", label_visibility="collapsed")
    data_str = data_sel.strftime("%Y-%m-%d")
    
    c1.markdown(f"## Caixa do Dia: {data_sel.strftime('%d/%m/%Y')}")

    df_dia = df_completo[df_completo['Data'] == data_str].copy()
    
    # Garantir as 8 linhas iniciais
    if len(df_dia) < 8:
        vazios = pd.DataFrame([{'Data': data_str, 'Funcionária': '', 'Dinheiro': 0.0, 'Débito': 0.0, 'Crédito': 0.0, 'Pix': 0.0, 'Quebra': 0.0, 'Retirada': 0.0, 'Justificativa': ''} for _ in range(8 - len(df_dia))])
        df_dia = pd.concat([df_dia, vazios], ignore_index=True)

    # Cards Rápidos
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Dinheiro", f"R$ {df_dia['Dinheiro'].sum():.2f}")
    r2.metric("Débito", f"R$ {df_dia['Débito'].sum():.2f}")
    r3.metric("Crédito", f"R$ {df_dia['Crédito'].sum():.2f}")
    r4.metric("Pix", f"R$ {df_dia['Pix'].sum():.2f}")

    with st.form("form_diario"):
        st.info("💡 Para apagar uma linha: Selecione o quadradinho à esquerda da linha e aperte 'Delete' no teclado.")
        df_editado = st.data_editor(
            df_dia, 
            use_container_width=True, 
            hide_index=False, # Mostra o índice para facilitar a seleção/exclusão
            column_config=config_tab,
            num_rows="dynamic", # HABILITA A LIXEIRINHA/EXCLUSÃO
            key=f"editor_{data_str}_{st.session_state.atualizador}"
        )
        
        if st.form_submit_button("💾 SALVAR ALTERAÇÕES", type="primary", use_container_width=True):
            # Substitui os dados do dia no banco global
            df_restante = df_completo[df_completo['Data'] != data_str]
            df_final = pd.concat([df_restante, df_editado], ignore_index=True)
            salvar_dados(df_final)
            st.session_state.atualizador += 1
            st.rerun()

# ==========================================
# ABA 2: MENSAL
# ==========================================
with aba_mensal:
    if not df_completo.empty:
        df_completo['Data_Obj'] = pd.to_datetime(df_completo['Data'], errors='coerce')
        df_completo['AnoMes'] = df_completo['Data_Obj'].dt.strftime('%m/%Y')
        meses = df_completo['AnoMes'].dropna().unique()
        
        if len(meses) > 0:
            mes_sel = st.selectbox("Escolha o Mês:", meses)
            df_mes = df_completo[df_completo['AnoMes'] == mes_sel].copy()
            df_mes['Total Dia'] = df_mes['Dinheiro'] + df_mes['Débito'] + df_mes['Crédito'] + df_mes['Pix']

            # Tabela Mensal com Lixeirinha também
            st.markdown("### 📊 Todos os Lançamentos do Mês")
            df_editado_mes = st.data_editor(
                df_mes.drop(columns=['Data_Obj', 'AnoMes']),
                use_container_width=True,
                num_rows="dynamic",
                column_config=config_tab,
                key=f"mes_{mes_sel}"
            )
            
            if st.button("💾 ATUALIZAR MENSAL (Salvar exclusões/ajustes)"):
                # Para o mensal, a lógica de salvar é mais complexa, então avisamos:
                df_outros_meses = df_completo[df_completo['AnoMes'] != mes_sel]
                df_final_mes = pd.concat([df_outros_meses, df_editado_mes], ignore_index=True)
                salvar_dados(df_final_mes)
                st.rerun()

            st.write("---")
            
            # RELATÓRIO DE QUEBRAS (A PARTE QUE FALTAVA)
            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.markdown("### ⚠️ Relatório de Quebras")
                # Agrupa por funcionária e soma as quebras
                df_quebras = df_mes.groupby('Funcionária')['Quebra'].sum().reset_index()
                df_quebras = df_quebras[df_quebras['Quebra'] > 0] # Só mostra quem tem quebra
                
                if not df_quebras.empty:
                    for _, row in df_quebras.iterrows():
                        st.markdown(f"""
                            <div class='caixa-vermelha'>
                                <span>{row['Funcionária']}</span>
                                <span style='float:right'>R$ {row['Quebra']:.2f}</span>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("Nenhuma quebra registrada este mês! 🎉")

            with col_dir:
                st.markdown("### ℹ️ Resumo Geral")
                dias = df_mes['Data'].nunique()
                total_mes = df_mes['Total Dia'].sum()
                media = total_mes / dias if dias > 0 else 0
                st.markdown(f"<div class='caixa-roxa'>Dias trabalhados: {dias}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='caixa-verde'>Média Faturamento/Dia: R$ {media:.2f}</div>", unsafe_allow_html=True)
        else:
            st.info("Lançamentos pendentes.")
    else:
        st.info("Planilha vazia.")
