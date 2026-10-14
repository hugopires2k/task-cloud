# Painel de Vendas: Sabor do Sertão

Painel interativo em **Streamlit** + **Plotly** que responde: onde, o quê, quando e
como os clientes compram na rede fictícia *Sabor do Sertão*
(Recife, Olinda, Caruaru, Petrolina e Garanhuns).

![Print do painel](print_painel.png)

> Substitua `print_painel.png` por um print do painel rodando.

## Como rodar

```bash
pip install -r requirements.txt
python gerar_dados.py          # gera vendas_sabor_do_sertao.csv
streamlit run app.py
```

## O que o painel tem

| Nível | Entrega |
|------|---------|
| 1 | Primeiras linhas, `describe()`, ausentes por coluna; `avaliacao` tratada com a **mediana** |
| 2 | 4 KPIs: faturamento, nº de vendas, ticket médio, avaliação média |
| 3 | Filtros na lateral: cidade, categoria e período (afetam KPIs e gráficos) |
| 4 | Gráficos em abas: mensal (linha), cidade (barras), top 5 produtos (barras horizontais), pagamento (pizza) e mapa de calor dia × hora |
| 5 | 3 insights dinâmicos + botão para baixar o CSV filtrado |
| Bônus | Aba **Explorador livre**: qualquer CSV, escolha de eixos X/Y e tipo de gráfico |

## Publicar no Streamlit Community Cloud

1. Suba `app.py`, `gerar_dados.py`, `requirements.txt`, `README.md` **e o CSV gerado** para um repositório público no GitHub.
2. Acesse https://share.streamlit.io e entre com o GitHub.
3. Clique em **Create app**, escolha o repositório, branch `main` e o arquivo `app.py`.
4. Clique em **Deploy** e cole o link do app aqui:

**Link do app:** _(cole aqui)_

## Autores

Dupla: _(nomes)_
