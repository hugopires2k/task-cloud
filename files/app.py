import os

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Sabor do Sertão", layout="wide")
st.title("Painel de Vendas: Sabor do Sertão")

CSV_PADRAO = "vendas_sabor_do_sertao.csv"
DIAS = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
        4: "Sexta", 5: "Sábado", 6: "Domingo"}
ORDEM_DIAS = list(DIAS.values())


def brl(valor: float) -> str:
    """Formata número como moeda brasileira: R$ 1.234,56"""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data
def carregar(arquivo):
    return pd.read_csv(arquivo, parse_dates=["data"])


# ---------------------------------------------------------------- Dados
arquivo = st.sidebar.file_uploader("Envie o CSV de vendas", type="csv")
if arquivo is None and os.path.exists(CSV_PADRAO):
    arquivo = CSV_PADRAO
    st.sidebar.caption(f"Usando o arquivo local `{CSV_PADRAO}`.")
if arquivo is None:
    st.info("Envie o arquivo para começar.")
    st.stop()

df_bruto = carregar(arquivo)

# ------------------------------------------------- Nível 1: Exploração
st.header("1. Exploração dos dados")
with st.expander("Ver exploração (dados brutos)", expanded=False):
    st.subheader("Primeiras linhas")
    st.dataframe(df_bruto.head(10))
    st.subheader("Resumo estatístico")
    st.dataframe(df_bruto.describe())
    st.subheader("Valores ausentes por coluna")
    ausentes = df_bruto.isna().sum().rename("ausentes").to_frame()
    st.dataframe(ausentes)

# Tratamento: preencher avaliações ausentes com a mediana
mediana_aval = df_bruto["avaliacao"].median()
df = df_bruto.copy()
df["avaliacao"] = df["avaliacao"].fillna(mediana_aval)
df["dia_semana"] = df["data"].dt.dayofweek.map(DIAS)

st.caption(
    f"Tratamento de `avaliacao`: {int(df_bruto['avaliacao'].isna().sum())} valores ausentes "
    f"foram preenchidos com a **mediana** ({mediana_aval:.0f}). Não removemos as linhas, "
    "porque elas têm preço, quantidade e total válidos e apagá-las reduziria o faturamento "
    "e o número de vendas. Escolhemos a mediana (e não a média) porque a nota é uma escala "
    "ordinal de 1 a 5 e a mediana sempre resulta em uma nota válida e não é afetada por "
    "valores extremos."
)

# ------------------------------------------------------ Nível 3: Filtros
st.sidebar.header("Filtros")
cidades = sorted(df["cidade"].unique())
categorias = sorted(df["categoria"].unique())
sel_cidades = st.sidebar.multiselect("Cidade", cidades, default=cidades)
sel_categorias = st.sidebar.multiselect("Categoria", categorias, default=categorias)

data_min, data_max = df["data"].min().date(), df["data"].max().date()
periodo = st.sidebar.date_input(
    "Período", value=(data_min, data_max), min_value=data_min, max_value=data_max
)
if not (isinstance(periodo, (tuple, list)) and len(periodo) == 2):
    st.warning("Selecione a data inicial e a data final no filtro de período.")
    st.stop()
inicio, fim = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])

filtrado = df[
    df["cidade"].isin(sel_cidades)
    & df["categoria"].isin(sel_categorias)
    & df["data"].between(inicio, fim)
].copy()

if filtrado.empty:
    st.warning("Nenhuma venda encontrada com os filtros selecionados.")
    st.stop()

