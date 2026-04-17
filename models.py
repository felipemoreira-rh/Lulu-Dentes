"""Database schema and CRUD helpers for the Lulu Dentes Streamlit app.

Defines three models backed by MySQL tables:
- Paciente: patient record with contact info
- Agenda: scheduled appointments linked to a Paciente
- Financeiro: financial entries (receitas/despesas) optionally linked to a Paciente

This module replaces the previous Flask-SQLAlchemy ORM definitions with
lightweight SQL helpers that are used directly by the Streamlit app.
"""

from datetime import datetime
from typing import Any, Iterable, Optional


# --- SCHEMA ---------------------------------------------------------------

CREATE_PACIENTE_SQL = """
CREATE TABLE IF NOT EXISTS paciente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(100),
    data_nascimento DATE,
    observacoes TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_AGENDA_SQL = """
CREATE TABLE IF NOT EXISTS agenda (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NOT NULL,
    procedimento VARCHAR(100),
    data_hora DATETIME NOT NULL,
    valor DECIMAL(10,2) DEFAULT 0,
    status_pagamento VARCHAR(20) DEFAULT 'Pendente',
    observacoes TEXT,
    FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE CASCADE
)
"""

CREATE_FINANCEIRO_SQL = """
CREATE TABLE IF NOT EXISTS financeiro (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paciente_id INT NULL,
    descricao VARCHAR(200),
    valor DECIMAL(10,2) NOT NULL,
    tipo VARCHAR(20) DEFAULT 'Receita',
    status VARCHAR(20) DEFAULT 'Pendente',
    data_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paciente_id) REFERENCES paciente(id) ON DELETE SET NULL
)
"""


def init_schema(conn) -> None:
    """Create all tables if they don't exist."""
    cursor = conn.cursor()
    cursor.execute(CREATE_PACIENTE_SQL)
    cursor.execute(CREATE_AGENDA_SQL)
    cursor.execute(CREATE_FINANCEIRO_SQL)
    conn.commit()
    cursor.close()


# --- PACIENTE CRUD --------------------------------------------------------

def insert_paciente(
    conn,
    nome: str,
    cpf: str,
    telefone: str,
    email: str,
    data_nascimento: Optional[Any] = None,
    observacoes: str = "",
) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO paciente (nome, cpf, telefone, email, data_nascimento, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (nome, cpf, telefone, email, data_nascimento, observacoes),
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    return new_id


def update_paciente(
    conn,
    paciente_id: int,
    nome: str,
    cpf: str,
    telefone: str,
    email: str,
    data_nascimento: Optional[Any] = None,
    observacoes: str = "",
) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE paciente
        SET nome = %s,
            cpf = %s,
            telefone = %s,
            email = %s,
            data_nascimento = %s,
            observacoes = %s
        WHERE id = %s
        """,
        (nome, cpf, telefone, email, data_nascimento, observacoes, paciente_id),
    )
    conn.commit()
    cursor.close()


def delete_paciente(conn, paciente_id: int) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM paciente WHERE id = %s", (paciente_id,))
    conn.commit()
    cursor.close()


def list_pacientes(conn) -> Iterable[dict]:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM paciente ORDER BY nome")
    rows = cursor.fetchall()
    cursor.close()
    return rows


# --- AGENDA CRUD ----------------------------------------------------------

def insert_agenda(
    conn,
    paciente_id: int,
    procedimento: str,
    data_hora: datetime,
    valor: float,
    observacoes: str = "",
) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO agenda (paciente_id, procedimento, data_hora, valor, observacoes)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (paciente_id, procedimento, data_hora, valor, observacoes),
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    return new_id


def update_agenda_status(conn, agenda_id: int, status: str) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE agenda SET status_pagamento = %s WHERE id = %s",
        (status, agenda_id),
    )
    conn.commit()
    cursor.close()


def delete_agenda(conn, agenda_id: int) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agenda WHERE id = %s", (agenda_id,))
    conn.commit()
    cursor.close()


# --- FINANCEIRO CRUD ------------------------------------------------------

def insert_financeiro(
    conn,
    descricao: str,
    valor: float,
    tipo: str,
    status: str,
    paciente_id: Optional[int] = None,
) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO financeiro (paciente_id, descricao, valor, tipo, status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (paciente_id, descricao, valor, tipo, status),
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    return new_id


def update_financeiro_status(conn, financeiro_id: int, status: str) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE financeiro SET status = %s WHERE id = %s",
        (status, financeiro_id),
    )
    conn.commit()
    cursor.close()


def delete_financeiro(conn, financeiro_id: int) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM financeiro WHERE id = %s", (financeiro_id,))
    conn.commit()
    cursor.close()
