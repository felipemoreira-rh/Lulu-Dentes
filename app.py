import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date

from models import (
    init_schema,
    insert_paciente,
    update_paciente,
    delete_paciente,
    insert_agenda,
    update_agenda_status,
    delete_agenda,
    insert_financeiro,
    update_financeiro_status,
    delete_financeiro,
)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Lulu Dentes", page_icon="🦷", layout="wide")

PROCEDIMENTOS = [
    "Avaliação", "Limpeza", "Canal", "Extração",
    "Aparelho", "Clareamento", "Restauração",
]
STATUS_PAGAMENTO = ["Pendente", "Pago", "Cancelado"]
TIPOS_FINANCEIRO = ["Receita", "Despesa"]


# --- FUNÇÃO DE CONEXÃO (Padrão RH App) ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="SUA_SENHA",  # <--- Coloca a tua senha aqui
            database="lulu_dentes",
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Erro de Conexão: {err}")
        return None


# --- INICIALIZAÇÃO DO BANCO ---
def init_db():
    conn = get_db_connection()
    if conn:
        init_schema(conn)
        conn.close()


def load_pacientes_df() -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql("SELECT * FROM paciente ORDER BY nome", conn)
    conn.close()
    return df


def load_agenda_df() -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql(
        """
        SELECT a.id, p.nome AS paciente, a.procedimento, a.data_hora,
               a.valor, a.status_pagamento, a.observacoes, a.paciente_id
        FROM agenda a
        LEFT JOIN paciente p ON p.id = a.paciente_id
        ORDER BY a.data_hora DESC
        """,
        conn,
    )
    conn.close()
    return df


def load_financeiro_df() -> pd.DataFrame:
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql(
        """
        SELECT f.id, f.descricao, f.valor, f.tipo, f.status,
               f.data_registro, p.nome AS paciente, f.paciente_id
        FROM financeiro f
        LEFT JOIN paciente p ON p.id = f.paciente_id
        ORDER BY f.data_registro DESC
        """,
        conn,
    )
    conn.close()
    return df


init_db()


# --- INTERFACE ---
st.title("🦷 Lulu Dentes - Gestão Odontológica")

menu = ["Dashboard", "Pacientes", "Agenda", "Financeiro"]
choice = st.sidebar.selectbox("Menu", menu)


# ====================================================================
# DASHBOARD
# ====================================================================
if choice == "Dashboard":
    st.subheader("Painel Geral")

    df_agenda = load_agenda_df()
    df_fin = load_financeiro_df()
    df_pac = load_pacientes_df()

    col1, col2, col3, col4 = st.columns(4)

    total_pacientes = len(df_pac)
    total_atendimentos = len(df_agenda)

    if not df_fin.empty:
        receitas = df_fin[(df_fin["tipo"] == "Receita") & (df_fin["status"] == "Pago")]["valor"].sum()
        a_receber = df_fin[(df_fin["tipo"] == "Receita") & (df_fin["status"] == "Pendente")]["valor"].sum()
    else:
        receitas = 0.0
        a_receber = 0.0

    col1.metric("Pacientes", total_pacientes)
    col2.metric("Atendimentos", total_atendimentos)
    col3.metric("Receita Confirmada", f"R$ {receitas:,.2f}")
    col4.metric("A Receber", f"R$ {a_receber:,.2f}")

    st.divider()
    st.write("### Próximas Consultas")
    if not df_agenda.empty:
        st.dataframe(
            df_agenda[["paciente", "procedimento", "data_hora", "valor", "status_pagamento"]],
            use_container_width=True,
        )
    else:
        st.info("Nenhum agendamento encontrado.")


