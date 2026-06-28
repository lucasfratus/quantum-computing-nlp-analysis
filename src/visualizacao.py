import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from preprocessamento import (
    STOPWORDS_EXTRA,
    construir_stopwords,
    preprocessar,
    lematizacao,
    stemming,
)
from extracao_informacoes import limpar_texto_artigo, dividir_sentencas


RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"
PASTA_OBSERVACOES = RESULTADOS / "observacoes"
CAMINHO_ETAPA1 = RESULTADOS / "etapa1_resultados.json"
CAMINHO_RESUMO = PASTA_OBSERVACOES / "observacoes_resumo.json"


# lista de abordagens/tecnicas mais comuns no tema do corpus.
TECNICAS = [
    "quantum computing",
    "quantum machine learning",
    "machine learning",
    "quantum circuit",
    "quantum algorithm",
    "quantum neural network",
    "quantum recurrent neural network",
    "quantum support vector machine",
    "variational quantum algorithm",
    "variational quantum circuit",
    "hybrid quantum classical",
    "quantum optimization",
    "quantum annealing",
    "quantum key distribution",
    "post quantum cryptography",
    "feature selection",
    "intrusion detection",
    "reinforcement learning",
    "neural network",
    "transfer learning",
    "blockchain",
]


# Termos que aparecem por causa de figura/tabela ou para encontrar trabalhos futuros
TERMOS_RUIDO_GERAL = {
    "fig",
    "figure",
    "table",
}

TERMOS_RUIDO_FUTUROS = {
    "future",
    "research",
    "direction",
    "directions",
    "work",
    "may",
    "will",
    "study",
    "studies",
    "further",
}

PADROES_FUTURO = [
    "future work",
    "future research",
    "future studies",
    "future study",
    "future direction",
    "future directions",
    "further research",
    "further studies",
    "in future",
    "as future work",
    "future investigation",
    "future investigations",
]


