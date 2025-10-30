# app.py - FSJ CORRIGIDO (SEM ERRO DE SESSION STATE)
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="FSJ Lavagens", layout="wide")

def init_db():
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nivel TEXT DEFAULT 'operador',
        data_cadastro TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS lavagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_ordem TEXT UNIQUE,
        placa TEXT NOT NULL,
        motorista TEXT,
        operacao TEXT,
        data TEXT,
        hora_inicio TEXT,
        hora_fim TEXT,
        status TEXT DEFAULT 'Pendente',
        observacoes TEXT,
        usuario_criacao TEXT
    )''')
    c.execute('INSERT OR IGNORE INTO usuarios (nome, email, senha, nivel, data_cadastro) VALUES (?, ?, ?, ?, ?)',
              ('Admin FSJ', 'admin@fsj.com', 'fsj123', 'admin', datetime.now().strftime('%d/%m/%Y %H:%M')))
    conn.commit()
    conn.close()

init_db()

def criar_usuario(nome, email, senha, nivel):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    data_cad = datetime.now().strftime('%d/%m/%Y %H:%M')
    try:
        c.execute('INSERT INTO usuarios (nome, email, senha, nivel, data_cadastro) VALUES (?, ?, ?, ?, ?)',
                  (nome, email, senha, nivel, data_cad))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def validar_login(email, senha):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('SELECT nome, nivel FROM usuarios WHERE email = ? AND senha = ?', (email, senha))
    resultado = c.fetchone()
    conn.close()
    return resultado

def listar_usuarios():
    conn = sqlite3.connect('fsj_lavagens.db')
    df = pd.read_sql_query('SELECT id, nome, email, senha, nivel, data_cadastro FROM usuarios ORDER BY data_cadastro DESC', conn)
    conn.close()
    return df

def alterar_senha(email, nova_senha):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('UPDATE usuarios SET senha = ? WHERE email = ?', (nova_senha, email))
    conn.commit()
    conn.close()

def alterar_nivel(email, novo_nivel):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('UPDATE usuarios SET nivel = ? WHERE email = ?', (novo_nivel, email))
    conn.commit()
    conn.close()

def emitir_ordem(placa, motorista, operacao, hora_inicio, hora_fim, obs, usuario):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) FROM lavagens WHERE data = ?', (data_hoje,))
    contador = c.fetchone()[0] + 1
    numero_ordem = f"ORD-{data_hoje.replace('-','')}-{contador:03d}"
    c.execute('''INSERT INTO lavagens 
    (numero_ordem, placa, motorista, operacao, data, hora_inicio, hora_fim, observacoes, status, usuario_criacao)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendente', ?)''',
    (numero_ordem, placa.upper(), motorista, operacao, data_hoje, hora_inicio, hora_fim, obs, usuario))
    conn.commit()
    conn.close()
    return numero_ordem

def listar_lavagens():
    conn = sqlite3.connect('fsj_lavagens.db')
    df = pd.read_sql_query('SELECT numero_ordem, placa, motorista, operacao, data, hora_inicio, hora_fim, status, observacoes FROM lavagens ORDER BY data DESC', conn)
    conn.close()
    return df

def atualizar_status(ordem, status):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('UPDATE lavagens SET status = ? WHERE numero_ordem = ?', (status, ordem))
    conn.commit()
    conn.close()

def sair():
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""
    st.rerun()

st.title("🚛 FSJ Logística - Gerenciador de Lavagens")

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

if not st.session_state.logado:
    st.subheader("🔐 Faça Login")
    col1, col2 = st.columns(2)
    email = col1.text_input("E-mail", placeholder="admin@fsj.com")
    senha = col2.text_input("Senha", type="password", placeholder="fsj123")
    if st.button("Entrar", use_container_width=True):
        user = validar_login(email, senha)
        if user:
            st.session_state.logado = True
            st.session_state.usuario, st.session_state.nivel = user
            st.success(f"Bem-vindo, {user[0]}! 🎉")
            st.rerun()
        else:
            st.error("❌ E-mail ou senha incorretos. Tente: admin@fsj.com / fsj123")

    st.info("👆 **Dica**: Use admin@fsj.com / fsj123 para o primeiro acesso. Mude depois!")

