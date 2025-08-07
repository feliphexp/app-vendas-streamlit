import streamlit as st
import pandas as pd

# Título do Web App
st.title('Aplicativo de Consulta a Produtos')

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    # Leitura do arquivo CSV com Pandas
    try:
        df = pd.read_csv(uploaded_file)

        st.header('Consulta de Dados')

        # Filtros de consulta
        # Adapte 'Nome da Coluna para Nome' e 'Nome da Coluna para Produto'
        # para os nomes reais das colunas no seu arquivo CSV.
        nome_filtro = st.text_input('Filtrar por nome:')
        produto_filtro = st.text_input('Filtrar por produto:')

        # Lógica de filtragem
        df_filtrado = df

        if nome_filtro:
            # A busca é case-insensitive (não diferencia maiúsculas de minúsculas)
            df_filtrado = df_filtrado[df_filtrado['Nome da Coluna para Nome'].str.contains(nome_filtro, case=False, na=False)]

        if produto_filtro:
            df_filtrado = df_filtrado[df_filtrado['Nome da Coluna para Produto'].str.contains(produto_filtro, case=False, na=False)]


        # Exibição dos dados filtrados
        st.dataframe(df_filtrado)

        # Opcional: Exibir a tabela de dados completa
        if st.checkbox('Mostrar dados brutos'):
            st.subheader('Dados Brutos')
            st.write(df)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo CSV: {e}")