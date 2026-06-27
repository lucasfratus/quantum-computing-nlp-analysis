"""
Etapa 2 - Extração de informações dos artigos.
Essa etapa procura frases que pareçam indicar:
objetivo, problema, método e contribuições do artigo.

Como o trabalho não permite usar modelos prontos de IA/ML, a extração é feita
com regras simples: procurar seções do artigo, separar sentenças e dar uma
pontuação para frases que tenham certos termos/padrões.
"""

import json
import os
import re
from dataclasses import dataclass

DIRETORIO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRETORIO_SAIDA = os.path.join(DIRETORIO_BASE, "resultados")

# Limite de frases salvas em cada campo.
# Retorna poucos trechos para diminuir falso positivo.
MAX_SENTENCAS = {
    "objetivo": 3,
    "problema": 4,
    "metodo": 4,
    "contribuicoes": 5,
}

ROTULOS = {
    "objetivo": "Objetivo",
    "problema": "Problema",
    "metodo": "Metodo",
    "contribuicoes": "Contribuicoes",
}

# Títulos que apareceram com frequência nos PDFs usados.
# Não cobre todos os artigos possíveis, mas cobre bem o corpus do trabalho.
TITULOS_SECAO = {
    "abstract": ["abstract"],
    "introducao": [
        "introduction",
        "background",
        "problem formulation",
        "motivation",
    ],
    "metodo": [
        "method",
        "methods",
        "methodology",
        "materials and methods",
        "proposed method",
        "proposed approach",
        "proposed framework",
        "proposed model",
        "proposed system",
        "framework",
        "implementation",
        "experimental setup",
        "experiment setup",
        "experiments",
        "simulation setup",
        "evaluation",
        "performance evaluation",
        "data processing",
    ],
    "conclusao": [
        "conclusion",
        "conclusions",
        "conclusion and future scope",
        "concluding remarks",
        "discussion",
        "results and discussion",
        "summary",
        "future work",
    ],
}

TODOS_TITULOS = sorted(
    {titulo for lista in TITULOS_SECAO.values() for titulo in lista}
    | {
        "results",
        "related work",
        "preliminaries",
        "author contributions",
        "data availability",
        "references",
        "acknowledgements",
        "funding",
    },
    key=len,
    reverse=True,
)