# ====================================================================
# PACIENTES
# ====================================================================
elif choice == "Pacientes":
    st.subheader("Cadastro de Pacientes")

    tab_novo, tab_lista = st.tabs(["➕ Novo Paciente", "📋 Lista de Pacientes"])

    with tab_novo:
        with st.form("form_paciente", clear_on_submit=True):
            nome = st.text_input("Nome completo *")
            col1, col2 = st.columns(2)
            cpf = col1.text_input("CPF")
            telefone = col2.text_input("Telefone")
            email = st.text_input("E-mail")
            data_nasc = st.date_input(
                "Data de nascimento",
                value=None,
                min_value=date(1900, 1, 1),
                max_value=date.today(),
            )
            observacoes = st.text_area("Observações")

            if st.form_submit_button("Salvar Paciente"):
                if not nome.strip():
                    st.error("O nome é obrigatório.")
                else:
                    conn = get_db_connection()
                    if conn:
                        try:
                            insert_paciente(
                                conn, nome, cpf, telefone, email, data_nasc, observacoes
                            )
                            st.success(f"Paciente {nome} cadastrado com sucesso!")
                        except mysql.connector.Error as err:
                            st.error(f"Erro ao salvar: {err}")
                        finally:
                            conn.close()

    with tab_lista:
        df = load_pacientes_df()
        if df.empty:
            st.info("Nenhum paciente cadastrado.")
        else:
            st.dataframe(
                df[["id", "nome", "cpf", "telefone", "email", "data_nascimento"]],
                use_container_width=True,
            )

            st.divider()
            st.write("#### Editar / Remover Paciente")
            opcoes = {f"{row['id']} - {row['nome']}": int(row["id"]) for _, row in df.iterrows()}
            selecionado = st.selectbox("Selecione um paciente", list(opcoes.keys()))
            paciente_id = opcoes[selecionado]
            registro = df[df["id"] == paciente_id].iloc[0]

            with st.form("form_edit_paciente"):
                nome_e = st.text_input("Nome completo *", value=registro["nome"] or "")
                col1, col2 = st.columns(2)
                cpf_e = col1.text_input("CPF", value=registro["cpf"] or "")
                tel_e = col2.text_input("Telefone", value=registro["telefone"] or "")
                email_e = st.text_input("E-mail", value=registro["email"] or "")
                dn_value = registro["data_nascimento"]
                if isinstance(dn_value, datetime):
                    dn_value = dn_value.date()
                data_nasc_e = st.date_input(
                    "Data de nascimento",
                    value=dn_value if dn_value else None,
                    min_value=date(1900, 1, 1),
                    max_value=date.today(),
                )
                obs_e = st.text_area("Observações", value=registro["observacoes"] or "")

                col_a, col_b = st.columns(2)
                salvar = col_a.form_submit_button("Salvar Alterações")
                remover = col_b.form_submit_button("Remover Paciente", type="secondary")

                if salvar:
                    conn = get_db_connection()
                    if conn:
                        try:
                            update_paciente(
                                conn, paciente_id, nome_e, cpf_e, tel_e, email_e,
                                data_nasc_e, obs_e,
                            )
                            st.success("Paciente atualizado.")
                            st.rerun()
                        except mysql.connector.Error as err:
                            st.error(f"Erro ao atualizar: {err}")
                        finally:
                            conn.close()

                if remover:
                    conn = get_db_connection()
                    if conn:
                        try:
                            delete_paciente(conn, paciente_id)
                            st.success("Paciente removido.")
                            st.rerun()
                        except mysql.connector.Error as err:
                            st.error(f"Erro ao remover: {err}")
                        finally:
                            conn.close()


# ====================================================================
# AGENDA
# ====================================================================
elif choice == "Agenda":
    st.subheader("Agenda de Consultas")

    df_pac = load_pacientes_df()
    if df_pac.empty:
        st.warning("Cadastre um paciente antes de criar agendamentos.")
    else:
        tab_novo, tab_lista = st.tabs(["➕ Novo Agendamento", "📋 Consultas"])

        pacientes_options = {row["nome"]: int(row["id"]) for _, row in df_pac.iterrows()}

        with tab_novo:
            with st.form("form_agenda", clear_on_submit=True):
                paciente_nome = st.selectbox("Paciente", list(pacientes_options.keys()))
                proc = st.selectbox("Procedimento", PROCEDIMENTOS)
                col1, col2 = st.columns(2)
                data = col1.date_input("Data", value=date.today())
                hora = col2.time_input("Hora")
                valor = st.number_input("Valor do Serviço (R$)", min_value=0.0, step=10.0)
                observacoes = st.text_area("Observações")

                if st.form_submit_button("Finalizar Agendamento"):
                    dt_completa = datetime.combine(data, hora)
                    conn = get_db_connection()
                    if conn:
                        try:
                            insert_agenda(
                                conn,
                                pacientes_options[paciente_nome],
                                proc,
                                dt_completa,
                                valor,
                                observacoes,
                            )
                            st.success(
                                f"Consulta para {paciente_nome} agendada em "
                                f"{dt_completa.strftime('%d/%m/%Y %H:%M')}."
                            )
                        except mysql.connector.Error as err:
                            st.error(f"Erro ao agendar: {err}")
                        finally:
                            conn.close()

        with tab_lista:
            df = load_agenda_df()
            if df.empty:
                st.info("Nenhum agendamento encontrado.")
            else:
                st.dataframe(
                    df[["id", "paciente", "procedimento", "data_hora", "valor", "status_pagamento"]],
                    use_container_width=True,
                )

                st.divider()
                st.write("#### Atualizar status ou remover")
                opcoes = {
                    f"{row['id']} - {row['paciente']} ({row['data_hora']})": int(row["id"])
                    for _, row in df.iterrows()
                }
                selecionado = st.selectbox("Selecione um agendamento", list(opcoes.keys()))
                agenda_id = opcoes[selecionado]
                registro = df[df["id"] == agenda_id].iloc[0]

                col_a, col_b = st.columns(2)
                status_atual = registro["status_pagamento"]
                default_index = (
                    STATUS_PAGAMENTO.index(status_atual)
                    if status_atual in STATUS_PAGAMENTO
                    else 0
                )
                novo_status = col_a.selectbox(
                    "Status do pagamento", STATUS_PAGAMENTO, index=default_index
                )
                if col_a.button("Atualizar Status"):
                    conn = get_db_connection()
                    if conn:
                        try:
                            update_agenda_status(conn, agenda_id, novo_status)
                            st.success("Status atualizado.")
                            st.rerun()
                        finally:
                            conn.close()

                if col_b.button("Remover Agendamento", type="secondary"):
                    conn = get_db_connection()
                    if conn:
                        try:
                            delete_agenda(conn, agenda_id)
                            st.success("Agendamento removido.")
                            st.rerun()
                        finally:
                            conn.close()


