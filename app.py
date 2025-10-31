# app.py - MENU LATERAL MODERNO + ANIMAÇÕES SUAVES
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# Configuração da página
st.set_page_config(page_title="FSJ Lavagens", layout="wide")

# CSS para animações suaves
st.markdown("""
<style>
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .menu-item {
        padding: 10px 15px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .menu-item:hover {
        background-color: #e3f2fd;
        transform: translateX(5px);
    }
    .menu-item.active {
        background-color: #bbdefb;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .submenu {
        margin-left: 20px;
        overflow: hidden;
        transition: max-height 0.4s ease, opacity 0.4s ease;
    }
    .submenu.collapsed {
        max-height: 0;
        opacity: 0;
    }
    .submenu.expanded {
        max-height: 200px;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Banco de dados
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

# Funções do sistema
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

# Estado da página
if 'pagina' not in st.session_state:
    st.session_state.pagina = "login"
if 'lavagem_expandido' not in st.session_state:
    st.session_state.lavagem_expandido = True
if 'usuarios_expandido' not in st.session_state:
    st.session_state.usuarios_expandido = False

# Login
if st.session_state.pagina == "login":
    st.title("FSJ Logística - Gerenciador de Lavagens")
    st.subheader("Faça Login")
    col1, col2 = st.columns(2)
    email = col1.text_input("E-mail", placeholder="admin@fsj.com")
    senha = col2.text_input("Senha", type="password", placeholder="fsj123")
    if st.button("Entrar", use_container_width=True):
        user = validar_login(email, senha)
        if user:
            st.session_state.logado = True
            st.session_state.usuario, st.session_state.nivel = user
            st.session_state.pagina = "emitir_ordem"
            st.success(f"Bem-vindo, {user[0]}!")
            st.rerun()
        else:
            st.error("E-mail ou senha incorretos.")
    st.info("**Dica**: admin@fsj.com / fsj123")

else:
    # MENU LATERAL MODERNO
    with st.sidebar:
        st.success(f"Logado como: **{st.session_state.usuario}**")
        st.button("Sair", on_click=sair, use_container_width=True)
        
        st.markdown("---")
        
        # LAVAGEM
        col_lav, _ = st.columns([0.9, 0.1])
        with col_lav:
            if st.button("Lavagem", key="btn_lavagem", use_container_width=True):
                st.session_state.lavagem_expandido = not st.session_state.lavagem_expandido
        
        submenu_class = "submenu expanded" if st.session_state.lavagem_expandido else "submenu collapsed"
        st.markdown(f'<div class="{submenu_class}">', unsafe_allow_html=True)
        
        op1 = st.button("Emitir Ordem de Lavagem", key="emitir_ordem", use_container_width=True)
        op2 = st.button("Pesquisa de Lavagens", key="pesquisa_lavagens", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # USUÁRIOS (só admin)
        if st.session_state.nivel == "admin":
            col_usr, _ = st.columns([0.9, 0.1])
            with col_usr:
                if st.button("Usuários", key="btn_usuarios", use_container_width=True):
                    st.session_state.usuarios_expandido = not st.session_state.usuarios_expandido
            
            submenu_usr_class = "submenu expanded" if st.session_state.usuarios_expandido else "submenu collapsed"
            st.markdown(f'<div class="{submenu_usr_class}">', unsafe_allow_html=True)
            
            op3 = st.button("Cadastro", key="cadastro_usuario", use_container_width=True)
            op4 = st.button("Pesquisa", key="pesquisa_usuarios", use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    # Redirecionamento
    if op1:
        st.session_state.pagina = "emitir_ordem"
        st.rerun()
    if op2:
        st.session_state.pagina = "pesquisa_lavagens"
        st.rerun()
    if op3:
        st.session_state.pagina = "cadastro_usuario"
        st.rerun()
    if op4:
        st.session_state.pagina = "pesquisa_usuarios"
        st.rerun()

    # PÁGINAS
    if st.session_state.pagina == "emitir_ordem":
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

    elif st.session_state.pagina == "pesquisa_lavagens":
        st.header("Pesquisa de Lavagens")
        df = listar_lavagens()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button("Baixar CSV", df.to_csv(index=False), "lavagens.csv")
        else:
            st.info("Nenhuma lavagem registrada.")

    elif st.session_state.pagina == "cadastro_usuario":
        st.header("Cadastrar Novo Usuário")
        with st.form("novo_usuario"):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            nivel = st.selectbox("Nível", ["operador", "admin"])
            if st.form_submit_button("Criar Usuário"):
                if nome and email and senha:
                    if criar_usuario(nome, email, senha, nivel):
                        st.success(f"Usuário {email} criado!")
                    else:
                        st.error("E-mail já existe!")
                else:
                    st.error("Preencha todos os campos!")

    elif st.session_state.pagina == "pesquisa_usuarios":
        st.header("Lista de Funcionários")
        df = listar_usuarios()
        if not df.empty:
            st.dataframe(df[['nome', 'email', 'data_cadastro', 'nivel']], use_container_width=True)
            st.download_button("Baixar CSV", df.to_csv(index=False), "funcionarios.csv")
        else:
            st.info("Nenhum usuário cadastrado.")

st.markdown("---")
st.markdown("*FSJ Logística - Sistema por Grok*")