# Regras principais de busca.
# A maioria está em regex porque o texto extraído de PDF vem com variações
# de espaço e escrita.
# As regras  ficaram concentradas aqui para ficar facilitar a modularidade do código.
PADROES = {
    "objetivo": [
        r"\bthis\s+(paper|study|work|article|research)\s+(aims?|seeks?|proposes?|presents?|introduces?|explores?|investigates?|addresses?|develops?|describes?|examines?)\b",
        r"\bwe\s+(aim|seek|propose|present|introduce|explore|investigate|address|develop|describe|examine|consider)\b",
        r"\b(the|our|main)\s+(main\s+)?(objective|objectives|aim|goal|purpose)\b",
        r"\bto\s+(address|overcome|bridge|solve|tackle|mitigate)\s+(these|this|the)\s+(challenge|challenges|gap|issue|issues|problem|problems|limitation|limitations)\b",
        r"\bhere\s+we\s+(describe|present|propose|introduce|develop)\b",
        r"\bthe\s+proposed\s+.+\s+(integrates|utilizes|combines|models|aims|seeks)\b",
        r"\bthe\s+goal\s+is\s+to\b",
    ],
    "problema": [
        r"\bhowever\b",
        r"\bdespite\b",
        r"\balthough\b",
        r"\bnevertheless\b",
        r"\bnonetheless\b",
        r"\b(challenge|challenges|problem|problems|issue|issues|limitation|limitations|drawback|drawbacks|gap|gaps|bottleneck|constraint|constraints|overhead|risk|risks|threat|threats|vulnerability|vulnerabilities)\b",
        r"\b(lack|lacks|insufficient|difficult|hinder|hinders|hindered|limited|scarce|noisy|unstable|cannot|not feasible|not been|remain|remains|suffer|suffers|struggle|struggles|costly)\b",
        r"\bto\s+the\s+best\s+of\s+our\s+knowledge\b",
    ],
    "metodo": [
        r"\bwe\s+(use|used|employ|employed|utilize|utilized|adopt|adopted|implement|implemented|develop|developed|design|designed|evaluate|evaluated|conduct|conducted|perform|performed|compare|compared|measure|measured|train|trained|test|tested|encode|encoded|extract|extracted|simulate|simulated|validate|validated|integrate|integrated|combine|combined|apply|applied|consider|considered|propose|proposed)\b",
        r"\b(the|our|proposed)\s+(method|approach|framework|model|algorithm|workflow|architecture|strategy|scheme|system)\s+(uses?|utilizes?|employs?|combines?|integrates?|consists|includes|is based|is implemented|leverages|performs|adopts|contains|models)\b",
        r"\b(is|are|was|were)\s+(used|conducted|implemented|trained|evaluated|applied|encoded|extracted|simulated|validated|performed|generated|optimized|computed|represented|arranged)\b",
        r"\b(experiments?|simulations?|evaluation|benchmark|training|testing|dataset|datasets|workflow|pre[- ]?processing|feature extraction|encoding|protocol|algorithm|framework|qiskit|pennylane|matlab|cloudsim|prisma)\b",
        r"\b(first|second|third|finally|next),?\s+(a|the|selected|quantum|classical|model|features?|dataset|circuit|workflow|algorithm)\b",
        r"\busing\s+.+\b(qiskit|pennylane|matlab|cloudsim|simulator|dataset|protocol|algorithm|framework|prisma)\b",
        r"\bto\s+this\s+end\b",
        r"\bfollowing\s+the\s+.+\s+methodology\b",
        r"\bthis\s+enabled\s+the\s+analysis\b",
        r"\bthe\s+proposed\s+framework\s+is\s+based\b",
        r"\bemploys\s+an\s+enhanced\b",
        r"\bis\s+conducted\s+through\b",
        r"\bthe\s+framework\s+uses\b",
        r"\bsignature\s+protocol\s+is\s+used\b",
        r"\bPCA\s+based\s+dimensionality\s+reduction\b",
        r"\bthe\s+proposed\s+methods\s+are\s+evaluated\b",
    ],
    "contribuicoes": [
        r"\bthe\s+main\s+contributions?\b",
        r"\bour\s+(main\s+)?contributions?\s+(are|is)\b",
        r"\bthis\s+(paper|study|work|review|article)\s+contributes\b",
        r"\bthe\s+review\s+contributes\b",
        r"\bthe\s+contributions?\s+(of\s+this|are|is)\b",
        r"\bthe\s+major\s+contributions?\b",
        r"\bwe\s+make\s+the\s+following\s+contributions?\b",
        r"\bour\s+contribution\s+is\b",
        r"\b(first|second|third)\s+(major\s+)?contribution\b",
        r"\bthe\s+novelty\s+involves\b",
        r"\bwe\s+propose\s+.+\bnovel\b",
        r"\bthis\s+novel\s+model\b",
        r"\b(the security analysis demonstrates|our .{0,80} outperforms|proposed .{0,80} outperforms|significantly outperforms its peers)\b",
        r"\bas\s+a\s+result,?\s+our\s+framework\b",
        r"\bby\s+minimizing\s+.+\bthe\s+proposed\s+methods\b",
        r"\badditionally,?\s+this\s+(review|paper|study|work)\s+introduces\b",
        r"\bthese\s+contributions\s+aim\b",
        r"\bthe\s+insights\s+generated\b",
    ],
}

PADROES = {
    categoria: [re.compile(padrao, re.IGNORECASE) for padrao in padroes]
    for categoria, padroes in PADROES.items()
}

# Termos que aumentam a pontuação da sentença quando aparecem.
REFORCOS = {
    "objetivo": [
        "aim", "objective", "purpose", "goal", "propose", "present",
        "introduce", "to address", "to overcome", "to bridge", "develop",
    ],
    "problema": [
        "however", "challenge", "limitation", "gap", "problem", "limited",
        "difficult", "threat", "insufficient", "overhead", "struggle",
        "noisy", "unstable", "costly",
    ],
    "metodo": [
        "dataset", "experiment", "workflow", "framework", "method",
        "algorithm", "simulation", "implemented", "used", "evaluated",
        "trained", "qiskit", "pennylane", "matlab", "cloudsim", "prisma",
        "encoding", "protocol", "pre-processing", "preprocessing",
    ],
    "contribuicoes": [
        "contribution", "contributes", "novel", "first", "second", "third",
        "propose", "introduce", "improve", "enhance", "outperforms",
        "superior", "advances", "novelty", "guide", "potential",
    ],
}

