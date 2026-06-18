import os
import re
import json

import nltk
from nltk.tokenize import sent_tokenize


from preprocessamento import carregar_artigos, separar_corpo_referencia

#nltk.download("punkt", quiet=True)
#nltk.download("punkt_tab", quiet=True)

DIRETORIO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRETORIO_PDFS = os.path.join(DIRETORIO_BASE, "artigos")
DIRETORIO_SAIDA = os.path.join(DIRETORIO_BASE, "resultados")
MAXIMO_SENTENCAS = 4 # máximo de sentenças extraídas por categoria


PALAVRAS_OBJETIVO = [
    "this paper aims", "this paper presents", "this paper proposes",
    "this paper introduces", "this study aims", "this study proposes",
    "this work aims", "this work proposes", "this work presents",
    "we aim", "we propose", "we present", "we introduce",
    "the objective", "the aim", "the purpose", "our goal",
    "in this paper, we", "in this work, we", "in this study, we",
]
 
PALAVRAS_PROBLEMA = [
    "however,", "the problem", "the challenge", "the issue",
    "is challenging", "remains challenging", "is difficult",
    "lack of", "limitation", "drawback", "suffers from",
    "existing methods", "current methods", "previous approaches",
    "has not been", "have not been", "cannot", "are limited",
    "a major challenge", "key challenge", "unfortunately",
]
 
PALAVRAS_METODO = [
    "we use", "we employ", "we utilize", "we adopt",
    "we implement", "we develop", "we design", "we evaluate",
    "our method", "our approach", "our framework",
    "the proposed method", "the proposed approach",
    "methodology", "experiment", "experiments", "evaluation",
    "we conduct", "we perform", "dataset", "simulation",
    "based on", "we measure", "we compare",
]
 
PALAVRAS_CONTRIBUICAO = [
    "contributes to", "our contribution", "our contributions",
    "the contribution", "the main contribution", "the key contribution",
    "we contribute", "the novelty", "novel contribution",
    "to the best of our knowledge", "for the first time",
    "we are the first", "first comprehensive",
]

NOMES_SECOES = {
    "abstract":   ["abstract"],
    "introducao": ["introduction"],
    "metodo":     ["method", "methodology", "methods", "proposed", "approach", "experimental"],
    "conclusao":  ["conclusion", "conclusions", "concluding remarks", "summary"],
}



def extrair_secao(texto: str, nomes: list[str]) -> str:
    """
    Localiza uma seção pelo nome do cabeçalho e retorna seu conteúdo.
    Percorre as linhas procurando pelo título da seção.
    """
    linhas = texto.splitlines()
    dentro_da_secao = False
    conteudo = []

    for linha in linhas:
        linha_lower = linha.strip().lower()

        # Verifica se a linha é o cabeçalho da seção procurada
        for nome in nomes:
            if nome in linha_lower and len(linha.strip()) < 60:
                dentro_da_secao = True
                break

        if not dentro_da_secao:
            continue

        # Quando encontra o início de outra seção numerada
        if dentro_da_secao and conteudo:
            eh_novo_cabecalho = (
                linha.strip() and
                len(linha.strip()) < 60 and
                linha.strip()[0].isdigit()
            )
            if eh_novo_cabecalho:
                break

        conteudo.append(linha)

    return "\n".join(conteudo).strip()



def extrair_sentencas(texto: str, palavras_chave: list[str]) -> list[str]:
    """
    Divide o texto em sentenças e retorna as que contêm
    alguma das palavras-chave, até o limite MAX_SENT.
    """
    sentencas  = sent_tokenize(texto)
    encontradas = []
 
    for sentenca in sentencas:
        sentenca_lower = sentenca.lower()
        for palavra in palavras_chave:
            if palavra in sentenca_lower:
                sentenca_limpa = re.sub(r'\s+', ' ', sentenca).strip()
                if len(sentenca_limpa) > 40:   # descarta fragmentos muito curtos
                    encontradas.append(sentenca_limpa)
                    break   # evita duplicata pela mesma sentença
 
        if len(encontradas) >= MAXIMO_SENTENCAS:
            break
 
    return encontradas


def extrair_informacoes(nome: str, texto: str) -> dict:
    """
    Extrai objetivo, problema, método e contribuições de um artigo.
    Cada categoria é buscada na seção mais provável de contê-la.
    """
    abstract = extrair_secao(texto, NOMES_SECOES["abstract"])
    introducao = extrair_secao(texto, NOMES_SECOES["introducao"])
    metodo = extrair_secao(texto, NOMES_SECOES["metodo"])
    conclusao  = extrair_secao(texto, NOMES_SECOES["conclusao"])
 
    # abstract + introdução
    if abstract or introducao:
        texto_intro = (abstract + "\n" + introducao).strip()
    else:
        texto_intro = texto[:3000]

    # método
    if metodo:
        texto_metodo = metodo
    else:
        texto_metodo = texto

    # contribuições: introdução + conclusão
    if introducao or conclusao:
        texto_contrib = (introducao + "\n" + conclusao).strip()
    else:
        texto_contrib = texto
 
    return {
        "arquivo": nome,
        "objetivo": extrair_sentencas(texto_intro,  PALAVRAS_OBJETIVO),
        "problema": extrair_sentencas(texto_intro,  PALAVRAS_PROBLEMA),
        "metodo": extrair_sentencas(texto_metodo, PALAVRAS_METODO),
        "contribuicoes": extrair_sentencas(texto_contrib, PALAVRAS_CONTRIBUICAO),
    }


def exibir_resultado(info: dict):
    print("\n")
    print(f"Artigo: {info['arquivo']}")

    campos = [
        ("Objetivo", "objetivo"),
        ("Problema", "problema"),
        ("Metodo", "metodo"),
        ("Contribuicoes", "contribuicoes"),
    ]

    for rotulo, chave in campos:
        print(f"\n{rotulo}:")
        sentencas = info[chave]
        if sentencas:
            for s in sentencas:
                if len(s) > 220:
                    trecho = s[:220] + "..."
                else:
                    trecho = s
                print(f"{trecho}")
        else:
            print("(nao encontrado)")


def main():
    caminho_json = os.path.join(DIRETORIO_SAIDA, "etapa1_resultados.json")

    with open(caminho_json, encoding="utf-8") as f:
        dados = json.load(f)

    resultados = []

    for nome, info in dados["artigos"].items():
        print(f"\\nProcessando: {nome}")
        corpo = info["corpo"]
        resultado = extrair_informacoes(nome, corpo)
        exibir_resultado(resultado)
        resultados.append(resultado)
        print(f"\n-------------------------------------------------\n")

    os.makedirs(DIRETORIO_SAIDA, exist_ok=True)
    caminho = os.path.join(DIRETORIO_SAIDA, "etapa2_resultados.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\nResultados salvos em: {caminho}")


if __name__ == "__main__":
    main()