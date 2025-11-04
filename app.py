# app.py - IMPORTAÇÃO EM MASSA DE VEÍCULOS
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

# TIPOS DE VEÍCULO
TIPOS_VEICULO = [
    "TRUCK", "CONJUNTO LS", "REBOQUE", "CAVALO", 
    "CAMINHÃO 3/4", "CONJUNTO BITREM", "PRANCHA"
]

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

# FUNÇÕES USUÁRIOS (resumidas)
def criar_usuario(nome, email, senha, nivel): ...
def editar_usuario(id_usuario, nome, email, senha, nivel): ...
def excluir_usuario(id_usuario): ...
def validar_login(email, senha): ...
def listar_usuarios(): ...

# FUNÇÕES VEÍCULOS
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

def editar_veiculo(id_veiculo, placa, tipo, modelo_marca): ...
def excluir_veiculo(id_veiculo): ...
def listar_veiculos(): ...

# IMPORTAÇÃO EM MASSA
def importar_veiculos_excel(file):
    try:
        df = pd.read_excel(file)
    except Exception as e:
        return False, [], f"Erro ao ler arquivo: {e}"

    required_cols = ["PLACA", "TIPO DO VEÍCULO", "MODELO/MARCA"]
    if not all(col in df.columns for col in required_cols):
        return False, [], f"Colunas obrigatórias: {', '.join(required_cols)}"

    sucessos = []
    erros = []

    for idx, row in df.iterrows():
        placa = str(row["PLACA"]).strip()
        tipo = str(row["TIPO DO VEÍCULO"]).strip().upper()
        modelo = str(row.get("MODELO/MARCA", "")).strip()

        success, msg = criar_veiculo(placa, tipo, modelo)
        if success:
            sucessos.append(f"{placa} → {tipo}")
        else:
            erros.append(f"Linha {idx+2}: {placa} → {msg}")

    return True, sucessos, erros

# FUNÇÕES LAVAGENS (resumidas)
def emitir_ordem(...): ...
def listar_lavagens(): ...

def sair():
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""
    st.rerun()

# ESTADO
if 'pagina' not in st.session_state: st.session_state.pagina = "login"
if 'lavagem_expandido' not in st.session_state: st.session_state.lavagem_expandido = True
if 'usuarios_expandido' not in st.session_state: st.session_state.usuarios_expandido = True
if 'veiculos_expandido' not in st.session_state: st.session_state.veiculos_expandido = True
if 'editando_usuario' not in st.session_state: st.session_state.editando_usuario = None
if 'confirmar_exclusao_usuario' not in st.session_state: st.session_state.confirmar_exclusao_usuario = None
if 'editando_veiculo' not in st.session_state: st.session_state.editando_veiculo = None
if 'confirmar_exclusao_veiculo' not in st.session_state: st.session_state.confirmar_exclusao_veiculo = None

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
            st.session_state.pagina = "emitir_ordem"; st.rerun()
        if st.button("Pesquisa de Lavagens", key="btn_pesquisa_lav", use_container_width=True):
            st.session_state.pagina = "pesquisa_lavagens"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # USUÁRIOS (ADMIN)
        if st.session_state.nivel == "admin":
            st.markdown('<div class="menu-title">Usuários</div>', unsafe_allow_html=True)
            submenu_usr = "submenu expanded" if st.session_state.usuarios_expandido else "submenu collapsed"
            st.markdown(f'<div class="{submenu_usr}">', unsafe_allow_html=True)
            if st.button("Cadastro", key="btn_cadastro", use_container_width=True):
                st.session_state.pagina = "cadastro_usuario"; st.rerun()
            if st.button("Pesquisa", key="btn_pesquisa_usr", use_container_width=True):
                st.session_state.pagina = "pesquisa_usuarios"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # VEÍCULOS (ADMIN)
        if st.session_state.nivel == "admin":
            st.markdown('<div class="menu-title">Veículos</div>', unsafe_allow_html=True)
            submenu_veic = "submenu expanded" if st.session_state.veiculos_expandido else "submenu collapsed"
            st.markdown(f'<div class="{submenu_veic}">', unsafe_allow_html=True)
            if st.button("Cadastro", key="btn_cadastro_veic", use_container_width=True):
                st.session_state.pagina = "cadastro_veiculo"; st.rerun()
            if st.button("Pesquisa", key="btn_pesquisa_veic", use_container_width=True):
                st.session_state.pagina = "pesquisa_veiculos"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # PÁGINAS
    # ... (outras páginas: emitir_ordem, cadastro_usuario, etc.)

    # PESQUISA DE VEÍCULOS COM IMPORTAÇÃO
    elif st.session_state.pagina == "pesquisa_veiculos":
        st.header("Pesquisa de Veículos")

        # BOTÃO DE IMPORTAÇÃO
        with st.expander("IMPORTAR VEÍCULOS (EXCEL)", expanded=False):
            col1, col2 = st.columns([3, 1])
            uploaded_file = col1.file_uploader("Escolha o arquivo Excel", type=['xlsx'], key="import_veic")
            if col2.button("Importar", use_container_width=True) and uploaded_file:
                with st.spinner("Importando..."):
                    success, sucessos, erros = importar_veiculos_excel(uploaded_file)
                    if success:
                        st.success(f"**{len(sucessos)} veículos importados com sucesso!**")
                        if sucessos:
                            st.write("**Importados:**")
                            for item in sucessos[:10]:
                                st.write(f"→ {item}")
                            if len(sucessos) > 10:
                                st.write(f"... e mais {len(sucessos)-10}")
                        if erros:
                            st.error(f"**{len(erros)} erros encontrados:**")
                            for erro in erros:
                                st.write(f"→ {erro}")
                    else:
                        st.error(f"Erro: {erros}")

            # LINK PARA TEMPLATE
            template = pd.DataFrame({
                "PLACA": ["ABC1D23", "XYZ9E87"],
                "TIPO DO VEÍCULO": ["TRUCK", "CONJUNTO BITREM"],
                "MODELO/MARCA": ["Scania R450", "Volvo FH"]
            })
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                template.to_excel(writer, index=False, sheet_name='Veiculos')
            output.seek(0)
            st.download_button(
                label="Baixar Modelo Excel",
                data=output,
                file_name="modelo_veiculos.xlsx",
                mime="application/vnd.ms-excel"
            )

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
                                del st.session_state.confirmar_exclusao_veiculo
                                st.rerun()
                            else:
                                st.session_state.confirmar_exclusao_veiculo = row['id']
                                st.warning("Clique novamente para confirmar.")
                                st.rerun()

            # EDIÇÃO
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

st.markdown("---")
st.markdown("*FSJ Logística - Sistema por Grok*")
