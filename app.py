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
    {% extends "base.html" %}
{% block content %}
<div class="container-fluid mt-4">
    <h1 class="mb-4">Dashboard - Lulu Dentes 🦷</h1>
    
    <div class="row">
        <div class="col-md-4">
            <div class="card text-white bg-success mb-3 shadow">
                <div class="card-body">
                    <h5 class="card-title">Receita Total (Paga)</h5>
                    <h2 class="card-text">R$ {{ "%.2f"|format(total_recebido) }}</h2>
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card text-white bg-primary mb-3 shadow">
                <div class="card-body">
                    <h5 class="card-title">Consultas para Hoje</h5>
                    <h2 class="card-text">{{ total_consultas_hoje }}</h2>
                </div>
            </div>
        </div>
    </div>

    <hr>

    <div class="row mt-4">
        <div class="col-md-12">
            <h3>Próximos Atendimentos</h3>
            <table class="table table-hover bg-white shadow-sm">
                <thead class="thead-dark">
                    <tr>
                        <th>Paciente</th>
                        <th>Procedimento</th>
                        <th>Data/Hora</th>
                    </tr>
                </thead>
                <tbody>
                    {% for consulta in consultas %}
                    <tr>
                        <td>{{ consulta.paciente.nome }}</td>
                        <td>{{ consulta.procedimento }}</td>
                        <td>{{ consulta.data_hora.strftime('%d/%m/%Y %H:%M') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
                     