# ----------------------------------------------------- Nível 2: Indicadores
st.header("2. Indicadores")
faturamento = filtrado["total"].sum()
n_vendas = len(filtrado)
ticket_medio = faturamento / n_vendas
aval_media = filtrado["avaliacao"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Faturamento total", brl(faturamento))
c2.metric("Número de vendas", f"{n_vendas:,}".replace(",", "."))
c3.metric("Ticket médio", brl(ticket_medio))
c4.metric("Avaliação média", f"{aval_media:.2f} / 5")

# -------------------------------------------------------- Nível 4: Gráficos
st.header("3. Visualizações")
aba_mensal, aba_cidade, aba_produtos, aba_pagto, aba_calor, aba_livre = st.tabs(
    ["Faturamento mensal", "Por cidade", "Top 5 produtos",
     "Formas de pagamento", "Mapa de calor", "Explorador livre"]
)

with aba_mensal:
    mensal = (
        filtrado.groupby(filtrado["data"].dt.to_period("M"))["total"].sum()
    )
    mensal.index = mensal.index.astype(str)
    mensal = mensal.reset_index()
    mensal.columns = ["mes", "faturamento"]
    fig = px.line(mensal, x="mes", y="faturamento", markers=True,
                  title="Faturamento mensal",
                  labels={"mes": "Mês", "faturamento": "Faturamento (R$)"})
    st.plotly_chart(fig)

with aba_cidade:
    por_cidade = (
        filtrado.groupby("cidade")["total"].sum().sort_values(ascending=False).reset_index()
    )
    fig = px.bar(por_cidade, x="cidade", y="total", text_auto=".2s",
                 title="Faturamento por cidade",
                 labels={"cidade": "Cidade", "total": "Faturamento (R$)"})
    st.plotly_chart(fig)

with aba_produtos:
    top5 = (
        filtrado.groupby("produto")["quantidade"].sum().nlargest(5).sort_values().reset_index()
    )
    fig = px.bar(top5, x="quantidade", y="produto", orientation="h", text="quantidade",
                 title="Top 5 produtos mais vendidos (em quantidade)",
                 labels={"quantidade": "Unidades vendidas", "produto": "Produto"})
    st.plotly_chart(fig)

with aba_pagto:
    pagto = filtrado.groupby("pagamento")["total"].sum().reset_index()
    fig = px.pie(pagto, names="pagamento", values="total", hole=0.4,
                 title="Participação das formas de pagamento no faturamento")
    st.plotly_chart(fig)

with aba_calor:
    fig = px.density_heatmap(
        filtrado, x="dia_semana", y="hora", z="total", histfunc="sum",
        category_orders={"dia_semana": ORDEM_DIAS},
        nbinsy=filtrado["hora"].nunique(),
        title="Faturamento por dia da semana e hora",
        labels={"dia_semana": "Dia da semana", "hora": "Hora", "total": "Faturamento (R$)"},
    )
    st.plotly_chart(fig)

# ------------------------------------------- Bônus: Explorador livre
with aba_livre:
    st.write("Envie qualquer CSV (ou use os dados filtrados do painel) e monte seu gráfico.")
    csv_livre = st.file_uploader("CSV para explorar (opcional)", type="csv", key="livre")
    base = pd.read_csv(csv_livre) if csv_livre is not None else filtrado.drop(columns=["dia_semana"])

    colunas = list(base.columns)
    col_x, col_y, col_tipo, col_agg = st.columns(4)
    eixo_x = col_x.selectbox("Eixo X", colunas, key="eixo_x")
    eixo_y = col_y.selectbox("Eixo Y", colunas, index=min(1, len(colunas) - 1), key="eixo_y")
    tipo = col_tipo.selectbox(
        "Tipo de gráfico", ["Barras", "Linha", "Dispersão", "Histograma", "Boxplot"], key="tipo"
    )
    agregacao = col_agg.selectbox(
        "Agregação (barras/linha)", ["soma", "média", "contagem"], key="agg"
    )
    mapa_agg = {"soma": "sum", "média": "mean", "contagem": "count"}

    try:
        if tipo in ("Barras", "Linha"):
            dados = base.groupby(eixo_x)[eixo_y].agg(mapa_agg[agregacao]).reset_index()
            func = px.bar if tipo == "Barras" else px.line
            fig = func(dados, x=eixo_x, y=eixo_y,
                       title=f"{agregacao.capitalize()} de {eixo_y} por {eixo_x}")
        elif tipo == "Dispersão":
            fig = px.scatter(base, x=eixo_x, y=eixo_y, title=f"{eixo_y} vs {eixo_x}")
        elif tipo == "Histograma":
            fig = px.histogram(base, x=eixo_x, title=f"Distribuição de {eixo_x}")
        else:
            fig = px.box(base, x=eixo_x, y=eixo_y, title=f"{eixo_y} por {eixo_x}")
        st.plotly_chart(fig)
    except Exception as erro:
        st.error(f"Não foi possível montar este gráfico com as colunas escolhidas: {erro}")

# ------------------------------------------- Nível 5: Insights e exportação
st.header("4. Insights para a gestão")

cidade_top = filtrado.groupby("cidade")["total"].sum().idxmax()
part_cidade = filtrado.groupby("cidade")["total"].sum().max() / faturamento
prod_top = filtrado.groupby("produto")["total"].sum().idxmax()
cat_top = filtrado.groupby("categoria")["total"].sum().idxmax()
hora_pico = filtrado.groupby("hora")["total"].sum().idxmax()
dia_pico = filtrado.groupby("dia_semana")["total"].sum().idxmax()
pagto_top = filtrado.groupby("pagamento")["total"].sum().idxmax()
part_pagto = filtrado.groupby("pagamento")["total"].sum().max() / faturamento
mes_top = filtrado.groupby(filtrado["data"].dt.to_period("M"))["total"].sum().idxmax()

st.markdown(
    f"""
1. **Onde vendemos mais:** **{cidade_top}** lidera com {part_cidade:.1%} do faturamento do
   recorte atual. Vale priorizar estoque e equipe nessa unidade e investigar por que as
   demais cidades ficam atrás.
2. **O que e quando vendemos mais:** o produto de maior faturamento é **{prod_top}**, e a
   categoria campeã é **{cat_top}**. O horário de pico é às **{hora_pico}h** e o melhor dia
   da semana é **{dia_pico}**; o mês de maior receita foi **{mes_top}**. Esses momentos pedem
   reforço de atendimento.
3. **Como os clientes pagam:** **{pagto_top}** é a forma mais usada, com {part_pagto:.1%} do
   faturamento. Isso indica que priorizar a estabilidade do Pix e negociar taxas de
   cartão tem mais impacto financeiro do que o caixa em dinheiro.
"""
)

st.download_button(
    "Baixar CSV filtrado",
    data=filtrado.drop(columns=["dia_semana"]).to_csv(index=False).encode("utf-8"),
    file_name="vendas_filtradas.csv",
    mime="text/csv",
)
