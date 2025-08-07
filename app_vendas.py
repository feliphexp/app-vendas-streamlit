import streamlit as st
import pandas as pd
from fpdf import FPDF
import urllib.parse

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="Sistema de Vendas",
    page_icon="🛒",
    layout="wide"
)

# --- FUNÇÕES AUXILIARES ---
def formatar_preco(valor):
    """Formata um número como moeda BRL."""
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def gerar_pdf(nome_cliente, carrinho, total):
    """Gera um PDF com os detalhes do pedido."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Detalhes do Pedido', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f'Cliente: {nome_cliente}', 0, 1)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(110, 10, 'Produto', 1)
    pdf.cell(25, 10, 'Qtd', 1, 0, 'C')
    pdf.cell(25, 10, 'V. Unit.', 1, 0, 'C')
    pdf.cell(30, 10, 'V. Total', 1, 1, 'C')
    pdf.set_font("Arial", '', 10)
    for item, detalhes in carrinho.items():
        item_encoded = item.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(110, 10, item_encoded, 1)
        pdf.cell(25, 10, str(detalhes['quantidade']), 1, 0, 'C')
        pdf.cell(25, 10, formatar_preco(detalhes['preco']), 1, 0, 'R')
        pdf.cell(30, 10, formatar_preco(detalhes['preco'] * detalhes['quantidade']), 1, 1, 'R')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(160, 10, 'Total:', 1, 0, 'R')
    pdf.cell(30, 10, formatar_preco(total), 1, 1, 'R')
    return pdf.output(dest='S').encode('latin1')

# --- INICIALIZAÇÃO E GERENCIAMENTO DE ESTADO ---
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

if 'df_produtos' not in st.session_state:
    try:
        df = pd.read_csv('vendas_arredondado.csv')
        df.columns = ['Descricao', 'V.Venda']
        df['V.Venda'] = pd.to_numeric(df['V.Venda'], errors='coerce')
        df.dropna(subset=['V.Venda'], inplace=True)
        st.session_state.df_produtos = df
    except FileNotFoundError:
        st.error("Arquivo 'vendas_arredondado.csv' não encontrado. Por favor, coloque o arquivo na mesma pasta do script.")
        st.stop()

# --- BARRA LATERAL (SIDEBAR) PARA GERENCIAMENTO ---
st.sidebar.header("Gerenciar Itens")

with st.sidebar.expander("➕ Adicionar Novo Produto"):
    with st.form("novo_produto_form", clear_on_submit=True):
        novo_nome = st.text_input("Nome do Produto")
        novo_preco = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Adicionar")
        if submitted and novo_nome:
            novo_produto = pd.DataFrame([{'Descricao': novo_nome, 'V.Venda': novo_preco}])
            st.session_state.df_produtos = pd.concat([st.session_state.df_produtos, novo_produto], ignore_index=True)
            st.success(f"Produto '{novo_nome}' adicionado!")

with st.sidebar.expander("✏️ Editar Produto da Lista"):
    produtos_list = st.session_state.df_produtos['Descricao'].tolist()
    produto_para_editar = st.selectbox("Selecione um produto", [""] + sorted(produtos_list), key="sel_edit")

    if produto_para_editar:
        produto_atual = st.session_state.df_produtos[st.session_state.df_produtos['Descricao'] == produto_para_editar].iloc[0]
        with st.form("editar_produto_form"):
            st.write(f"Editando: **{produto_para_editar}**")
            novo_nome_edit = st.text_input("Novo nome", value=produto_atual['Descricao'])
            novo_preco_edit = st.number_input("Novo preço", value=float(produto_atual['V.Venda']), format="%.2f")
            submitted_edit = st.form_submit_button("Salvar Alterações")
            if submitted_edit:
                idx = st.session_state.df_produtos.index[st.session_state.df_produtos['Descricao'] == produto_para_editar][0]
                st.session_state.df_produtos.at[idx, 'Descricao'] = novo_nome_edit
                st.session_state.df_produtos.at[idx, 'V.Venda'] = novo_preco_edit
                st.success(f"Produto '{produto_para_editar}' atuali