else:
    # Menu lateral
    st.sidebar.success(f"👤 Logado como: {st.session_state.usuario}")
    st.sidebar.button("🚪 Sair", on_click=sair)
    
    opcao = st.sidebar.selectbox("📋 Escolha uma opção:", ["Emitir Nova Ordem", "Ver Histórico"])
    if st.session_state.nivel == "admin":
        opcao = st.sidebar.selectbox("📋 Escolha uma opção:", ["Emitir Nova Ordem", "Ver Histórico", "Cadastrar Novo Usuário", "Histórico de Cadastro de Funcionários"])

    if opcao == "Emitir Nova Ordem":
        st.header("📄 Emitir Ordem de Lavagem")
        with st.form("nova_ordem", clear_on_submit=True):
            col1, col2 = st.columns(2)
            placa = col1.text_input("**Placa do Caminhão** (obrigatório)", placeholder="ABC-1234").upper()
            motorista = col2.text_input("Motorista")
            operacao = st.text_input("Operação", placeholder="Ex: Carga/Descarga")
            col5, col6 = st.columns(2)
            hora_inicio = col5.time_input("Hora Início")
            hora_fim = col6.time_input("Hora Fim")
            obs = st.text_area("Observações")
            if st.form_submit_button("🚀 Emitir Ordem", use_container_width=True):
                if placa:
                    ordem_num = emitir_ordem(placa, motorista or "Não informado", operacao or "Geral",
                                             str(hora_inicio) if hora_inicio else "", str(hora_fim) if hora_fim else "", obs, st.session_state.usuario)
                    st.balloons()
                    st.success(f"✅ Ordem emitida: **{ordem_num}**")
                else:
                    st.error("❌ Placa obrigatória!")

    elif opcao == "Ver Histórico":
        st.header("📊 Histórico de Lavagens")
        col_f1, col_f2, col_f3 = st.columns(3)
        filtro_placa = col_f1.text_input("🔍 Filtrar por Placa")
        filtro_motorista = col_f2.text_input("🔍 Filtrar por Motorista")
        filtro_status = col_f3.selectbox("Status", ["Todos", "Pendente", "Concluída"])
        df = listar_lavagens()
        if filtro_placa:
            df = df[df['placa'].str.contains(filtro_placa.upper(), na=False)]
        if filtro_motorista:
            df = df[df['motorista'].str.contains(filtro_motorista, case=False, na=False)]
        if filtro_status != "Todos":
            df = df[df['status'] == filtro_status]
        if not df.empty:
            st.subheader(f"🗂️ {len(df)} registro(s) encontrado(s)")
            st.dataframe(df[['numero_ordem', 'placa', 'motorista', 'data', 'status']], use_container_width=True)
            csv = df.to_csv(index=False)
            st.download_button("📥 Baixar CSV", csv, "historico.csv", "text/csv")
        else:
            st.info("Nenhuma lavagem registrada.")

    elif opcao == "Cadastrar Novo Usuário" and st.session_state.nivel == "admin":
        st.header("👥 Cadastrar Novo Usuário (Apenas Mestre)")
        with st.form("novo_usuario", clear_on_submit=True):
            nome = st.text_input("Nome Completo *")
            email = st.text_input("E-mail *", placeholder="joao@fsj.com")
            senha = st.text_input("Senha *", type="password")
            nivel = st.selectbox("Nível de Acesso", ["operador", "admin"])
            if st.form_submit_button("Criar Usuário"):
                if nome and email and senha:
                    if criar_usuario(nome, email, senha, nivel):
                        st.success(f"✅ Usuário **{email}** criado com sucesso!")
                    else:
                        st.error("❌ E-mail já existe. Tente outro.")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios.")

    elif opcao == "Histórico de Cadastro de Funcionários" and st.session_state.nivel == "admin":
        st.header("Histórico de Cadastro de Funcionários")
        df = listar_usuarios()
        if not df.empty:
            st.subheader(f"🗂️ {len(df)} funcionário(s) cadastrado(s)")
            # Tabela editável para status
            for idx, row in df.iterrows():
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Nome", row['nome'])
                col2.metric("E-mail", row['email'])
                col3.metric("Data", row['data_cadastro'])
                col4.metric("Senha", row['senha'])
                novo_nivel = col5.selectbox("Nível", ["operador", "admin"], 
                                            index=0 if row['nivel'] == 'operador' else 1,
                                            key=f"nivel_{row['id']}")
                if novo_nivel != row['nivel'] and st.button("Atualizar", key=f"atualizar_{row['id']}"):
                    alterar_nivel(row['email'], novo_nivel)
                    st.success("Nível atualizado!")
                    st.rerun()
            # Botão exportar
            csv = df.to_csv(index=False)
            st.download_button("📥 Baixar como Excel/CSV", csv, "historico_funcionarios.csv", "text/csv")
        else:
            st.info("Nenhum funcionário cadastrado ainda.")

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido para FSJ Logística por Grok (xAI). Qualquer dúvida, pergunte aqui!*")
