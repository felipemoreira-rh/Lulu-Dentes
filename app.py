import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Lulu Dentes", page_icon="🦷", layout="wide")

# --- FUNÇÃO DE CONEXÃO (Padrão RH App) ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="SUA_SENHA", # <--- Coloca a tua senha aqui
            database="lulu_dentes"
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Erro de Conexão: {err}")
        return None

# --- INICIALIZAÇÃO DO BANCO ---
def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Tabela de Agenda
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agenda (
                id INT AUTO_INCREMENT PRIMARY KEY,
                paciente VARCHAR(100),
                procedimento VARCHAR(100),
                data_hora DATETIME,
                valor DECIMAL(10,2),
                status_pagamento VARCHAR(20) DEFAULT 'Pendente'
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

init_db()

# --- INTERFACE ---
st.title("🦷 Lulu Dentes - Gestão Odontológica")

menu = ["Dashboard", "Agendar Consulta", "Financeiro"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Dashboard":
    st.subheader("Painel Geral")
    
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM agenda", conn)
    conn.close()

    if not df.empty:
        # Métricas
        col1, col2, col3 = st.columns(3)
        total_pago = df[df['status_pagamento'] == 'Pago']['valor'].sum()
        total_pendente = df[df['status_pagamento'] == 'Pendente']['valor'].sum()
        
        col1.metric("Receita Confirmada", f"R$ {total_pago:,.2f}")
        col2.metric("A Receber", f"R$ {total_pendente:,.2f}")
        col3.metric("Total de Atendimentos", len(df))

        st.divider()
        st.write("### Próximas Consultas")
        st.dataframe(df[['paciente', 'procedimento', 'data_hora', 'valor', 'status_pagamento']], use_container_width=True)
    else:
        st.info("Nenhum dado encontrado. Comece agendando uma consulta!")

elif choice == "Agendar Consulta":
    st.subheader("Novo Agendamento")
    
    with st.form("form_lulu"):
        nome = st.text_input("Nome do Paciente")
        proc = st.selectbox("Procedimento", ["Avaliação", "Limpeza", "Canal", "Extração", "Aparelho"])
        data = st.date_input("Data")
        hora = st.time_input("Hora")
        valor = st.number_input("Valor do Serviço (R$)", min_value=0.0)
        
        if st.form_submit_button("Finalizar Agendamento"):
            dt_completa = datetime.combine(data, hora)
            conn = get_db_connection()
            cursor = conn.cursor()
            query = "INSERT INTO agenda (paciente, procedimento, data_hora, valor) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (nome, proc, dt_completa, valor))
            conn.commit()
            cursor.close()
            conn.close()
            st.success(f"Consulta para {nome} agendada com sucesso!")

elif choice == "Financeiro":
    st.subheader("Fluxo de Caixa")
    conn = get_db_connection()
    df = pd.read_sql("SELECT id, paciente, valor, status_pagamento FROM agenda", conn)
    
    if not df.empty:
        st.table(df)
        id_pagar = st.number_input("Digite o ID para confirmar pagamento", min_value=1, step=1)
        if st.button("Confirmar Recebimento"):
            cursor = conn.cursor()
            cursor.execute("UPDATE agenda SET status_pagamento = 'Pago' WHERE id = %s", (id_pagar,))
            conn.commit()
            st.rerun()
    conn.close()
