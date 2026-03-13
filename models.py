from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True)
    telefone = db.Column(db.String(20))
    # Relacionamentos
    agendamentos = db.relationship('Agenda', backref='paciente', lazy=True)
    financeiro = db.relationship('Financeiro', backref='paciente', lazy=True)

class Agenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False)
    procedimento = db.Column(db.String(100))
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'))

class Financeiro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), default='Receita') 
    status = db.Column(db.String(20), default='Pendente') # Pendente ou Pago
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'))
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
