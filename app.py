# app.py - FORNECEDORES + TABELA DE PREÇOS + VEÍCULOS
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import re
import io

st.set_page_config(page_title="FSJ Lavagens", layout="wide")

# CSS
st.markdown("""
<style>
    .sidebar .sidebar-content { background-color: #f8f9fa; }
    .menu-title { font-weight: bold; font-size: 16px; padding: 10px 0; margin: 15px 0 8px 0; color: #1565c0; }
    .submenu { overflow: hidden; transition: max-height 0.4s ease, opacity 0.4s ease; margin-left: 10px; }
    .action-btn { font-size: 11px !important; padding: 4px 8px !important; margin: 0 2px !important; }
    .stButton > button { border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# LISTAS GLOBAIS
TIPOS_VEICULO = [
    "TRUCK", "CONJUNTO LS", "REBOQUE", "CAVALO", 
    "CAMINHÃO 3/4", "CONJUNTO BITREM", "PRANCHA"
]

SERVICOS = ["LAVAGEM EXTERNA", "LAVAGEM INTERNA", "LAVAGEM COMPLETA", "POLIMENTO", "DESINFECÇÃO"]

# BANCO DE DADOS
def init_db():
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()

    # USUÁRIOS
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nivel TEXT DEFAULT 'operador',
        data_cadastro TEXT
    )''')

    # LAVAGENS
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

    # VEÍCULOS
    c.execute('''CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT UNIQUE NOT NULL,
        tipo TEXT NOT NULL,
        modelo_marca TEXT,
        data_cadastro TEXT
    )''')

    # FORNECEDORES
    c.execute('''CREATE TABLE IF NOT EXISTS fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lavador TEXT NOT NULL,
        cnpj TEXT UNIQUE NOT NULL,
        endereco TEXT,
        data_cadastro TEXT
    )''')

    # TABELA DE PREÇOS
    c.execute('''CREATE TABLE IF NOT EXISTS precos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fornecedor_id INTEGER,
        tipo_veiculo TEXT NOT NULL,
        servico TEXT NOT NULL,
        valor REAL NOT NULL,
        FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id) ON DELETE CASCADE
    )''')

    # ADMIN PADRÃO
    c.execute('INSERT OR IGNORE INTO usuarios (nome, email, senha, nivel, data_cadastro) VALUES (?, ?, ?, ?, ?)',
              ('Admin FSJ', 'admin@fsj.com', 'fsj123', 'admin', datetime.now().strftime('%d/%m/%Y %H:%M')))
    conn.commit()
    conn.close()

init_db()

# === FUNÇÕES USUÁRIOS ===
def criar_usuario(nome, email, senha, nivel): ...
def editar_usuario(id_usuario, nome, email, senha, nivel): ...
def excluir_usuario(id_usuario): ...
def validar_login(email, senha): ...
def listar_usuarios(): ...

# === FUNÇÕES VEÍCULOS ===
def criar_veiculo(placa, tipo, modelo_marca): ...
def editar_veiculo(id_veiculo, placa, tipo, modelo_marca): ...
def excluir_veiculo(id_veiculo): ...
def listar_veiculos(): ...

# === FUNÇÕES FORNECEDORES ===
def criar_fornecedor(lavador, cnpj, endereco):
    cnpj = re.sub(r'\D', '', cnpj)
    if len(cnpj) != 14:
        return False, "CNPJ inválido"
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    data_cad = datetime.now().strftime('%d/%m/%Y %H:%M')
    try:
        c.execute('INSERT INTO fornecedores (lavador, cnpj, endereco, data_cadastro) VALUES (?, ?, ?, ?)',
                  (lavador, cnpj, endereco or "", data_cad))
        conn.commit()
        fornecedor_id = c.lastrowid
        return True, fornecedor_id
    except sqlite3.IntegrityError:
        return False, "CNPJ já cadastrado"
    finally:
        conn.close()

def editar_fornecedor(id_forn, lavador, cnpj, endereco):
    cnpj = re.sub(r'\D', '', cnpj)
    if len(cnpj) != 14:
        return False
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    try:
        c.execute('UPDATE fornecedores SET lavador=?, cnpj=?, endereco=? WHERE id=?',
                  (lavador, cnpj, endereco or "", id_forn))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def excluir_fornecedor(id_forn):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('DELETE FROM fornecedores WHERE id = ?', (id_forn,))
    conn.commit()
    conn.close()

def listar_fornecedores():
    conn = sqlite3.connect('fsj_lavagens.db')
    df = pd.read_sql_query('SELECT id, lavador, cnpj, endereco, data_cadastro FROM fornecedores ORDER BY data_cadastro DESC', conn)
    conn.close()
    return df

# === FUNÇÕES PREÇOS ===
def adicionar_preco(fornecedor_id, tipo_veiculo, servico, valor):
    if tipo_veiculo not in TIPOS_VEICULO or servico not in SERVICOS:
        return False
    valor = float(valor)
    if valor <= 0:
        return False
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO precos (fornecedor_id, tipo_veiculo, servico, valor) VALUES (?, ?, ?, ?)',
                  (fornecedor_id, tipo_veiculo, servico, valor))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def editar_preco(id_preco, tipo_veiculo, servico, valor):
    valor = float(valor)
    if valor <= 0 or tipo_veiculo not in TIPOS_VEICULO or servico not in SERVICOS:
        return False
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    try:
        c.execute('UPDATE precos SET tipo_veiculo=?, servico=?, valor=? WHERE id=?',
                  (tipo_veiculo, servico, valor, id_preco))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def excluir_preco(id_preco):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('DELETE FROM precos WHERE id = ?', (id_preco,))
    conn.commit()
    conn.close()

def listar_precos_por_fornecedor(fornecedor_id):
    conn = sqlite3.connect('fsj_lavagens.db')
    df = pd.read_sql_query('SELECT id, tipo_veiculo, servico, valor FROM precos WHERE fornecedor_id = ? ORDER BY tipo_veiculo, servico', conn, params=(fornecedor_id,))
    conn.close()
    return df

# === FUNÇÕES LAVAGENS ===
def emitir_ordem(...): ...
def listar_lavagens(): ...

def sair():
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""
    st.rerun()

# ESTADO
if 'pagina' not in st.session_state: st.session_state.pagina = "login"
if 'fornecedores_expandido' not in st.session_state: st.session_state.fornecedores_expandido = True
if 'editando_fornecedor' not in st.session_state: st.session_state.editando_fornecedor = None
if 'confirmar_exclusao_forn' not in st.session_state: st.session_state.confirmar_exclusao_forn = None
if 'fornecedor_precos' not in st.session_state: st.session_state.fornecedor_precos = None

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
        submenu_lav = "submenu expanded" if st.session_state.get('lavagem_expandido', True) else "submenu collapsed"
        st.markdown(f'<div class="{submenu_lav}">', unsafe_allow_html=True)
        if st.button("Emitir Ordem", key="btn_emitir", use_container_width=True):
            st.session_state.pagina = "emitir_ordem"; st.rerun()
        if st.button("Pesquisa", key="btn_pesquisa_lav", use_container_width=True):
            st.session_state.pagina = "pesquisa_lavagens"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # VEÍCULOS
        if st.session_state.nivel == "admin":
            st.markdown('<div class="menu-title">Veículos</div>', unsafe_allow_html=True)
            submenu_veic = "submenu expanded" if st.session_state.get('veiculos_expandido', True) else "submenu collapsed"
            st.markdown(f'<div class="{submenu_veic}">', unsafe_allow_html=True)
            if st.button("Cadastro", key="btn_cadastro_veic", use_container_width=True):
                st.session_state.pagina = "cadastro_veiculo"; st.rerun()
            if st.button("Pesquisa", key="btn_pesquisa_veic", use_container_width=True):
                st.session_state.pagina = "pesquisa_veiculos"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # FORNECEDORES (NOVO!)
        if st.session_state.nivel == "admin":
            st.markdown('<div class="menu-title">Fornecedores</div>', unsafe_allow_html=True)
            submenu_forn = "submenu expanded" if st.session_state.fornecedores_expandido else "submenu collapsed"
            st.markdown(f'<div class="{submenu_forn}">', unsafe_allow_html=True)
            if st.button("Cadastro", key="btn_cadastro_forn", use_container_width=True):
                st.session_state.pagina = "cadastro_fornecedor"; st.rerun()
            if st.button("Pesquisa", key="btn_pesquisa_forn", use_container_width=True):
                st.session_state.pagina = "pesquisa_fornecedores"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # PÁGINAS
    # ... (outras páginas: emitir_ordem, cadastro_veiculo, etc.)

    # CADASTRO DE FORNECEDOR
    elif st.session_state.pagina == "cadastro_fornecedor":
        st.header("Cadastrar Fornecedor")
        with st.form("novo_fornecedor"):
            lavador = st.text_input("**Nome do Lavador**", max_chars=50)
            cnpj = st.text_input("**CNPJ** (apenas números)", placeholder="12345678000195", max_chars=14)
            endereco = st.text_area("Endereço Completo")
            if st.form_submit_button("Cadastrar"):
                if lavador and cnpj:
                    success, msg = criar_fornecedor(lavador, cnpj, endereco)
                    if success:
                        st.success(f"Fornecedor **{lavador}** cadastrado! ID: {msg}")
                    else:
                        st.error(msg)
                else:
                    st.error("Preencha Lavador e CNPJ!")

    # PESQUISA DE FORNECEDORES
    elif st.session_state.pagina == "pesquisa_fornecedores":
        st.header("Pesquisa de Fornecedores")

        df = listar_fornecedores()
        if not df.empty:
            header_cols = st.columns([3, 2.5, 3, 2, 1.5])
            header_cols[0].write("**Lavador**")
            header_cols[1].write("**CNPJ**")
            header_cols[2].write("**Endereço**")
            header_cols[3].write("**Cadastro**")
            header_cols[4].write("**Ações**")
            st.markdown("---")

            for _, row in df.iterrows():
                cols = st.columns([3, 2.5, 3, 2, 1.5])
                cols[0].write(row['lavador'])
                cols[1].write(f"{row['cnpj'][:2]}.{row['cnpj'][2:5]}.{row['cnpj'][5:8]}/{row['cnpj'][8:12]}-{row['cnpj'][12:]}")
                cols[2].write(row['endereco'] or "-")
                cols[3].write(row['data_cadastro'])

                with cols[4]:
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("Editar", key=f"edit_forn_{row['id']}"):
                            st.session_state.editando_fornecedor = row['id']
                            st.rerun()
                    with col_del:
                        if st.button("Excluir", key=f"del_forn_{row['id']}"):
                            if st.session_state.get('confirmar_exclusao_forn') == row['id']:
                                excluir_fornecedor(row['id'])
                                st.success("Fornecedor excluído!")
                                if 'confirmar_exclusao_forn' in st.session_state:
                                    del st.session_state.confirmar_exclusao_forn
                                st.rerun()
                            else:
                                st.session_state.confirmar_exclusao_forn = row['id']
                                st.warning("Clique novamente para confirmar.")

            # EDIÇÃO
            if st.session_state.editando_fornecedor:
                forn_df = df[df['id'] == st.session_state.editando_fornecedor]
                if not forn_df.empty:
                    forn = forn_df.iloc[0]
                    st.markdown("---")
                    st.subheader(f"Editando: {forn['lavador']}")
                    with st.form("editar_fornecedor"):
                        novo_lavador = st.text_input("Lavador", value=forn['lavador'])
                        novo_cnpj = st.text_input("CNPJ", value=forn['cnpj'])
                        novo_end = st.text_area("Endereço", value=forn['endereco'] or "")
                        col1, col2 = st.columns(2)
                        if col1.form_submit_button("Salvar"):
                            if editar_fornecedor(st.session_state.editando_fornecedor, novo_lavador, novo_cnpj, novo_end):
                                st.success("Atualizado!")
                                del st.session_state.editando_fornecedor
                                st.rerun()
                            else:
                                st.error("CNPJ inválido ou duplicado!")
                        if col2.form_submit_button("Cancelar"):
                            del st.session_state.editando_fornecedor
                            st.rerun()

            # TABELA DE PREÇOS
            st.markdown("---")
            st.subheader("Tabela de Preços por Fornecedor")
            fornecedor_selecionado = st.selectbox("Selecione o Fornecedor", [""] + df['lavador'].tolist())
            if fornecedor_selecionado:
                forn_id = df[df['lavador'] == fornecedor_selecionado].iloc[0]['id']
                st.session_state.fornecedor_precos = forn_id
                precos_df = listar_precos_por_fornecedor(forn_id)

                with st.expander("Adicionar Novo Preço", expanded=False):
                    with st.form("novo_preco"):
                        tipo = st.selectbox("Tipo de Veículo", TIPOS_VEICULO)
                        serv = st.selectbox("Serviço", SERVICOS)
                        valor = st.number_input("Valor (R$)", min_value=0.01, step=5.0)
                        if st.form_submit_button("Adicionar"):
                            if adicionar_preco(forn_id, tipo, serv, valor):
                                st.success("Preço adicionado!")
                                st.rerun()
                            else:
                                st.error("Erro ao adicionar.")

                if not precos_df.empty:
                    for _, row in precos_df.iterrows():
                        col1, col2, col3, col4 = st.columns([2, 2.5, 1.5, 1.5])
                        col1.write(row['tipo_veiculo'])
                        col2.write(row['servico'])
                        col3.write(f"R$ {row['valor']:.2f}")
                        with col4:
                            if st.button("Excluir", key=f"del_preco_{row['id']}"):
                                excluir_preco(row['id'])
                                st.success("Preço removido!")
                                st.rerun()
                else:
                    st.info("Nenhum preço cadastrado.")

            st.download_button("Baixar Fornecedores (CSV)", df.to_csv(index=False).encode('utf-8'), "fornecedores.csv", "text/csv")
        else:
            st.info("Nenhum fornecedor cadastrado.")

st.markdown("---")
st.markdown("*FSJ Logística - Sistema por Grok*")