# ====================================================================
# FINANCEIRO
# ====================================================================
elif choice == "Financeiro":
    st.subheader("Fluxo de Caixa")

    df_pac = load_pacientes_df()
    pacientes_options = {"— Nenhum —": None}
    for _, row in df_pac.iterrows():
        pacientes_options[row["nome"]] = int(row["id"])

    tab_novo, tab_lista = st.tabs(["➕ Novo Lançamento", "📋 Lançamentos"])

    with tab_novo:
        with st.form("form_financeiro", clear_on_submit=True):
            descricao = st.text_input("Descrição *")
            col1, col2 = st.columns(2)
            tipo = col1.selectbox("Tipo", TIPOS_FINANCEIRO)
            status = col2.selectbox("Status", ["Pendente", "Pago"])
            valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            paciente_nome = st.selectbox(
                "Paciente (opcional)", list(pacientes_options.keys())
            )

            if st.form_submit_button("Salvar Lançamento"):
                if not descricao.strip():
                    st.error("A descrição é obrigatória.")
                else:
                    conn = get_db_connection()
                    if conn:
                        try:
                            insert_financeiro(
                                conn,
                                descricao,
                                valor,
                                tipo,
                                status,
                                pacientes_options[paciente_nome],
                            )
                            st.success("Lançamento registrado.")
                        except mysql.connector.Error as err:
                            st.error(f"Erro ao salvar: {err}")
                        finally:
                            conn.close()

    with tab_lista:
        df = load_financeiro_df()
        if df.empty:
            st.info("Nenhum lançamento registrado.")
        else:
            receitas_pagas = df[(df["tipo"] == "Receita") & (df["status"] == "Pago")]["valor"].sum()
            despesas_pagas = df[(df["tipo"] == "Despesa") & (df["status"] == "Pago")]["valor"].sum()
            saldo = receitas_pagas - despesas_pagas

            col1, col2, col3 = st.columns(3)
            col1.metric("Receitas (Pago)", f"R$ {receitas_pagas:,.2f}")
            col2.metric("Despesas (Pago)", f"R$ {despesas_pagas:,.2f}")
            col3.metric("Saldo", f"R$ {saldo:,.2f}")

            st.dataframe(
                df[["id", "descricao", "paciente", "tipo", "status", "valor", "data_registro"]],
                use_container_width=True,
            )

            st.divider()
            st.write("#### Atualizar ou remover")
            opcoes = {
                f"{row['id']} - {row['descricao']} (R$ {float(row['valor']):.2f})": int(row["id"])
                for _, row in df.iterrows()
            }
            selecionado = st.selectbox("Selecione um lançamento", list(opcoes.keys()))
            fin_id = opcoes[selecionado]
            registro = df[df["id"] == fin_id].iloc[0]

            col_a, col_b = st.columns(2)
            novo_status = col_a.selectbox(
                "Status",
                ["Pendente", "Pago"],
                index=0 if registro["status"] != "Pago" else 1,
            )
            if col_a.button("Atualizar Status"):
                conn = get_db_connection()
                if conn:
                    try:
                        update_financeiro_status(conn, fin_id, novo_status)
                        st.success("Status atualizado.")
                        st.rerun()
                    finally:
                        conn.close()

            if col_b.button("Remover Lançamento", type="secondary"):
                conn = get_db_connection()
                if conn:
                    try:
                        delete_financeiro(conn, fin_id)
                        st.success("Lançamento removido.")
                        st.rerun()
                    finally:
                        conn.close()
