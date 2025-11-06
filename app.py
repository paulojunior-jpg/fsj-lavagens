# app.py - FSJ LAVAGENS: SISTEMA COMPLETO COM PDF, STATUS, FOTO E RELATÓRIO
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import re
import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
import plotly.express as px

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
        usuario_criacao TEXT,
        foto_path TEXT
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

    # ADICIONAR COLUNAS SE NÃO EXISTIREM
    c.execute('PRAGMA table_info(lavagens)')
    cols = [col[1] for col in c.fetchall()]
    if 'status' not in cols:
        c.execute('ALTER TABLE lavagens ADD COLUMN status TEXT DEFAULT "Pendente"')
    if 'foto_path' not in cols:
        c.execute('ALTER TABLE lavagens ADD COLUMN foto_path TEXT')

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
def emitir_ordem(placa, motorista, operacao, hora_inicio, hora_fim, obs, usuario, status="Pendente", foto_path=None):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) FROM lavagens WHERE data = ?', (data_hoje,))
    contador = c.fetchone()[0] + 1
    numero_ordem = f"ORD-{data_hoje.replace('-','')}-{contador:03d}"
    c.execute('''INSERT INTO lavagens 
    (numero_ordem, placa, motorista, operacao, data, hora_inicio, hora_fim, observacoes, status, usuario_criacao, foto_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (numero_ordem, placa.upper(), motorista, operacao, data_hoje, hora_inicio, hora_fim, obs, status, usuario, foto_path))
    conn.commit()
    conn.close()
    return numero_ordem

def listar_lavagens():
    conn = sqlite3.connect('fsj_lavagens.db')
    df = pd.read_sql_query('''SELECT numero_ordem, placa, motorista, operacao, data, hora_inicio, hora_fim, status, observacoes, foto_path,
                           (SELECT lavador FROM fornecedores f 
                            JOIN precos p ON p.fornecedor_id = f.id 
                            WHERE p.tipo_veiculo = SUBSTR(operacao, 1, INSTR(operacao, ' - ')-1)
                            LIMIT 1) as lavador,
                           (SELECT valor FROM precos p 
                            WHERE p.tipo_veiculo = SUBSTR(operacao, 1, INSTR(operacao, ' - ')-1)
                            AND p.servico = SUBSTR(operacao, INSTR(operacao, ' - ')+3)
                            LIMIT 1) as valor
                           FROM lavagens ORDER BY data DESC''', conn)
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
        if st.button("Controle de Lavagens", key="btn_controle", use_container_width=True):
            st.session_state.pagina = "controle_lavagens"
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

        df_veiculos = listar_veiculos()
        df_fornecedores = listar_fornecedores()
        placas = [""] + df_veiculos['placa'].tolist()
        lavadores = [""] + df_fornecedores['lavador'].tolist()

        with st.form("nova_ordem", clear_on_submit=True):
            data_ordem = datetime.now().strftime("%d/%m/%Y")
            st.write(f"**Data:** {data_ordem}")

            col1, col2, col3 = st.columns(3)
            caminhao = col1.selectbox("**CAMINHÃO**", placas, key="caminhao")
            reboque1 = col2.selectbox("**REBOQUE 1**", placas, key="reboque1")
            reboque2 = col3.selectbox("**REBOQUE 2**", placas, key="reboque2")

            tipo_veiculo = ""
            if caminhao and not reboque1 and not reboque2:
                tipo_row = df_veiculos[df_veiculos['placa'] == caminhao]
                tipo_veiculo = tipo_row['tipo'].iloc[0] if not tipo_row.empty else ""
            elif caminhao and reboque1 and not reboque2:
                tipo_veiculo = "CONJUNTO LS"
            elif caminhao and reboque1 and reboque2:
                tipo_veiculo = "CONJUNTO BITREM"

            st.write(f"**TIPO DE VEÍCULO:** {tipo_veiculo or 'Selecione as placas'}")

            lavador = st.selectbox("**LAVADOR**", lavadores, key="lavador")

            servico = ""
            valor = 0.0
            if lavador and tipo_veiculo:
                forn_id = df_fornecedores[df_fornecedores['lavador'] == lavador].iloc[0]['id']
                precos_df = listar_precos_por_fornecedor(forn_id)
                precos_filtrados = precos_df[precos_df['tipo_veiculo'] == tipo_veiculo]
                servicos_disponiveis = precos_filtrados['servico'].tolist()

                if servicos_disponiveis:
                    servico = st.selectbox("**SERVIÇO**", servicos_disponiveis, key="servico")
                    valor_row = precos_filtrados[precos_filtrados['servico'] == servico]
                    valor = valor_row['valor'].iloc[0] if not valor_row.empty else 0.0
                    st.write(f"**VALOR:** R$ {valor:.2f}")
                else:
                    st.warning("Nenhum serviço cadastrado.")
            else:
                st.write("**SERVIÇO/VALOR:** Selecione Lavador + Placas")

            col4, col5 = st.columns(2)
            motorista = col4.text_input("**MOTORISTA**", max_chars=50)
            frota = col5.checkbox("FROTA", key="frota")
            px = col5.checkbox("PX", key="px")

            uploaded_file = st.file_uploader("**Foto do Veículo (opcional)**", type=['png', 'jpg', 'jpeg'])
            obs = st.text_area("Observações")

            if st.form_submit_button("Emitir Ordem"):
                if not caminhao or not lavador or not tipo_veiculo or not servico or valor == 0:
                    st.error("Preencha todos os campos obrigatórios!")
                else:
                    placa_final = caminhao
                    if reboque1: placa_final += f" + {reboque1}"
                    if reboque2: placa_final += f" + {reboque2}"

                    foto_path = None
                    if uploaded_file:
                        foto_path = f"static/fotos/{uploaded_file.name}"
                        os.makedirs("static/fotos", exist_ok=True)
                        with open(foto_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                    ordem = emitir_ordem(
                        placa=placa_final,
                        motorista=motorista or "Não informado",
                        operacao=f"{tipo_veiculo} - {servico}",
                        hora_inicio="",
                        hora_fim="",
                        obs=f"Lavador: {lavador} | Valor: R${valor:.2f} | Frota: {'Sim' if frota else 'Não'} | PX: {'Sim' if px else 'Não'} | {obs}",
                        usuario=st.session_state.usuario,
                        status="Pendente",
                        foto_path=foto_path
                    )

                    # GERAR PDF
                    buffer = BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm)
                    styles = getSampleStyleSheet()
                    story = []

                    story.append(Paragraph("<font size=18><b>ORDEM DE LAVAGEM</b></font>", styles['Title']))
                    story.append(Spacer(1, 0.5*cm))

                    data = [
                        ["<b>Nº Ordem:</b>", ordem],
                        ["<b>Data:</b>", datetime.now().strftime("%d/%m/%Y %H:%M")],
                        ["<b>Placa(s):</b>", placa_final],
                        ["<b>Tipo:</b>", tipo_veiculo],
                        ["<b>Lavador:</b>", lavador],
                        ["<b>Serviço:</b>", servico],
                        ["<b>Valor:</b>", f"R$ {valor:.2f}"],
                        ["<b>Motorista:</b>", motorista or "Não informado"],
                        ["<b>Frota/PX:</b>", f"FROTA: {'Sim' if frota else 'Não'} | PX: {'Sim' if px else 'Não'}"],
                        ["<b>Status:</b>", "Pendente"],
                    ]
                    table = Table(data, colWidths=[3*cm, 10*cm])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1565c0')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 0.5*cm))

                    if foto_path and os.path.exists(foto_path):
                        img = Image(foto_path, width=12*cm, height=8*cm)
                        img.hAlign = 'CENTER'
                        story.append(img)
                        story.append(Spacer(1, 0.3*cm))

                    qr = qrcode.QRCode(version=1, box_size=5, border=2)
                    qr.add_data(f"https://seusite.com/ordem/{ordem}")
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    qr_buffer = BytesIO()
                    img.save(qr_buffer, format='PNG')
                    qr_buffer.seek(0)
                    qr_img = Image(qr_buffer, width=3*cm, height=3*cm)
                    qr_img.hAlign = 'CENTER'
                    story.append(qr_img)
                    story.append(Paragraph("<i>Escaneie para acompanhar</i>", ParagraphStyle('Normal', alignment=1)))

                    doc.build(story)
                    pdf_data = buffer.getvalue()
                    buffer.close()

                    st.success(f"**Ordem emitida: {ordem}**")
                    st.download_button("BAIXAR PDF", pdf_data, f"{ordem}.pdf", "application/pdf")
                    st.balloons()

    elif st.session_state.pagina == "controle_lavagens":
        st.header("Controle de Lavagens")

        df = listar_lavagens()
        if not df.empty:
            for _, row in df.iterrows():
                with st.expander(f"**{row['numero_ordem']}** | {row['placa']} | {row['status']}", expanded=False):
                    col1, col2 = st.columns([3, 2])
                    col1.write(f"**Placa:** {row['placa']}")
                    col1.write(f"**Operação:** {row['operacao']}")
                    col1.write(f"**Data:** {row['data']}")
                    col1.write(f"**Motorista:** {row['motorista']}")
                    col1.write(f"**Lavador:** {row['lavador'] or 'N/D'}")
                    col1.write(f"**Valor:** R$ {row['valor'] or 0:.2f}")

                    status = col2.selectbox(
                        "Status",
                        ["Pendente", "Em Andamento", "Concluída"],
                        index=["Pendente", "Em Andamento", "Concluída"].index(row['status']),
                        key=f"status_{row['numero_ordem']}"
                    )

                    if status != row['status']:
                        conn = sqlite3.connect('fsj_lavagens.db')
                        c = conn.cursor()
                        c.execute('UPDATE lavagens SET status = ? WHERE numero_ordem = ?', (status, row['numero_ordem']))
                        conn.commit()
                        conn.close()
                        st.success(f"Status atualizado para **{status}**")
                        st.rerun()

                    if row['foto_path'] and os.path.exists(row['foto_path']):
                        col2.image(row['foto_path'], caption="Foto do veículo", width=200)

                    foto_nova = col2.file_uploader("Nova foto", type=['png', 'jpg'], key=f"foto_{row['numero_ordem']}")
                    if foto_nova:
                        novo_path = f"static/fotos/{foto_nova.name}"
                        os.makedirs("static/fotos", exist_ok=True)
                        with open(novo_path, "wb") as f:
                            f.write(foto_nova.getbuffer())
                        conn = sqlite3.connect('fsj_lavagens.db')
                        c = conn.cursor()
                        c.execute('UPDATE lavagens SET foto_path = ? WHERE numero_ordem = ?', (novo_path, row['numero_ordem']))
                        conn.commit()
                        conn.close()
                        st.success("Foto atualizada!")
                        st.rerun()

        # RELATÓRIO MENSAL
        st.markdown("---")
        st.subheader("Relatório Mensal")
        mes = st.selectbox("Mês", [f"{i:02d}/2025" for i in range(1, 13)], index=10)
        mes_num = mes.split("/")[0]
        df_mes = df[df['data'].str.contains(f"-{mes_num.zfill(2)}-")]
        if not df_mes.empty:
            resumo = df_mes.groupby(['lavador']).agg({
                'valor': 'sum',
                'numero_ordem': 'count'
            }).reset_index()
            resumo.columns = ['Lavador', 'Total (R$)', 'Ordens']

            col1, col2 = st.columns(2)
            col1.dataframe(resumo, use_container_width=True)
            fig = px.bar(resumo, x='Lavador', y='Total (R$)', text='Ordens', title=f"Total por Lavador - {mes}")
            col2.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma lavagem neste mês.")

    # [Demais páginas: cadastro_usuario, pesquisa_usuarios, cadastro_veiculo, pesquisa_veiculos, cadastro_fornecedor, pesquisa_fornecedores]
    # ... (mantidas como estavam nas versões anteriores)

st.markdown("---")
st.markdown("*FSJ Logística*")
