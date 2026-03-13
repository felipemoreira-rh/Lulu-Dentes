from flask import Flask, render_template, request, redirect
from models import db, Paciente, Agenda, Financeiro

app = Flask(__name__)
# Substitui 'usuario', 'senha' e 'nome_do_banco' pelos teus dados do MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://usuario:senha@localhost/clinica_odonto'
db.init_app(app)

@app.route('/')
def dashboard():
    # Cálculo para o Dashboard Financeiro
    total_recebido = db.session.query(db.func.sum(Financeiro.valor)).filter_by(status='Pago').scalar() or 0
    proximas_consultas = Agenda.query.order_by(Agenda.data_hora).limit(5).all()
    return render_template('dashboard.html', total=total_recebido, consultas=proximas_consultas)

@app.route('/agendar', methods=['POST'])
def agendar():
    # Lógica de integração: Agendamento + Financeiro
    novo_agendamento = Agenda(
        data_hora=request.form['data'],
        procedimento=request.form['servico'],
        paciente_id=request.form['paciente_id']
    )
    # Gera automaticamente um lançamento pendente
    novo_financeiro = Financeiro(
        valor=request.form['valor'],
        tipo='Entrada',
        status='Pendente',
        paciente_id=request.form['paciente_id']
    )
    db.session.add(novo_agendamento)
    db.session.add(novo_financeiro)
    db.session.commit()
    return redirect('/')