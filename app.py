# app.py - LISTA DE FUNCIONÁRIOS: CHECKBOX ALINHADO + ESTILO PROFISSIONAL
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

st.title("FSJ Logística - Gerenciador de Lavagens")

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

if not st.session_state.logado:
    st.subheader("Faça Login")
    col1, col2 = st.columns(2)
    email = col1.text_input("E-mail", placeholder="admin@fsj.com")
    senha = col2.text_input("Senha", type="password", placeholder="fsj123")
    if st.button("Entrar", use_container_width=True):
        user = validar_login(email, senha)
        if user:
            st.session_state.logado = True
            st.session_state.usuario, st.session_state.nivel = user
            st.success(f"Bem-vindo, {user[0]}!")
            st.rerun()
        else:
            st.error("E-mail ou senha incorretos.")
    st.info("**Dica**: admin@fsj.com / fsj123")
else:
    st.sidebar.success(f"Logado como: {st.session_state.usuario}")
    st.sidebar.button("Sair", on_click=lambda: (setattr(st.session_state, 'logado', False), st.rerun()))

    opcoes = ["Emitir Nova Ordem", "Ver Histórico"]
    if st.session_state.nivel == "admin":
        opcoes.extend(["Cadastrar Novo Usuário", "Histórico de Cadastro de Funcionários"])
    opcao = st.sidebar.selectbox("Escolha uma opção:", opcoes)

    if opcao == "Emitir Nova Ordem":
        st.header("Emitir Ordem de Lavagem")
        with st.form("nova_ordem", clear_on_submit=True):
            col1, col2 = st.columns(2)
            placa = col1.text_input("**Placa** (obrigatório)").upper()
            motorista = col2.text_input("Motorista")
            operacao = st.text_input("Operação", placeholder="Ex: Carga/Descarga")
            col5, col6 = st.columns(2)
            hora_inicio = col5.time_input("Hora Início")
            hora_fim = col6.time_input("Hora Fim")
            obs = st.text_area("Observações")
            if st.form_submit_button("Emitir Ordem"):
                if placa:
                    ordem = emitir_ordem(placa, motorista or "Não informado", operacao or "Geral",
                                       str(hora_inicio), str(hora_fim), obs, st.session_state.usuario)
                    st.success(f"Ordem emitida: **{ordem}**")
                else:
                    st.error("Placa obrigatória!")

    elif opcao == "Ver Histórico":
        st.header("Histórico de Lavagens")
        df = listar_lavagens()
        if not df.empty:
            for _, row in df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 1])
                    col1.metric("Ordem", row['numero_ordem'])
                    col2.write(f"**{row['placa']}** | {row['motorista']} | {row['operacao']}")
                    status = col3.selectbox("Status", ["Pendente", "Concluída"], 
                                          index=0 if row['status'] == 'Pendente' else 1,
                                          key=f"st_{row['numero_ordem']}")
                    if status != row['status'] and st.button("Salvar", key=f"sv_{row['numero_ordem']}"):
                        atualizar_status(row['numero_ordem'], status)
                        st.success("Atualizado!")
                        st.rerun()
            st.download_button("Baixar CSV", df.to_csv(index=False), "lavagens.csv")
        else:
            st.info("Nenhuma lavagem ainda.")

    elif opcao == "Cadastrar Novo Usuário" and st.session_state.nivel == "admin":
        st.header("Cadastrar Novo Usuário")
        with st.form("novo_usuario"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            nivel = st.selectbox("Nível", ["operador", "admin"])
            if st.form_submit_button("Criar Usuário"):
                if nome and email and senha:
                    if criar_usuario(nome, email, senha, nivel):
                        st.success(f"Usuário {email} criado com sucesso!")
                    else:
                        st.error("E-mail já existe!")
                else:
                    st.error("Preencha todos os campos!")

    elif opcao == "Histórico de Cadastro de Funcionários" and st.session_state.nivel == "admin":
        st.header("Lista de Funcionários")

        # Botões no topo
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            btn_senha = st.button("Alterar Senha", key="btn_senha", disabled=True)
        with col_btn2:
            btn_nivel = st.button("Alterar Nível", key="btn_nivel", disabled=True)

        df = listar_usuarios()
        if df.empty:
            st.info("Nenhum funcionário cadastrado ainda.")
        else:
            # Estado para seleção
            if 'selected_id' not in st.session_state:
                st.session_state.selected_id = None

            # Tabela com colunas fixas
            st.write("### ")
            for _, row in df.iterrows():
                cols = st.columns([0.6, 2.8, 3.2, 2.2, 1.6, 1.4])
                
                # Checkbox alinhado
                checked = cols[0].checkbox("", key=f"chk_{row['id']}", 
                                         value=(st.session_state.selected_id == row['id']))

                # Destacar linha
                bg_color = "#e6f7ff" if checked else "white"
                border = "1px solid #ddd" if checked else "1px solid #eee"
                
                with st.container():
                    st.markdown(f"""
                    <div style="
                        display: flex; 
                        align-items: center; 
                        padding: 10px; 
                        margin: 2px 0; 
                        background-color: {bg_color};
                        border: {border};
                        border-radius: 8px;
                        font-size: 14px;
                    ">
                        <div style="flex: 0.6; text-align: center;">&nbsp;</div>
                        <div style="flex: 2.8; font-weight: bold;">{row['nome']}</div>
                        <div style="flex: 3.2; color: #555;">{row['email']}</div>
                        <div style="flex: 2.2; color: #777;">{row['data_cadastro']}</div>
                        <div style="flex: 1.6; color: #d4380d;">{row['senha']}</div>
                        <div style="flex: 1.4; font-weight: bold; color: #089e60;">{row['nivel'].title()}</div>
                    </div>
                    """, unsafe_allow_html=True)

                if checked:
                    st.session_state.selected_id = row['id']
                    st.session_state.selected_row = row
                    # Habilitar botões
                    st.rerun()
                elif st.session_state.selected_id == row['id']:
                    st.session_state.selected_id = None
                    st.rerun()

            # Habilitar botões
            if st.session_state.selected_id:
                st.session_state.btn_senha = True
                st.session_state.btn_nivel = True
            else:
                st.session_state.btn_senha = False
                st.session_state.btn_nivel = False

            # Re-render botões
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("Alterar Senha", disabled=not getattr(st.session_state, 'btn_senha', False)):
                    user = st.session_state.selected_row
                    with st.form("form_senha"):
                        st.write(f"**Alterar senha de:** {user['nome']}")
                        nova_senha = st.text_input("Nova Senha", type="password")
                        if st.form_submit_button("Salvar"):
                            if nova_senha:
                                alterar_senha(user['email'], nova_senha)
                                st.success("Senha atualizada!")
                                st.rerun()
                            else:
                                st.error("Digite uma senha!")
            with col_btn2:
                if st.button("Alterar Nível", disabled=not getattr(st.session_state, 'btn_nivel', False)):
                    user = st.session_state.selected_row
                    with st.form("form_nivel"):
                        st.write(f"**Alterar nível de:** {user['nome']}")
                        novo_nivel = st.selectbox("Nível", ["operador", "admin"], 
                                                index=0 if user['nivel'] == 'operador' else 1)
                        if st.form_submit_button("Salvar"):
                            alterar_nivel(user['email'], novo_nivel)
                            st.success("Nível atualizado!")
                            st.rerun()

            st.download_button(
                "Baixar Lista (CSV)",
                df[['nome', 'email', 'senha', 'nivel', 'data_cadastro']].to_csv(index=False).encode('utf-8'),
                "funcionarios.csv",
                "text/csv"
            )

st.markdown("---")
st.markdown("*FSJ Logística - Sistema por Grok*")
