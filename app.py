    elif st.session_state.pagina == "pesquisa_usuarios":
        st.header("Lista de Funcionários")
        df = listar_usuarios()
        if not df.empty:
            # Remover coluna 'senha' da exibição
            df_display = df[['nome', 'email', 'data_cadastro', 'nivel']].copy()
            df_display.index = df['id']

            # Adicionar coluna com 3 pontinhos
            def make_menu(row_id):
                with st.expander("", expanded=False):
                    col1, col2 = st.columns(2)
                    if col1.button("Alterar", key=f"edit_{row_id}"):
                        st.session_state.editando = row_id
                        st.rerun()
                    if col2.button("Excluir", key=f"del_{row_id}", type="secondary"):
                        if st.session_state.get('confirmar_exclusao') == row_id:
                            # Excluir usuário
                            conn = sqlite3.connect('fsj_lavagens.db')
                            c = conn.cursor()
                            c.execute('DELETE FROM usuarios WHERE id = ?', (row_id,))
                            conn.commit()
                            conn.close()
                            st.success("Usuário excluído com sucesso!")
                            del st.session_state.confirmar_exclusao
                            st.rerun()
                        else:
                            st.session_state.confirmar_exclusao = row_id
                            st.warning("Clique novamente em 'Excluir' para confirmar.")
                            st.rerun()

            # Exibir tabela com menu
            for idx, row in df_display.iterrows():
                cols = st.columns([3, 3, 2, 2, 0.5])
                cols[0].write(row['nome'])
                cols[1].write(row['email'])
                cols[2].write(row['data_cadastro'])
                cols[3].write(row['nivel'].title())
                with cols[4]:
                    make_menu(idx)

            # Formulário de edição
            if 'editando' in st.session_state:
                user_id = st.session_state.editando
                user = df[df['id'] == user_id].iloc[0]
                st.markdown("---")
                st.subheader(f"Editando: {user['nome']}")
                with st.form("editar_usuario"):
                    novo_nome = st.text_input("Nome Completo", value=user['nome'])
                    novo_email = st.text_input("E-mail", value=user['email'])
                    nova_senha = st.text_input("Nova Senha (deixe em branco para manter)", type="password")
                    novo_nivel = st.selectbox("Nível", ["operador", "admin"], 
                                            index=0 if user['nivel'] == 'operador' else 1)
                    
                    col1, col2 = st.columns(2)
                    if col1.form_submit_button("Salvar Alterações"):
                        conn = sqlite3.connect('fsj_lavagens.db')
                        c = conn.cursor()
                        if nova_senha:
                            c.execute('UPDATE usuarios SET nome=?, email=?, senha=?, nivel=? WHERE id=?',
                                      (novo_nome, novo_email, nova_senha, novo_nivel, user_id))
                        else:
                            c.execute('UPDATE usuarios SET nome=?, email=?, nivel=? WHERE id=?',
                                      (novo_nome, novo_email, novo_nivel, user_id))
                        conn.commit()
                        conn.close()
                        st.success("Usuário atualizado!")
                        del st.session_state.editando
                        st.rerun()
                    
                    if col2.form_submit_button("Cancelar"):
                        del st.session_state.editando
                        st.rerun()

            st.download_button(
                "Baixar Lista (CSV)",
                df_display.to_csv(index=False).encode('utf-8'),
                "funcionarios.csv",
                "text/csv"
            )
        else:
            st.info("Nenhum usuário cadastrado.")
