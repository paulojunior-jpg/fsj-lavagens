# app.py - Sistema de Lavagens FSJ Logística
import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# Configuração da página
st.set_page_config(page_title="FSJ Lavagens", layout="wide")

# Conexão com banco
def init_db():
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nivel TEXT DEFAULT 'operador'  -- operador ou admin
    )
    ''')
    
    # Tabela de lavagens
    c.execute('''
    CREATE TABLE IF NOT EXISTS lavagens (
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
    )
    ''')
    
    # Usuário padrão (mude a senha depois!)
    c.execute('INSERT OR IGNORE INTO usuarios (nome, email, senha, nivel) VALUES (?, ?, ?, ?)',
              ('Admin FSJ', 'admin@fsj.com', 'fsj123', 'admin'))
    
    conn.commit()
    conn.close()

# Inicializar banco
init_db()

# Funções de banco
def criar_usuario(nome, email, senha, nivel='operador'):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO usuarios (nome, email, senha, nivel) VALUES (?, ?, ?, ?)',
                  (nome, email, senha, nivel))
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

def emitir_ordem(placa, motorista, operacao, hora_inicio, hora_fim, obs, usuario):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    contador = len(listar_lavagens()) + 1
    numero_ordem = f"ORD-{data_hoje.replace('-','')}-{contador:03d}"
    
    c.execute('''
    INSERT INTO lavagens 
    (numero_ordem, placa, motorista, operacao, data, hora_inicio, hora_fim, observacoes, status, usuario_criacao)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendente', ?)
    ''', (numero_ordem, placa.upper(), motorista, operacao, data_hoje, hora_inicio, hora_fim, obs, usuario))
    
    conn.commit()
    conn.close()
    return numero_ordem

def listar_lavagens():
    conn = sqlite3.connect('fsj_lavagens.db')
    df = pd.read_sql_query('''
    SELECT numero_ordem, placa, motorista, operacao, data, hora_inicio, hora_fim, status, observacoes
    FROM lavagens ORDER BY data DESC, hora_inicio DESC
    ''', conn)
    conn.close()
    return df

def atualizar_status(ordem, status):
    conn = sqlite3.connect('fsj_lavagens.db')
    c = conn.cursor()
    c.execute('UPDATE lavagens SET status = ? WHERE numero_ordem = ?', (status, ordem))
    conn.commit()
    conn.close()

# Interface
st.title("🚛 FSJ Logística - Gerenciador de Lavagens")

# Sessão de login
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

# Tela de Login
if not st.session_state.logado:
    st.subheader("🔐 Faça Login")
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("E-mail", placeholder="ex: admin@fsj.com")
    with col2:
        senha = st.text_input("Senha", type="password", placeholder="fsj123")
    
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

    # Cadastro (só admin - mas por enquanto, escondei para simplicidade)
    if st.button("Precisa de ajuda para criar usuários? Me avise no chat!"):
        st.info("Clique no botão de chat para eu te ajudar.")

else:
    # Menu lateral
    st.sidebar.success(f"👤 Logado como: {st.session_state.usuario}")
    st.sidebar.button("🚪 Sair", on_click=lambda: setattr(st.session_state, 'logado', False) or st.rerun())
    
    opcao = st.sidebar.selectbox("📋 Escolha uma opção:", ["Emitir Nova Ordem", "Ver Histórico"])

    if opcao == "Emitir Nova Ordem":
        st.header("📄 Emitir Ordem de Lavagem")
        with st.form("nova_ordem", clear_on_submit=True):
            col1, col2 = st.columns(2)
            placa = col1.text_input("**Placa do Caminhão** (obrigatório)", placeholder="ABC-1234").upper()
            motorista = col2.text_input("Motorista")
            
            col3, col4 = st.columns(2)
            operacao = col3.text_input("Operação", placeholder="Ex: Carga/Descarga")
            
            col5, col6 = st.columns(2)
            hora_inicio = col5.time_input("Hora Início")
            hora_fim = col6.time_input("Hora Fim")
            
            obs = st.text_area("Observações", placeholder="Ex: Lavagem externa completa")
            
            if st.form_submit_button("🚀 Emitir Ordem", use_container_width=True):
                if placa:
                    ordem_num = emitir_ordem(
                        placa, motorista or "Não informado", operacao or "Geral",
                        str(hora_inicio) if hora_inicio else "Não definido",
                        str(hora_fim) if hora_fim else "Não definido",
                        obs, st.session_state.usuario
                    )
                    st.balloons()
                    st.success(f"✅ Ordem emitida com sucesso! **Número: {ordem_num}**")
                    st.info(f"Salva no histórico. Vá em 'Ver Histórico' para acompanhar.")
                else:
                    st.error("❌ Placa é obrigatória! Preencha e tente novamente.")

    elif opcao == "Ver Histórico":
        st.header("📊 Histórico de Lavagens")
        
        # Filtros simples
        col_f1, col_f2, col_f3 = st.columns(3)
        filtro_placa = col_f1.text_input("🔍 Filtrar por Placa")
        filtro_motorista = col_f2.text_input("🔍 Filtrar por Motorista")
        filtro_status = col_f3.selectbox("Status", ["Todos", "Pendente", "Concluída"])
        
        df = listar_lavagens()
        
        # Aplicar filtros
        if filtro_placa:
            df = df[df['placa'].str.contains(filtro_placa.upper(), na=False)]
        if filtro_motorista:
            df = df[df['motorista'].str.contains(filtro_motorista, case=False, na=False)]
        if filtro_status != "Todos":
            df = df[df['status'] == filtro_status]
        
        if not df.empty:
            st.subheader(f"🗂️ {len(df)} registro(s) encontrado(s)")
            
            # Tabela editável para status
            for idx, row in df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 1.5, 1])
                    col1.metric("Ordem", row['numero_ordem'])
                    col2.write(f"**Placa:** {row['placa']} | **Motorista:** {row['motorista']} | **Op:** {row['operacao']} | **Data:** {row['data']}")
                    col3.write(f"⏰ {row['hora_inicio']} - {row['hora_fim']}")
                    
                    # Atualizar status
                    novo_status = col4.selectbox(
                        "Status Atualizar", ["Pendente", "Concluída"], 
                        index=0 if row['status'] == 'Pendente' else 1,
                        key=f"status_key_{row['id'] if 'id' in row else idx}"
                    )
                    if novo_status != row['status'] and st.button("💾 Salvar", key=f"salvar_{row['numero_ordem']}"):
                        atualizar_status(row['numero_ordem'], novo_status)
                        st.success("Status atualizado! 🔄")
                        st.rerun()
            
            # Tabela resumida
            st.dataframe(
                df[['numero_ordem', 'placa', 'motorista', 'data', 'status', 'observacoes']],
                use_container_width=True,
                hide_index=True
            )
            
            # Botão exportar (bônus!)
            csv = df.to_csv(index=False)
            st.download_button("📥 Baixar como Excel/CSV", csv, "historico_lavagens.csv", "text/csv")
            
        else:
            st.info("📭 Nenhuma lavagem registrada ainda. Emita a primeira ordem!")

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido para FSJ Logística por Grok (xAI). Qualquer dúvida, pergunte aqui!*")