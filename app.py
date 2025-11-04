# app.py - MENU 3 PONTINHOS 100% ALINHADO E COMPACTO
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="FSJ Lavagens", layout="wide")

# CSS OTIMIZADO: MENU COMPACTO E ALINHADO
st.markdown("""
<style>
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .menu-title {
        font-weight: bold;
        font-size: 16px;
        padding: 10px 0;
        margin: 15px 0 8px 0;
        color: #1565c0;
    }
    .submenu {
        overflow: hidden;
        transition: max-height 0.4s ease, opacity 0.4s ease;
        margin-left: 10px;
    }
    .submenu.collapsed {
        max-height: 0;
        opacity: 0;
    }
    .submenu.expanded {
        max-height: 300px;
        opacity: 1;
    }
    /* MENU 3 PONTINHOS - COMPACTO E ALINHADO */
    div[data-testid="column"]:last-child {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .action-expander {
        width: 40px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .action-expander > div {
        padding: 0 !important;
    }
    .action-button {
        width: 100% !important;
        text-align: center !important;
        padding: 8px 4px !important;
        margin: 1px 0 !important;
        font-size: 12px !important;
        border-radius: 6px !important;
    }
    .action-button:hover {
        background-color: #e3f2fd !important;
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

# Funções
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

def excluir_usuario(user_id):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
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

def sair():
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""
    st.rerun()

# Estado
if 'pagina' not in st.session_state:
    st.session_state.pagina = "login"
if 'lavagem_expandido' not in st.session_state:
    st.session_state.lavagem_expandido = True
if 'usuarios_expandido' not in st.session_state:
    st.session_state.usuarios_expandido = True
if 'editando' not in st.session_state:
    st.session_state.editando = None
if 'confirmar_exclusao' not in st.session_state:
    st.session_state.confirmar_exclusao = None

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
    # MENU LATERAL
    with st.sidebar:
        st.success(f"Logado como: **{st.session_state.usuario}**")
        st.button("Sair", on_click=sair, use_container_width=True)
        st.markdown("---")

        st.markdown('<div class="menu-title">Lavagem</div>', unsafe_allow_html=True)
        submenu_lav = "submenu expanded" if st.session_state.lavagem_expandido else "submenu collapsed"
        st.markdown(f'<div class="{submenu_lav}">', unsafe_allow_html=True)
        if st.button("Emitir Ordem de Lavagem", key="btn_emitir", use_container_width=True):
            st.session_state.pagina = "emitir_ordem"
            st.rerun()
        if st.button("Pesquisa de Lavagens", key="btn_pesquisa_lav", use_container_width=True):
            st.session_state.pagina = "pesquisa_lavagens"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.nivel == "admin":
            st.markdown('<div class="menu-title">Usuários</div>', unsafe_allow_html=True)
            submenu_usr = "submenu expanded" if st.session_state.usuarios_expandido else "submenu collapsed"
            st.markdown(f'<div class="{submenu_usr}">', unsafe_allow_html=True)
            if st.button("Cadastro", key="btn_cadastro", use_container_width=True):
                st.session_state.pagina = "cadastro_usuario"
                st.rerun()
            if st.button("Pesquisa", key="btn_pesquisa_usr", use_container_width=True):
                st.session_state.pagina = "pesquisa_usuarios"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

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
            for _, row in df.iterrows():
                cols = st.columns([3, 3, 2, 2, 0.5])
                cols[0].write(row['nome'])
                cols[1].write(row['email'])
                cols[2].write(row['data_cadastro'])
                cols[3].write(row['nivel'].title())
                
                with cols[4]:
                    with st.expander("⋮", expanded=False):
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("Alterar", key=f"edit_{row['id']}", use_container_width=True):
                                st.session_state.editando = row['id']
                                st.rerun()
                        with col_btn2:
                            if st.button("Excluir", key=f"del_{row['id']}", type="secondary", use_container_width=True):
                                if st.session_state.get('confirmar_exclusao') == row['id']:
                                    excluir_usuario(row['id'])
                                    st.success("Usuário excluído!")
                                    if 'confirmar_exclusao' in st.session_state:
                                        del st.session_state.confirmar_exclusao
                                    st.rerun()
                                else:
                                    st.session_state.confirmar_exclusao = row['id']
                                    st.warning("Clique novamente para confirmar.")
                                    st.rerun()

            # Formulário de edição
            if st.session_state.editando is not None:
                user_df = df[df['id'] == st.session_state.editando]
                if not user_df.empty:
                    user = user_df.iloc[0]
                    st.markdown("---")
                    st.subheader(f"Editando: {user['nome']}")
                    with st.form("editar_usuario"):
                        novo_nome = st.text_input("Nome Completo", value=user['nome'])
                        novo_email = st.text_input("E-mail", value=user['email'])
                        nova_senha = st.text_input("Nova Senha (deixe em branco para manter)", type="password")
                        novo_nivel = st.selectbox("Nível", ["operador", "admin"], 
                                                index=0 if user['nivel'] == 'operador' else 1)
                        
                        col1, col2 = st.columns(2)
                        if col1.form_submit_button("Salvar"):
                            conn = sqlite3.connect('fsj_lavagens.db')
                            c = conn.cursor()
                            if nova_senha:
                                c.execute('UPDATE usuarios SET nome=?, email=?, senha=?, nivel=? WHERE id=?',
                                          (novo_nome, novo_email, nova_senha, novo_nivel, st.session_state.editando))
                            else:
                                c.execute('UPDATE usuarios SET nome=?, email=?, nivel=? WHERE id=?',
                                          (novo_nome, novo_email, novo_nivel, st.session_state.editando))
                            conn.commit()
                            conn.close()
                            st.success("Usuário atualizado!")
                            del st.session_state.editando
                            st.rerun()
                        
                        if col2.form_submit_button("Cancelar"):
                            del st.session_state.editando
                            st.rerun()

            # Download
            df_display = df[['nome', 'email', 'data_cadastro', 'nivel']].copy()
            st.download_button("Baixar Lista (CSV)", df_display.to_csv(index=False).encode('utf-8'), "funcionarios.csv", "text/csv")
        else:
            st.info("Nenhum usuário cadastrado.")

st.markdown("---")
st.markdown("*FSJ Logística - Sistema por Grok*")
