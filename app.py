# app.py - TABELA DE VEÍCULOS COM ÍCONES DE AÇÃO (EDITAR/EXCLUIR)
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import re

st.set_page_config(page_title="FSJ Lavagens", layout="wide")

# CSS MODERNO E PROFISSIONAL
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
    .action-btn {
        font-size: 11px !important;
        padding: 4px 8px !important;
        margin: 0 2px !important;
    }
    .action-btn-edit {
        background-color: #e3f2fd !important;
        color: #1976d2 !important;
    }
    .action-btn-delete {
        background-color: #ffebee !important;
        color: #d32f2f !important;
    }
    .stButton > button {
        border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

# BANCO DE DADOS
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
    c.execute('''CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT UNIQUE NOT NULL,
        tipo TEXT NOT NULL,
        modelo_marca TEXT,
        data_cadastro TEXT
    )''')
    c.execute('INSERT OR IGNORE INTO usuarios (nome, email, senha, nivel, data_cadastro) VALUES (?, ?, ?, ?, ?)',
              ('Admin FSJ', 'admin@fsj.com', 'fsj123', 'admin', datetime.now().strftime('%d/%m/%Y %H:%M')))
    conn.commit()
    conn.close()

init_db()

# FUNÇÕES USUÁRIOS
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

# FUNÇÕES VEÍCULOS
def criar_veiculo(placa, tipo, modelo_marca):
    placa = placa.upper().replace("-", "").replace(" ", "")
    if len(placa) != 7 or not re.match(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$", placa):
        return False
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    data_cad = datetime.now().strftime('%d/%m/%Y %H:%M')
    try:
        c.execute('INSERT INTO veiculos (placa, tipo, modelo_marca, data_cadastro) VALUES (?, ?, ?, ?)',
                  (placa, tipo, modelo_marca, data_cad))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def editar_veiculo(id_veiculo, placa, tipo, modelo_marca):
    placa = placa.upper().replace("-", "").replace(" ", "")
    if len(placa) != 7 or not re.match(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$", placa):
        return False
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    try:
        c.execute('UPDATE veiculos SET placa = ?, tipo = ?, modelo_marca = ? WHERE id = ?',
                  (placa, tipo, modelo_marca, id_veiculo))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def excluir_veiculo(id_veiculo):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('DELETE FROM veiculos WHERE id = ?', (id_veiculo,))
    conn.commit()
    conn.close()

def listar_veiculos():
    conn = sqlite3.connect('fsj_lavagens.db')
    df = pd.read_sql_query('SELECT id, placa, tipo, modelo_marca, data_cadastro FROM veiculos ORDER BY data_cadastro DESC', conn)
    conn.close()
    return df

# FUNÇÕES LAVAGENS
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

# ESTADO
if 'pagina' not in st.session_state:
    st.session_state.pagina = "login"
if 'lavagem_expandido' not in st.session_state:
    st.session_state.lavagem_expandido = True
if 'usuarios_expandido' not in st.session_state:
    st.session_state.usuarios_expandido = True
if 'veiculos_expandido' not in st.session_state:
    st.session_state.veiculos_expandido = True
if 'editando_veiculo' not in st.session_state:
    st.session_state.editando_veiculo = None
if 'confirmar_exclusao_veiculo' not in st.session_state:
    st.session_state.confirmar_exclusao_veiculo = None

# LOGIN
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

        # LAVAGEM
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

        # USUÁRIOS (ADMIN)
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

        # VEÍCULOS (ADMIN)
        if st.session_state.nivel == "admin":
            st.markdown('<div class="menu-title">Veículos</div>', unsafe_allow_html=True)
            submenu_veic = "submenu expanded" if st.session_state.veiculos_expandido else "submenu collapsed"
            st.markdown(f'<div class="{submenu_veic}">', unsafe_allow_html=True)
            if st.button("Cadastro", key="btn_cadastro_veic", use_container_width=True):
                st.session_state.pagina = "cadastro_veiculo"
                st.rerun()
            if st.button("Pesquisa", key="btn_pesquisa_veic", use_container_width=True):
                st.session_state.pagina = "pesquisa_veiculos"
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
            st.dataframe(df[['nome', 'email', 'data_cadastro', 'nivel']], use_container_width=True)
            st.download_button("Baixar CSV", df.to_csv(index=False), "funcionarios.csv")
        else:
            st.info("Nenhum usuário cadastrado.")

    # CADASTRO DE VEÍCULO
    elif st.session_state.pagina == "cadastro_veiculo":
        st.header("Cadastrar Veículo")
        with st.form("novo_veiculo"):
            placa = st.text_input("**PLACA** (7 caracteres: ABC1D23)", max_chars=7).upper()
            tipo = st.selectbox("TIPO", [
                "Cavalo", "Reboque", "Reboque Bitrem", "Carreta", "Prancha", 
                "Reboque Refrig.", "Cavalo Bitrem", "VUC", "Truck", "Toco", "Passeio"
            ])
            modelo_marca = st.text_input("MODELO/MARCA", max_chars=30)
            if st.form_submit_button("Cadastrar Veículo"):
                if len(placa) == 7 and re.match(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$", placa):
                    if criar_veiculo(placa, tipo, modelo_marca):
                        st.success(f"Veículo **{placa}** cadastrado!")
                    else:
                        st.error("Placa já cadastrada!")
                else:
                    st.error("Placa inválida! Use: ABC1D23")

    # PESQUISA DE VEÍCULOS COM ÍCONES
    elif st.session_state.pagina == "pesquisa_veiculos":
        st.header("Pesquisa de Veículos")
        df = listar_veiculos()
        if not df.empty:
            # Cabeçalho
            header_cols = st.columns([2, 2.5, 2.5, 2, 1.5])
            header_cols[0].write("**Placa**")
            header_cols[1].write("**Tipo**")
            header_cols[2].write("**Modelo/Marca**")
            header_cols[3].write("**Data Cadastro**")
            header_cols[4].write("**Ações**")

            st.markdown("---")

            # Linhas
            for _, row in df.iterrows():
                cols = st.columns([2, 2.5, 2.5, 2, 1.5])
                cols[0].write(row['placa'])
                cols[1].write(row['tipo'])
                cols[2].write(row['modelo_marca'] or "-")
                cols[3].write(row['data_cadastro'])
                
                with cols[4]:
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("Editar", key=f"edit_{row['id']}", help="Editar veículo"):
                            st.session_state.editando_veiculo = row['id']
                            st.rerun()
                    with col_del:
                        if st.button("Excluir", key=f"del_{row['id']}", help="Excluir veículo"):
                            if st.session_state.get('confirmar_exclusao_veiculo') == row['id']:
                                excluir_veiculo(row['id'])
                                st.success("Veículo excluído!")
                                if 'confirmar_exclusao_veiculo' in st.session_state:
                                    del st.session_state.confirmar_exclusao_veiculo
                                st.rerun()
                            else:
                                st.session_state.confirmar_exclusao_veiculo = row['id']
                                st.warning("Clique novamente para confirmar.")
                                st.rerun()

            # FORMULÁRIO DE EDIÇÃO
            if st.session_state.editando_veiculo is not None:
                veic_df = df[df['id'] == st.session_state.editando_veiculo]
                if not veic_df.empty:
                    veic = veic_df.iloc[0]
                    st.markdown("---")
                    st.subheader(f"Editando Veículo: {veic['placa']}")
                    with st.form("editar_veiculo"):
                        nova_placa = st.text_input("PLACA", value=veic['placa'], max_chars=7).upper()
                        novo_tipo = st.selectbox("TIPO", [
                            "Cavalo", "Reboque", "Reboque Bitrem", "Carreta", "Prancha", 
                            "Reboque Refrig.", "Cavalo Bitrem", "VUC", "Truck", "Toco", "Passeio"
                        ], index=[
                            "Cavalo", "Reboque", "Reboque Bitrem", "Carreta", "Prancha", 
                            "Reboque Refrig.", "Cavalo Bitrem", "VUC", "Truck", "Toco", "Passeio"
                        ].index(veic['tipo']))
                        novo_modelo = st.text_input("MODELO/MARCA", value=veic['modelo_marca'] or "", max_chars=30)
                        
                        col1, col2 = st.columns(2)
                        if col1.form_submit_button("Salvar"):
                            if len(nova_placa) == 7 and re.match(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$", nova_placa):
                                if editar_veiculo(st.session_state.editando_veiculo, nova_placa, novo_tipo, novo_modelo):
                                    st.success("Veículo atualizado!")
                                    del st.session_state.editando_veiculo
                                    st.rerun()
                                else:
                                    st.error("Placa já existe!")
                            else:
                                st.error("Placa inválida!")
                        
                        if col2.form_submit_button("Cancelar"):
                            del st.session_state.editando_veiculo
                            st.rerun()

            # DOWNLOAD
            df_display = df[['placa', 'tipo', 'modelo_marca', 'data_cadastro']].copy()
            st.download_button("Baixar CSV", df_display.to_csv(index=False).encode('utf-8'), "veiculos.csv", "text/csv")
        else:
            st.info("Nenhum veículo cadastrado.")

st.markdown("---")
st.markdown("*FSJ Logística - Sistema por Grok*")