def carregar_json(caminho: Path):
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(dados, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def salvar_csv(linhas: list[dict], caminho: Path, campos: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)


def preparar_texto_para_busca(texto: str) -> str:
    """Deixa o texto mais fácil de buscar, sem tentar fazer uma limpeza perfeita."""
    texto = limpar_texto_artigo(texto)
    texto = texto.lower()
    texto = texto.replace("–", "-").replace("—", "-")
    texto = re.sub(r"(?<=[a-z])\s*-\s+(?=[a-z])", "", texto)
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return " ".join(texto.split())


def obter_tokens_por_artigo(dados_etapa1: dict) -> dict[str, list[str]]:
    stop_words = construir_stopwords().union(STOPWORDS_EXTRA)
    tokens_por_artigo = {}

    for nome, info in dados_etapa1.get("artigos", {}).items():
        corpo = info.get("corpo", "")
        tokens = preprocessar(corpo, stop_words, lematizacao, stemming)
        tokens_por_artigo[nome] = tokens

    return tokens_por_artigo


def contar_palavras(tokens_por_artigo: dict[str, list[str]]) -> Counter:
    contagem = Counter()
    for tokens in tokens_por_artigo.values():
        contagem.update(tokens)
    return contagem


def remover_termos(contagem: Counter, termos_remover: set[str]) -> Counter:
    """Remove termos pouco informativos só das visualizações/resumos."""
    nova_contagem = contagem.copy()
    for termo in termos_remover:
        nova_contagem.pop(termo, None)
    return nova_contagem


def gerar_grafico_barras(contagem: Counter, caminho: Path, titulo: str, top_n: int = 15) -> None:
    itens = contagem.most_common(top_n)
    if not itens:
        return

    nomes = [item[0].replace("_", " ") for item in itens]
    valores = [item[1] for item in itens]

    plt.figure(figsize=(11, 5))
    plt.bar(nomes, valores)
    plt.title(titulo)
    plt.ylabel("Frequência")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(caminho, dpi=200)
    plt.close()


def gerar_nuvem_palavras(contagem: Counter, caminho: Path) -> None:
    """Gera uma nuvem. Se a biblioteca wordcloud não existir, faz uma versão simples."""
    frequencias = dict(contagem.most_common(80))
    if not frequencias:
        return

    try:
        from wordcloud import WordCloud

        nuvem = WordCloud(
            width=1200,
            height=800,
            background_color="white",
            collocations=False,
        ).generate_from_frequencies(frequencias)

        plt.figure(figsize=(12, 8))
        plt.imshow(nuvem, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(caminho, dpi=200)
        plt.close()
        return
    except Exception:
        pass

    # fallback
    maior = max(frequencias.values())
    palavras = list(frequencias.items())

    plt.figure(figsize=(12, 8))
    plt.axis("off")

    x = 0.03
    y = 0.92
    for palavra, freq in palavras:
        tamanho = 10 + 30 * (freq / maior)
        texto = palavra.replace("_", " ")
        plt.text(x, y, texto, fontsize=tamanho, transform=plt.gca().transAxes)
        x += 0.17 + len(texto) * 0.004
        if x > 0.82:
            x = 0.03
            y -= 0.11
        if y < 0.08:
            break

    plt.title("Nuvem de palavras geral")
    plt.tight_layout()
    plt.savefig(caminho, dpi=200)
    plt.close()


def contar_tecnicas(dados_etapa1: dict) -> Counter:
    contagem = Counter()

    for info in dados_etapa1.get("artigos", {}).values():
        texto = preparar_texto_para_busca(info.get("corpo", ""))
        for tecnica in TECNICAS:
            termo_busca = tecnica.replace("-", " ").lower()
            contagem[tecnica] += texto.count(termo_busca)

    # Remove técnicas que não apareceram nenhuma vez.
    return Counter({termo: qtd for termo, qtd in contagem.items() if qtd > 0})


def descobrir_ano(nome_arquivo: str, corpo: str) -> str:
    """
    Tenta descobrir o ano do artigo.
    Primeiro uso o nome do arquivo, porque vários PDFs do corpus têm 025/026 no nome.
    Depois olho o começo do texto do artigo.
    """
    if "-026-" in nome_arquivo or "026-" in nome_arquivo:
        return "2026"
    if "-025-" in nome_arquivo or "025-" in nome_arquivo:
        return "2025"

    inicio = corpo[:5000]
    anos = re.findall(r"\b20(?:1[4-9]|2[0-9])\b", inicio)
    if anos:
        return max(anos)

    return "ano_nao_identificado"


def calcular_evolucao_temporal(dados_etapa1: dict, tokens_por_artigo: dict[str, list[str]]) -> tuple[dict, list[str]]:
    contagem_por_ano = defaultdict(Counter)
    ano_por_artigo = {}

    for nome, info in dados_etapa1.get("artigos", {}).items():
        ano = descobrir_ano(nome, info.get("corpo", ""))
        ano_por_artigo[nome] = ano
        contagem_por_ano[ano].update(tokens_por_artigo.get(nome, []))

    geral = Counter()
    for contagem in contagem_por_ano.values():
        geral.update(contagem)

    termos_acompanhados = [termo for termo, _ in geral.most_common(8)]

    evolucao = {}
    for ano in sorted(contagem_por_ano):
        evolucao[ano] = {
            termo: contagem_por_ano[ano].get(termo, 0)
            for termo in termos_acompanhados
        }

    return {
        "ano_por_artigo": ano_por_artigo,
        "termos_acompanhados": termos_acompanhados,
        "frequencias_por_ano": evolucao,
    }, termos_acompanhados


def gerar_grafico_evolucao(evolucao: dict, termos: list[str], caminho: Path) -> None:
    anos = sorted(evolucao["frequencias_por_ano"])
    if not anos or not termos:
        return

    plt.figure(figsize=(11, 6))
    for termo in termos[:6]:
        valores = [evolucao["frequencias_por_ano"][ano].get(termo, 0) for ano in anos]
        plt.plot(anos, valores, marker="o", label=termo.replace("_", " "))

    plt.title("Evolução temporal dos termos mais frequentes")
    plt.xlabel("Ano")
    plt.ylabel("Frequência")
    plt.legend()
    plt.tight_layout()
    plt.savefig(caminho, dpi=200)
    plt.close()


def gerar_heatmap_artigo_termo(tokens_por_artigo: dict[str, list[str]], termos: list[str], caminho: Path) -> None:
    artigos = list(tokens_por_artigo.keys())
    if not artigos or not termos:
        return

    matriz = []
    for nome in artigos:
        contagem = Counter(tokens_por_artigo[nome])
        matriz.append([contagem.get(termo, 0) for termo in termos])

    plt.figure(figsize=(11, 7))
    plt.imshow(matriz, aspect="auto")
    plt.colorbar(label="Frequência")
    plt.xticks(range(len(termos)), [t.replace("_", " ") for t in termos], rotation=45, ha="right")
    plt.yticks(range(len(artigos)), artigos)
    plt.title("Heatmap artigo x termo")
    plt.tight_layout()
    plt.savefig(caminho, dpi=200)
    plt.close()


def extrair_trabalhos_futuros(dados_etapa1: dict) -> tuple[list[dict], Counter]:
    trechos = []
    termos_futuros = Counter()
    stop_words = construir_stopwords().union(STOPWORDS_EXTRA)

    for nome, info in dados_etapa1.get("artigos", {}).items():
        corpo = limpar_texto_artigo(info.get("corpo", ""))
        # Normalmente fica no fim do artigo
        fim = corpo[-12000:]
        sentencas = dividir_sentencas(fim)

        for sentenca in sentencas:
            s_minuscula = sentenca.lower()
            if any(padrao in s_minuscula for padrao in PADROES_FUTURO):
                item = {
                    "arquivo": nome,
                    "trecho": sentenca,
                }
                trechos.append(item)
                tokens = preprocessar(sentenca, stop_words, lematizacao, stemming)
                termos_futuros.update(tokens)

    return trechos, termos_futuros


def salvar_trechos_futuros_txt(trechos: list[dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for item in trechos:
            arquivo.write(f"Arquivo: {item['arquivo']}\n")
            arquivo.write(item["trecho"] + "\n")
            arquivo.write("-" * 80 + "\n")


def main() -> None:
    print("\nGerando visualizações e observações do corpus\n")

    if not CAMINHO_ETAPA1.exists():
        raise FileNotFoundError(f"Execute a Etapa 1 antes. Arquivo não encontrado: {CAMINHO_ETAPA1}")

    PASTA_OBSERVACOES.mkdir(parents=True, exist_ok=True)
    dados_etapa1 = carregar_json(CAMINHO_ETAPA1)

    tokens_por_artigo = obter_tokens_por_artigo(dados_etapa1)
    contagem_palavras = contar_palavras(tokens_por_artigo)
    contagem_tecnicas = contar_tecnicas(dados_etapa1)
    evolucao, termos_evolucao = calcular_evolucao_temporal(dados_etapa1, tokens_por_artigo)
    trechos_futuros, termos_futuros = extrair_trabalhos_futuros(dados_etapa1)

    # deixa os graficos mais limpos
    contagem_palavras_visual = remover_termos(contagem_palavras, TERMOS_RUIDO_GERAL)
    termos_futuros_visual = remover_termos(termos_futuros, TERMOS_RUIDO_FUTUROS)

    caminho_palavras = PASTA_OBSERVACOES / "palavras_mais_citadas.png"
    caminho_nuvem = PASTA_OBSERVACOES / "nuvem_palavras_geral.png"
    caminho_tecnicas = PASTA_OBSERVACOES / "tecnicas_mais_mencionadas.png"
    caminho_evolucao = PASTA_OBSERVACOES / "evolucao_temporal_termos.png"
    caminho_heatmap = PASTA_OBSERVACOES / "heatmap_artigo_termo.png"
    caminho_futuros = PASTA_OBSERVACOES / "termos_trabalhos_futuros.png"

    gerar_grafico_barras(contagem_palavras_visual, caminho_palavras, "Palavras mais citadas nos artigos", 15)
    gerar_nuvem_palavras(contagem_palavras_visual, caminho_nuvem)
    gerar_grafico_barras(contagem_tecnicas, caminho_tecnicas, "Técnicas mais mencionadas", 15)
    gerar_grafico_evolucao(evolucao, termos_evolucao, caminho_evolucao)
    gerar_heatmap_artigo_termo(tokens_por_artigo, termos_evolucao, caminho_heatmap)
    gerar_grafico_barras(termos_futuros_visual, caminho_futuros, "Termos em trechos de trabalhos futuros", 15)

    linhas_evolucao = []
    for ano, termos in evolucao["frequencias_por_ano"].items():
        for termo, frequencia in termos.items():
            linhas_evolucao.append({
                "ano": ano,
                "termo": termo,
                "frequencia": frequencia,
            })
    salvar_csv(linhas_evolucao, PASTA_OBSERVACOES / "evolucao_temporal_termos.csv", ["ano", "termo", "frequencia"])

    salvar_trechos_futuros_txt(trechos_futuros, PASTA_OBSERVACOES / "trechos_trabalhos_futuros.txt")

    resumo = {
        "palavras_mais_citadas": dict(contagem_palavras_visual.most_common(20)),
        "tecnicas_mais_mencionadas": dict(contagem_tecnicas.most_common(20)),
        "evolucao_temporal": evolucao,
        "trabalhos_futuros": {
            "quantidade_trechos": len(trechos_futuros),
            "termos_mais_frequentes": dict(termos_futuros_visual.most_common(20)),
            "trechos": trechos_futuros,
        },
        "visualizacoes_geradas": [
            str(caminho_palavras.relative_to(RAIZ)),
            str(caminho_nuvem.relative_to(RAIZ)),
            str(caminho_tecnicas.relative_to(RAIZ)),
            str(caminho_evolucao.relative_to(RAIZ)),
            str(caminho_heatmap.relative_to(RAIZ)),
            str(caminho_futuros.relative_to(RAIZ)),
        ],
    }
    salvar_json(resumo, CAMINHO_RESUMO)

    print(f"Resumo salvo em: {CAMINHO_RESUMO}")
    print("Visualizações geradas na pasta resultados/observacoes")


if __name__ == "__main__":
    main()
