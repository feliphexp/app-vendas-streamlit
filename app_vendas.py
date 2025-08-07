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
                st.success(f"Produto '{produto_para_editar}' atualizado!")
                # LINHA CORRIGIDA AQUI
                st.rerun()

# --- LAYOUT PRINCIPAL ---
st.title("🛒 Sistema de Vendas Dinâmico")
st.markdown("---")

col1, col2 = st.columns([2, 1.5])

with col1:
    st.header("📦 Produtos Disponíveis")
    busca = st.text_input("Buscar produto por nome:")
    df_filtrado = st.session_state.df_produtos[st.session_state.df_produtos['Descricao'].str.contains(busca, case=False, na=False)] if busca else st.session_state.df_produtos
    for index, row in df_filtrado.sort_values('Descricao').iterrows():
        expander = st.expander(f"{row['Descricao']} - {formatar_preco(row['V.Venda'])}")
        with expander:
            c1, c2 = st.columns([1, 2])
            with c1:
                quantidade = st.number_input("Qtd", min_value=1, value=1, step=1, key=f"qtd_{index}")
            with c2:
                if st.button("Adicionar ao Carrinho", key=f"add_{index}", use_container_width=True):
                    if row['Descricao'] in st.session_state.carrinho:
                        st.session_state.carrinho[row['Descricao']]['quantidade'] += quantidade
                    else:
                        st.session_state.carrinho[row['Descricao']] = {'quantidade': quantidade, 'preco': row['V.Venda']}
                    st.success(f"{quantidade}x '{row['Descricao']}' adicionado(s)!")
                    st.rerun() # Adicionado para melhor feedback ao usuário

with col2:
    st.header("🛒 Carrinho de Compras")
    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio.")
    else:
        total_pedido = 0
        for item, detalhes in list(st.session_state.carrinho.items()):
            c1, c2, c3 = st.columns([4, 3, 1])
            with c1:
                st.markdown(f"**{item}**")
                nova_qtd = st.number_input("Qtd", value=detalhes['quantidade'], min_value=1, key=f"qtd_cart_{item}")
                st.session_state.carrinho[item]['quantidade'] = nova_qtd
            with c2:
                novo_preco = st.number_input("Preço Unit. (R$)", value=float(detalhes['preco']), min_value=0.0, format="%.2f", key=f"price_cart_{item}")
                st.session_state.carrinho[item]['preco'] = novo_preco
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{item}"):
                    del st.session_state.carrinho[item]
                    # LINHA CORRIGIDA AQUI
                    st.rerun()

            st.markdown(f"Subtotal: `{formatar_preco(st.session_state.carrinho[item]['preco'] * st.session_state.carrinho[item]['quantidade'])}`")
            st.markdown("---")
            total_pedido += st.session_state.carrinho[item]['preco'] * st.session_state.carrinho[item]['quantidade']

        st.subheader(f"**Total do Pedido: {formatar_preco(total_pedido)}**")
        with st.expander("Finalizar Pedido", expanded=True):
            nome_cliente = st.text_input("Nome do Cliente:", "Cliente")
            texto_pedido_whatsapp = f"Olá, gostaria de fazer o seguinte pedido:\n\n*Cliente:* {nome_cliente}\n\n*Itens:*\n"
            for item, detalhes in st.session_state.carrinho.items():
                texto_pedido_whatsapp += f"- {detalhes['quantidade']}x {item} ({formatar_preco(detalhes['preco'])})\n"
            texto_pedido_whatsapp += f"\n*Total:* {formatar_preco(total_pedido)}"
            link_whatsapp = f"https://wa.me/?text={urllib.parse.quote(texto_pedido_whatsapp)}"
            
            b1, b2 = st.columns(2)
            b1.link_button("📲 Enviar por WhatsApp", link_whatsapp, use_container_width=True)
            pdf_bytes = gerar_pdf(nome_cliente, st.session_state.carrinho, total_pedido)
            b2.download_button(
                label="📄 Exportar PDF",
                data=pdf_bytes,
                file_name=f"pedido_{nome_cliente.replace(' ', '_').lower()}.pdf",
                mime='application/octet-stream',
                use_container_width=True
            )```

#### Passo 2: Envie a Correção para o GitHub

Agora, repita o processo que você já conhece:

1.  **Abra o GitHub Desktop.** Ele mostrará o arquivo `app_vendas.py` na lista de alterações.
2.  Escreva uma mensagem de commit (ex: **"Atualiza st.rerun e corrige bug de edição"**).
3.  Clique em **`Commit to main`**.
4.  Clique em **`Push origin`** para enviar as alterações.

O Streamlit Cloud irá detectar a mudança e reiniciar seu aplicativo com o código corrigido. A função de editar e remover itens do carrinho agora deve funcionar perfeitamente