# Coisas que costumam vir de cabeçalho, rodapé, figuras ou metadados do PDF.
TERMOS_LIXO = [
    "table ",
    "fig.",
    "figure ",
    " page ",
    "publisher",
    "copyright",
    "creative commons",
    "contents lists available",
    "journal homepage",
    "received ",
    "accepted ",
    "published",
    "correspondence",
    "author contributions",
    "data availability",
    "github repository",
    "key performance metrics",
    "supplementary information",
    "http://",
    "https://",
    "doi.org",
    "www.",
]

TERMOS_RELACIONADOS = [
    "related work",
    "previous studies",
    "previous work",
    "existing studies",
    "literature review",
    "survey on",
]


# Alguns PDFs quebraram palavras no meio. Foi colocado apenas os casos
# que apareceram de fato durante os testes.
QUEBRAS_COMUNS = {
    r"\bal\s+gorithm": "algorithm",
    r"\bal\s+gorithms": "algorithms",
    r"\bcyberse\s+curity": "cybersecurity",
    r"\bmethodo\s+logical": "methodological",
    r"\bmethodo\s+logy": "methodology",
    r"\bquan\s+tum": "quantum",
    r"\bclassi\s+cal": "classical",
    r"\barti\s+ficial": "artificial",
    r"\bintel\s+ligence": "intelligence",
    r"\bcom\s+puting": "computing",
    r"\bexperi\s+ments": "experiments",
    r"\beffi\s+cient": "efficient",
    r"\beffi\s+ciency": "efficiency",
    r"\bscal\s+ability": "scalability",
    r"\blimita\s+tions": "limitations",
    r"\binfra\s+structure": "infrastructure",
}


def corrigir_quebras_pdf(texto: str) -> str:
    """Arruma alguns problemas que quebram a leitura dos PDFs."""
    substituicoes = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb00": "ff",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\x0c": "\n",
        "–": "-",
        "—": "-",
    }
    for antigo, novo in substituicoes.items():
        texto = texto.replace(antigo, novo)

    # Ex: cyberse - curity -> cybersecurity
    texto = re.sub(r"(?<=[A-Za-z])\s+-\s+(?=[A-Za-z])", "", texto)
    # Ex: quan-\ntum -> quantum
    texto = re.sub(r"(?<=[A-Za-z])-\s*\n\s*(?=[A-Za-z])", "", texto)

    for padrao, correcao in QUEBRAS_COMUNS.items():
        texto = re.sub(padrao, correcao, texto, flags=re.IGNORECASE)
    return texto


@dataclass
class SentencaCandidata:
    texto: str
    secao: str
    posicao: int


def limpar_linha_pdf(linha: str) -> str | None:
    """Remove uma linha quando ela parece ser ruído do PDF."""
    linha = linha.strip()
    if not linha:
        return ""

    linha_minuscula = linha.lower()

    if re.fullmatch(r"\d{1,4}", linha):
        return None
    if re.fullmatch(r"[\d\s().,:;v\-]+", linha):
        return None
    if "page " in linha_minuscula and " of " in linha_minuscula:
        return None
    if "scientific reports" in linha_minuscula and "doi" in linha_minuscula:
        return None
    if "npj quantum information" in linha_minuscula:
        return None
    if "epj quantum technology" in linha_minuscula and "page" in linha_minuscula:
        return None
    if "discover computing" in linha_minuscula and "page" in linha_minuscula:
        return None
    if "discover internet of things" in linha_minuscula and "page" in linha_minuscula:
        return None
    if "www.nature.com" in linha_minuscula:
        return None
    if linha_minuscula == "open":
        return None
    if "©" in linha or "creative commons" in linha_minuscula:
        return None
    if "e-mail" in linha_minuscula or "email:" in linha_minuscula or "@" in linha:
        return None
    if "corresponding author" in linha_minuscula:
        return None
    if "received:" in linha_minuscula or "accepted:" in linha_minuscula:
        return None

    return linha


