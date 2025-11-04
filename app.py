# app.py - FSJ LAVAGENS: FORNECEDORES + TABELA DE PREÇOS + EDIÇÃO
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

# SERVIÇOS ATUALIZADOS
SERVICOS = [
    "LAVAGEM COMPLETA",
    "LAVAGEM + LUBRIFICAÇÃO",
    "LAVAGEM COMPLETA + LIMPEZA INTERNA",
    "LAVAGEM INTERNA DO BAU"
]

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

def editar_usuario(id_usuario, nome, email, senha, nivel):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    try:
        if senha:
            c.execute('UPDATE usuarios SET nome=?, email=?, senha=?, nivel=? WHERE id=?',
                      (nome, email, senha, nivel, id_usuario))
        else:
            c.execute('UPDATE usuarios SET nome=?, email=?, nivel=? WHERE id=?',
                      (nome, email, nivel, id_usuario))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def excluir_usuario(id_usuario):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('DELETE FROM usuarios WHERE id = ?', (id_usuario,))
    conn.commit()
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

# === FUNÇÕES VEÍCULOS ===
def criar_veiculo(placa, tipo, modelo_marca):
    placa = placa.upper().replace("-", "").replace(" ", "")
    if len(placa) != 7 or not re.match(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$", placa):
        return False, "Placa inválida"
    if tipo not in TIPOS_VEICULO:
        return False, "Tipo inválido"
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    data_cad = datetime.now().strftime('%d/%m/%Y %H:%M')
    try:
        c.execute('INSERT INTO veiculos (placa, tipo, modelo_marca, data_cadastro) VALUES (?, ?, ?, ?)',
                  (placa, tipo, modelo_marca or "", data_cad))
        conn.commit()
        return True, "OK"
    except sqlite3.IntegrityError:
        return False, "Placa já cadastrada"
    finally:
        conn.close()

def editar_veiculo(id_veiculo, placa, tipo, modelo_marca):
    placa = placa.upper().replace("-", "").replace(" ", "")
    if len(placa) != 7 or not re.match(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$", placa):
        return False
    if tipo not in TIPOS_VEICULO:
        return False
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    try:
        c.execute('UPDATE veiculos SET placa = ?, tipo = ?, modelo_marca = ? WHERE id = ?',
                  (placa, tipo, modelo_marca or "", id_veiculo))
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
    try:
        valor = float(valor)
        if valor <= 0:
            return False
    except:
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
    try:
        valor = float(valor)
        if valor <= 0 or tipo_veiculo not in TIPOS_VEICULO or servico not in SERVICOS:
            return False
    except:
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
if 'fornecedores_expandido' not in st.session_state:
    st.session_state.fornecedores_expandido = True
if 'editando_usuario' not in st.session_state:
    st.session_state.editando_usuario = None
if 'confirmar_exclusao_usuario' not in st.session_state:
    st.session_state.confirmar_exclusao_usuario = None
if 'editando_veiculo' not in st.session_state:
    st.session_state.editando_veiculo = None
if 'confirmar_exclusao_veiculo' not in st.session_state:
    st.session_state.confirmar_exclusao_veiculo = None
if 'editando_fornecedor' not in st.session_state:
    st.session_state.editando_fornecedor = None
if 'confirmar_exclusao_forn' not in st.session_state:
    st.session_state.confirmar_exclusao_forn = None
if 'fornecedor_precos' not in st.session_state:
    st.session_state.fornecedor_precos = None
if 'editando_preco' not in st.session_state:
    st.session_state.editando_preco = None
if 'preco_tipo' not in st.session_state:
    st.session_state.preco_tipo = ""
if 'preco_serv' not in st.session_state:
    st.session_state.preco_serv = ""
if 'preco_valor' not in st.session_state:
    st.session_state.preco_valor = 0.0

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

        # FORNECEDORES (ADMIN)
        if st.session_state.nivel == "admin":
            st.markdown('<div class="menu-title">Fornecedores</div>', unsafe_allow_html=True)
            submenu_forn = "submenu expanded" if st.session_state.fornecedores_expandido else "submenu collapsed"
            st.markdown(f'<div class="{submenu_forn}">', unsafe_allow_html=True)
            if st.button("Cadastro", key="btn_cadastro_forn", use_container_width=True):
                st.session_state.pagina = "cadastro_fornecedor"
                st.rerun()
            if st.button("Pesquisa", key="btn_pesquisa_forn", use_container_width=True):
                st.session_state.pagina = "pesquisa_fornecedores"
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
            header_cols = st.columns([3, 3, 2, 1.5, 1.5])
            header_cols[0].write("**Nome**")
            header_cols[1].write("**E-mail**")
            header_cols[2].write("**Data Cadastro**")
            header_cols[3].write("**Nível**")
            header_cols[4].write("**Ações**")
            st.markdown("---")

            for _, row in df.iterrows():
                cols = st.columns([3, 3, 2, 1.5, 1.5])
                cols[0].write(row['nome'])
                cols[1].write(row['email'])
                cols[2].write(row['data_cadastro'])
                cols[3].write(row['nivel'].title())
                
                with cols[4]:
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("Editar", key=f"edit_usr_{row['id']}"):
                            st.session_state.editando_usuario = row['id']
                            st.rerun()
                    with col_del:
                        if st.button("Excluir", key=f"del_usr_{row['id']}"):
                            if st.session_state.get('confirmar_exclusao_usuario') == row['id']:
                                excluir_usuario(row['id'])
                                st.success("Usuário excluído!")
                                if 'confirmar_exclusao_usuario' in st.session_state:
                                    del st.session_state.confirmar_exclusao_usuario
                                st.rerun()
                            else:
                                st.session_state.confirmar_exclusao_usuario = row['id']
                                st.warning("Clique novamente para confirmar.")
                                st.rerun()

            if st.session_state.editando_usuario is not None:
                user_df = df[df['id'] == st.session_state.editando_usuario]
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
                            if editar_usuario(st.session_state.editando_usuario, novo_nome, novo_email, nova_senha, novo_nivel):
                                st.success("Usuário atualizado!")
                                del st.session_state.editando_usuario
                                st.rerun()
                            else:
                                st.error("E-mail já existe!")
                        
                        if col2.form_submit_button("Cancelar"):
                            del st.session_state.editando_usuario
                            st.rerun()

            df_display = df[['nome', 'email', 'data_cadastro', 'nivel']].copy()
            st.download_button("Baixar Lista (CSV)", df_display.to_csv(index=False).encode('utf-8'), "funcionarios.csv", "text/csv")
        else:
            st.info("Nenhum usuário cadastrado.")

    elif st.session_state.pagina == "cadastro_veiculo":
        st.header("Cadastrar Veículo")
        with st.form("novo_veiculo"):
            placa = st.text_input("**PLACA** (7 caracteres: ABC1D23)", max_chars=7).upper()
            tipo = st.selectbox("**TIPO DO VEÍCULO**", TIPOS_VEICULO)
            modelo_marca = st.text_input("MODELO/MARCA", max_chars=30)
            if st.form_submit_button("Cadastrar Veículo"):
                if len(placa) == 7 and re.match(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$", placa):
                    success, _ = criar_veiculo(placa, tipo, modelo_marca)
                    if success:
                        st.success(f"Veículo **{placa}** cadastrado!")
                    else:
                        st.error("Placa já cadastrada!")
                else:
                    st.error("Placa inválida! Use: ABC1D23")

    elif st.session_state.pagina == "pesquisa_veiculos":
        st.header("Pesquisa de Veículos")

        with st.expander("IMPORTAR VEÍCULOS (CSV)", expanded=False):
            col1, col2 = st.columns([3, 1])
            uploaded_file = col1.file_uploader("Escolha o arquivo CSV", type=['csv'], key="import_veic_csv")
            if col2.button("Importar", use_container_width=True) and uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    required = ["PLACA", "TIPO DO VEÍCULO", "MODELO/MARCA"]
                    if not all(col in df.columns for col in required):
                        st.error(f"Colunas obrigatórias: {', '.join(required)}")
                    else:
                        sucessos = []
                        erros = []
                        for idx, row in df.iterrows():
                            placa = str(row["PLACA"]).strip()
                            tipo = str(row["TIPO DO VEÍCULO"]).strip().upper()
                            modelo = str(row.get("MODELO/MARCA", "")).strip()
                            success, msg = criar_veiculo(placa, tipo, modelo)
                            if success:
                                sucessos.append(placa)
                            else:
                                erros.append(f"Linha {idx+2}: {msg}")
                        st.success(f"**{len(sucessos)} importados!**")
                        if erros:
                            st.error(f"**{len(erros)} erros:** " + "; ".join(erros[:5]))
                except Exception as e:
                    st.error(f"Erro: {e}")

            csv_template = """PLACA,TIPO DO VEÍCULO,MODELO/MARCA
ABC1D23,TRUCK,Scania R450
XYZ9E87,CONJUNTO BITREM,Volvo FH
"""
            st.download_button("Baixar Modelo (CSV)", data=csv_template, file_name="modelo_veiculos.csv", mime="text/csv")

        st.markdown("---")
        df = listar_veiculos()
        if not df.empty:
            header_cols = st.columns([2, 2.5, 2.5, 2, 1.5])
            header_cols[0].write("**Placa**")
            header_cols[1].write("**Tipo do Veículo**")
            header_cols[2].write("**Modelo/Marca**")
            header_cols[3].write("**Data Cadastro**")
            header_cols[4].write("**Ações**")
            st.markdown("---")

            for _, row in df.iterrows():
                cols = st.columns([2, 2.5, 2.5, 2, 1.5])
                cols[0].write(row['placa'])
                cols[1].write(row['tipo'])
                cols[2].write(row['modelo_marca'] or "-")
                cols[3].write(row['data_cadastro'])
                
                with cols[4]:
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("Editar", key=f"edit_veic_{row['id']}"):
                            st.session_state.editando_veiculo = row['id']
                            st.rerun()
                    with col_del:
                        if st.button("Excluir", key=f"del_veic_{row['id']}"):
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

            if st.session_state.editando_veiculo:
                veic_df = df[df['id'] == st.session_state.editando_veiculo]
                if not veic_df.empty:
                    veic = veic_df.iloc[0]
                    st.markdown("---")
                    st.subheader(f"Editando: {veic['placa']}")
                    with st.form("editar_veiculo"):
                        nova_placa = st.text_input("PLACA", value=veic['placa'], max_chars=7).upper()
                        novo_tipo = st.selectbox("**TIPO DO VEÍCULO**", TIPOS_VEICULO,
                                                index=TIPOS_VEICULO.index(veic['tipo']) if veic['tipo'] in TIPOS_VEICULO else 0)
                        novo_modelo = st.text_input("MODELO/MARCA", value=veic['modelo_marca'] or "", max_chars=30)
                        col1, col2 = st.columns(2)
                        if col1.form_submit_button("Salvar"):
                            if len(nova_placa) == 7 and re.match(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$", nova_placa):
                                if editar_veiculo(st.session_state.editando_veiculo, nova_placa, novo_tipo, novo_modelo):
                                    st.success("Atualizado!")
                                    del st.session_state.editando_veiculo
                                    st.rerun()
                                else:
                                    st.error("Placa já existe!")
                            else:
                                st.error("Placa inválida!")
                        if col2.form_submit_button("Cancelar"):
                            del st.session_state.editando_veiculo
                            st.rerun()

            df_display = df[['placa', 'tipo', 'modelo_marca', 'data_cadastro']].copy()
            st.download_button("Baixar CSV", df_display.to_csv(index=False).encode('utf-8'), "veiculos.csv", "text/csv")
        else:
            st.info("Nenhum veículo cadastrado.")

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
                cnpj_formatado = f"{row['cnpj'][:2]}.{row['cnpj'][2:5]}.{row['cnpj'][5:8]}/{row['cnpj'][8:12]}-{row['cnpj'][12:]}"
                cols[1].write(cnpj_formatado)
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
            fornecedor_selecionado = st.selectbox("Selecione o Fornecedor", [""] + df['lavador'].tolist(), key="select_forn_preco")
            if fornecedor_selecionado:
                forn_id = df[df['lavador'] == fornecedor_selecionado].iloc[0]['id']
                st.session_state.fornecedor_precos = forn_id
                precos_df = listar_precos_por_fornecedor(forn_id)

                with st.expander("Adicionar Novo Preço", expanded=False):
                    with st.form("novo_preco"):
                        tipo = st.selectbox("Tipo de Veículo", TIPOS_VEICULO, key="novo_tipo")
                        serv = st.selectbox("Serviço", SERVICOS, key="novo_serv")
                        valor = st.number_input("Valor (R$)", min_value=0.01, step=5.0, format="%.2f", key="novo_valor")
                        if st.form_submit_button("Adicionar"):
                            if adicionar_preco(forn_id, tipo, serv, valor):
                                st.success("Preço adicionado!")
                                st.rerun()
                            else:
                                st.error("Erro ao adicionar.")

                if not precos_df.empty:
                    st.write("**Preços Cadastrados:**")
                    for idx, row in precos_df.iterrows():
                        col1, col2, col3, col4 = st.columns([2, 3, 1.5, 2])
                        col1.write(row['tipo_veiculo'])
                        col2.write(row['servico'])
                        col3.write(f"R$ {row['valor']:.2f}")

                        with col4:
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button("Editar", key=f"edit_preco_{row['id']}"):
                                    st.session_state.editando_preco = row['id']
                                    st.session_state.preco_tipo = row['tipo_veiculo']
                                    st.session_state.preco_serv = row['servico']
                                    st.session_state.preco_valor = row['valor']
                                    st.rerun()
                            with col_del:
                                if st.button("Excluir", key=f"del_preco_{row['id']}"):
                                    excluir_preco(row['id'])
                                    st.success("Preço removido!")
                                    st.rerun()

                    if st.session_state.get('editando_preco'):
                        preco_id = st.session_state.editando_preco
                        with st.form("editar_preco_form"):
                            st.write("**Editando Preço**")
                            tipo_edit = st.selectbox(
                                "Tipo de Veículo",
                                TIPOS_VEICULO,
                                index=TIPOS_VEICULO.index(st.session_state.preco_tipo) if st.session_state.preco_tipo in TIPOS_VEICULO else 0,
                                key="edit_tipo"
                            )
                            serv_edit = st.selectbox(
                                "Serviço",
                                SERVICOS,
                                index=SERVICOS.index(st.session_state.preco_serv) if st.session_state.preco_serv in SERVICOS else 0,
                                key="edit_serv"
                            )
                            valor_edit = st.number_input(
                                "Valor (R$)",
                                min_value=0.01,
                                value=float(st.session_state.preco_valor),
                                step=5.0,
                                format="%.2f",
                                key="edit_valor"
                            )
                            col1, col2 = st.columns(2)
                            if col1.form_submit_button("Salvar Alterações"):
                                if editar_preco(preco_id, tipo_edit, serv_edit, valor_edit):
                                    st.success("Preço atualizado!")
                                    for key in ['editando_preco', 'preco_tipo', 'preco_serv', 'preco_valor']:
                                        if key in st.session_state:
                                            del st.session_state[key]
                                    st.rerun()
                                else:
                                    st.error("Erro ao salvar.")
                            if col2.form_submit_button("Cancelar"):
                                for key in ['editando_preco', 'preco_tipo', 'preco_serv', 'preco_valor']:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.rerun()

                else:
                    st.info("Nenhum preço cadastrado para este fornecedor.")

            st.download_button(
                "Baixar Fornecedores (CSV)",
                df.to_csv(index=False).encode('utf-8'),
                "fornecedores.csv",
                "text/csv"
            )
        else:
            st.info("Nenhum fornecedor cadastrado.")

st.markdown("---")
st.markdown("*FSJ Logística - Sistema por Grok*")
