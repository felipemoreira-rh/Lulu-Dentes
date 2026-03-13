from flask import Flask, render_template, request, redirect, url_for
from models import db, Paciente, Agenda, Financeiro
from datetime import datetime

app = Flask(__name__)

# CONFIGURAÇÃO DO MYSQL (Ajusta com os teus dados)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:SUA_SENHA@localhost/lulu_dentes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Rota 1: Dashboard (Visão Geral)
@app.route('/')
def dashboard():
    total_recebido = db.session.query(db.func.sum(Financeiro.valor)).filter_by(status='Pago').scalar() or 0
    total_pendente = db.session.query(db.func.sum(Financeiro.valor)).filter_by(status='Pendente').scalar() or 0
    consultas = Agenda.query.order_by(Agenda.data_hora.asc()).all()
    pacientes = Paciente.query.all()
    return render_template('dashboard.html', total=total_recebido, pendente=total_pendente, consultas=consultas, pacientes=pacientes)

# Rota 2: Novo Agendamento (INTEGRADO com Financeiro)
@app.route('/agendar', methods=['POST'])
def agendar():
    paciente_id = request.form.get('paciente_id')
    procedimento = request.form.get('procedimento')
    data_str = request.form.get('data_hora')
    valor = float(request.form.get('valor'))

    # Converter string para objeto datetime
    data_dt = datetime.strptime(data_str, '%Y-%m-%dT%H:%M')

    # 1. Cria o agendamento
    nova_consulta = Agenda(data_hora=data_dt, procedimento=procedimento, paciente_id=paciente_id)
    
    # 2. Cria automaticamente o lançamento financeiro pendente
    novo_lancamento = Financeiro(valor=valor, status='Pendente', paciente_id=paciente_id)

    db.session.add(nova_consulta)
    db.session.add(novo_lancamento)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

# Inicialização do Banco (Executa apenas uma vez)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