def limpar_texto_artigo(texto: str) -> str:
    """Realiza uma limpeza antes de procurar as sentenças."""
    texto = corrigir_quebras_pdf(texto)

    linhas_limpas = []
    for linha in texto.splitlines():
        linha_limpa = limpar_linha_pdf(linha)
        if linha_limpa is not None:
            linhas_limpas.append(linha_limpa)

    texto = "\n".join(linhas_limpas)
    texto = corrigir_quebras_pdf(texto)

    # Junta palavras quebradas por hifenização no fim da linha.
    texto = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", texto)

    # Remove marcadores numéricos de página que aparecem no meio de palavras:
    # ex: "stud123\n...\nies" -> "studies" depois da remoção do cabeçalho.
    texto = re.sub(r"(?<=[A-Za-z])\s*\d{1,4}\s*\n\s*(?=[a-z])", "", texto)

    # Junta quebras de linha dentro de palavras, mas preserva separação comum.
    texto = re.sub(r"(?<=[a-z])\s*\n\s*(?=[a-z])", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def limpar_sentenca(texto: str) -> str:
    texto = corrigir_quebras_pdf(texto)
    texto = limpar_texto_artigo(texto)
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+([,.;:])", r"\1", texto)
    texto = re.sub(r"\[\s+", "[", texto)
    texto = re.sub(r"\s+\]", "]", texto)
    texto = re.sub(r"\(\s+", "(", texto)
    texto = re.sub(r"\s+\)", ")", texto)
    return texto.strip()


def dividir_sentencas(texto: str) -> list[str]:
    """Divide o texto em frases sem depender do tokenizador do NLTK."""
    texto = limpar_sentenca(texto)
    partes = re.split(
        r"(?<=[.!?])\s+(?=(?:\d+\s+[A-Z]|[A-Z]|To\b|However\b|Despite\b|Although\b|In\b|This\b|The\b|We\b|Our\b|Furthermore\b|Additionally\b|Hence\b|Therefore\b|Unlike\b|First\b|Second\b|Third\b|Finally\b|Next\b|Each\b|Through\b|Conventional\b|Current\b|Deep\b|Quantum\b|As\b|A\b|An\b|By\b))",
        texto,
    )
    return [limpar_sentenca(parte) for parte in partes if parte.strip()]


def normalizar_titulo(linha: str) -> str | None:
    linha = linha.strip()
    if not linha or len(linha) > 90:
        return None

    sem_numero = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s+", "", linha)
    sem_numero = re.sub(r"\s+", " ", sem_numero)
    sem_numero = sem_numero.strip().lower().strip(":.-")

    for titulo in TODOS_TITULOS:
        if sem_numero == titulo:
            return titulo
        if sem_numero.startswith(titulo + " ") and len(sem_numero) <= len(titulo) + 30:
            return titulo
    return None


def mapear_secoes(texto: str) -> list[tuple[str, str]]:
    linhas = texto.splitlines()
    marcadores = []
    posicao = 0

    for linha in linhas:
        titulo = normalizar_titulo(linha)
        if titulo:
            marcadores.append((posicao, posicao + len(linha), titulo))
        posicao += len(linha) + 1

    secoes = []
    for indice, (_, fim_titulo, titulo) in enumerate(marcadores):
        proximo_inicio = marcadores[indice + 1][0] if indice + 1 < len(marcadores) else len(texto)
        conteudo = texto[fim_titulo:proximo_inicio].strip()
        if len(conteudo) > 30:
            secoes.append((titulo, conteudo))
    return secoes


def extrair_por_titulos(texto: str, grupo: str) -> str:
    titulos = set(TITULOS_SECAO[grupo])
    blocos = [conteudo for titulo, conteudo in mapear_secoes(texto) if titulo in titulos]
    return "\n".join(blocos).strip()


def candidatos_de_texto(texto: str, secao: str) -> list[SentencaCandidata]:
    candidatos = []
    posicao = 0
    for sentenca in dividir_sentencas(texto):
        candidatos.append(SentencaCandidata(sentenca, secao, posicao))
        posicao += len(sentenca) + 1
    return candidatos


def sentenca_valida(sentenca: str, categoria: str) -> bool:
    sentenca = limpar_sentenca(sentenca)
    palavras = sentenca.split()
    baixa = f" {sentenca.lower()} "

    if len(palavras) < 7 or len(palavras) > 95:
        return False
    if len(sentenca) < 45:
        return False
    if "|" in sentenca:
        return False
    if sum(c.isalpha() for c in sentenca) < 35:
        return False
    if len(re.findall(r"\d", sentenca)) > max(16, len(sentenca) // 7):
        return False
    if any(termo in baixa for termo in TERMOS_LIXO):
        return False
    if re.match(r"^\(?\d{4}\)?\s+", sentenca):
        return False

    # Evita marcar trabalhos relacionados como contribuição do artigo analisado.
    if categoria == "contribuicoes":
        if re.match(r"^\s*\[?\d+\]?\s*proposed\b", sentenca, re.IGNORECASE):
            return False
        if "proposed that" in baixa or "techniques such as" in baixa:
            return False
        if any(termo in baixa for termo in TERMOS_RELACIONADOS) and "our" not in baixa and "this" not in baixa:
            return False

    if categoria == "metodo":
        # Evita provas/protocolos muito específicos e trabalhos relacionados
        # quando eles aparecem antes das sentenças metodológicas principais.
        termos_prova = [" bob ", " alice ", " charlie ", " eavesdropping ", " doesn’t know ", " doesn't know "]
        if any(t in baixa for t in termos_prova):
            return False
        if " et al." in sentenca.lower() and any(v in baixa for v in [" introduced ", " proposed ", " presented "]):
            return False

    return True


def pontuar(candidato: SentencaCandidata, categoria: str) -> int:
    sentenca = candidato.texto
    baixa = sentenca.lower()
    pontos = 0

    for padrao in PADROES[categoria]:
        if padrao.search(sentenca):
            pontos += 3

    for termo in REFORCOS[categoria]:
        if termo in baixa:
            pontos += 1

    # Dá um peso maior para seções onde cada informação normalmente aparece.
    if categoria in {"objetivo", "problema"}:
        if candidato.secao in {"abstract", "introducao", "inicio"}:
            pontos += 3
    elif categoria == "metodo":
        if candidato.secao == "metodo":
            pontos += 4
        elif candidato.secao == "abstract":
            pontos += 2
        elif candidato.secao == "inicio":
            pontos += 1
    elif categoria == "contribuicoes":
        if candidato.secao in {"abstract", "introducao", "conclusao", "fim"}:
            pontos += 3

    # Uma frase começando com "To address..." geralmente é objetivo, não problema.
    if categoria == "problema" and re.match(
        r"\s*to\s+(address|overcome|bridge|solve|tackle|mitigate)",
        sentenca,
        re.IGNORECASE,
    ):
        pontos -= 5

    # Contribuição precisa de pistas mais explícitas, senão vira muito ruído.
    if categoria == "contribuicoes":
        expressoes_fortes = [
            "contribution",
            "contributions",
            "contributes",
            "novelty involves",
            "we propose",
            "we introduce",
            "we present",
            "outperforms",
            "the insights generated",
            "as a result, our framework",
        ]
        if any(expressao in baixa for expressao in expressoes_fortes):
            pontos += 4

    # Penaliza frases que parecem linhas de tabela.
    if sentenca.count(";") >= 4:
        pontos -= 3
    if sentenca.count(",") >= 10:
        pontos -= 2
    if re.search(r"\b(reference|sector|country|tools|studied variables)\b", baixa):
        pontos -= 4

    return pontos


def extrair_sentencas(candidatos: list[SentencaCandidata], categoria: str) -> list[str]:
    pontuadas = []
    vistas = set()

    for candidato in candidatos:
        sentenca = limpar_sentenca(candidato.texto)
        if not sentenca_valida(sentenca, categoria):
            continue
        if not any(padrao.search(sentenca) for padrao in PADROES[categoria]):
            continue

        chave = re.sub(r"[^a-z0-9]+", " ", sentenca.lower()).strip()
        if chave in vistas:
            continue
        vistas.add(chave)

        pontos = pontuar(SentencaCandidata(sentenca, candidato.secao, candidato.posicao), categoria)
        if pontos > 0:
            pontuadas.append((pontos, candidato.posicao, sentenca))

    pontuadas.sort(key=lambda item: (-item[0], item[1]))
    return [sentenca for _, _, sentenca in pontuadas[:MAX_SENTENCAS[categoria]]]


def montar_candidatos_por_categoria(texto: str) -> dict[str, list[SentencaCandidata]]:
    abstract = extrair_por_titulos(texto, "abstract")
    introducao = extrair_por_titulos(texto, "introducao")
    metodo = extrair_por_titulos(texto, "metodo")
    conclusao = extrair_por_titulos(texto, "conclusao")

    inicio = texto[:14000]
    fim = texto[-9000:]

    candidatos_intro = []
    candidatos_intro.extend(candidatos_de_texto(abstract, "abstract"))
    candidatos_intro.extend(candidatos_de_texto(introducao, "introducao"))
    candidatos_intro.extend(candidatos_de_texto(inicio, "inicio"))

    # Método costuma estar em seção própria, mas alguns artigos já explicam
    # a abordagem no resumo ou na introdução.
    candidatos_metodo = []
    candidatos_metodo.extend(candidatos_de_texto(metodo, "metodo"))
    
    # Resumo/introdução entram como apoio para não deixar o campo vazio.
    candidatos_metodo.extend(candidatos_de_texto(abstract, "abstract"))
    candidatos_metodo.extend(candidatos_de_texto(introducao, "introducao"))
    if not metodo:
        candidatos_metodo.extend(candidatos_de_texto(inicio, "inicio"))

    candidatos_contrib = []
    candidatos_contrib.extend(candidatos_de_texto(abstract, "abstract"))
    candidatos_contrib.extend(candidatos_de_texto(introducao, "introducao"))
    candidatos_contrib.extend(candidatos_de_texto(conclusao, "conclusao"))
    candidatos_contrib.extend(candidatos_de_texto(fim, "fim"))

    return {
        "objetivo": candidatos_intro,
        "problema": candidatos_intro,
        "metodo": candidatos_metodo,
        "contribuicoes": candidatos_contrib,
    }


def extrair_informacoes(nome: str, texto: str) -> dict:
    texto = limpar_texto_artigo(texto)
    candidatos = montar_candidatos_por_categoria(texto)

    return {
        "arquivo": nome,
        "objetivo": extrair_sentencas(candidatos["objetivo"], "objetivo"),
        "problema": extrair_sentencas(candidatos["problema"], "problema"),
        "metodo": extrair_sentencas(candidatos["metodo"], "metodo"),
        "contribuicoes": extrair_sentencas(candidatos["contribuicoes"], "contribuicoes"),
    }


def exibir_resultado(info: dict):
    print("\n")
    print(f"Artigo: {info['arquivo']}")

    for chave, rotulo in ROTULOS.items():
        print(f"\n{rotulo}:")
        sentencas = info[chave]
        if not sentencas:
            print("(nao encontrado)")
            continue
        for sentenca in sentencas:
            print(sentenca[:260] + ("..." if len(sentenca) > 260 else ""))


def main():
    caminho_json = os.path.join(DIRETORIO_SAIDA, "etapa1_resultados.json")
    with open(caminho_json, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    resultados = []
    for nome, info in dados["artigos"].items():
        print(f"\nProcessando: {nome}")
        resultado = extrair_informacoes(nome, info["corpo"])
        exibir_resultado(resultado)
        resultados.append(resultado)
        print("\n-------------------------------------------------\n")

    os.makedirs(DIRETORIO_SAIDA, exist_ok=True)
    caminho = os.path.join(DIRETORIO_SAIDA, "etapa2_resultados.json")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(resultados, arquivo, ensure_ascii=False, indent=2)

    print(f"\nResultados salvos em: {caminho}")


if __name__ == "__main__":
    main()
