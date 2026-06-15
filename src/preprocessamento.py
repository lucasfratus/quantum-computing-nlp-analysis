import pypdf
import re
import nltk
import os
import json

from collections import Counter
from pathlib import Path
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.util import ngrams


DIRETORIO_PDFS = "artigos"
DIRETORIO_SAIDA = "resultados"
TOP_N = 10

# parâmetros
lematizacao = True
stemming = False


def setup_nltk():    
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
    nltk.download("stopwords", quiet=True)
    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)


def construir_stopwords():
    return set(stopwords.words("english"))


def ler_pdf(caminho: str) -> str:
    """Extrai o texto de um arquivo PDF usando a biblioteca pypdf."""
    try:
        texto_extraido = ""
        with open(caminho, "rb") as f:
            leitor = pypdf.PdfReader(f);
            for pagina in leitor.pages:
                try:
                    conteudo = pagina.extract_text()
                    if conteudo:
                        texto_extraido += conteudo + "\n"
                except Exception:
                    continue
        if texto_extraido.strip():
            return texto_extraido
        raise ValueError
    
    except Exception as e:
        from pdfminer.high_level import extract_text as pdfminer_extract
        return pdfminer_extract(caminho)


def carregar_artigos(diretorio: str) -> dict[str, str]:
    """
    Lê todos os arquivos '.pdf' de um diretório informado.
    Retorna um dicionário {nome_arquivo : texto_extraido}.
    """
    artigos = {}
    pdfs = sorted(Path(diretorio).glob("*.pdf"))

    if not pdfs:
        raise FileNotFoundError(f"Nenhum arquivo '.pdf' encontrado no diretório '{diretorio}'.")
    
    for caminho in pdfs:
        print(f"{caminho.name}")
        artigos[caminho.name] = ler_pdf(str(caminho))

    return artigos



INDICADORES_REFERENCIAS = ["References", "REFERENCES", "Bibliography", "BIBLIOGRAPHY", "Referências", "REFERÊNCIAS"]

def separar_corpo_referencia(texto: str) -> tuple[str, str]:
    """
    Divide o texto do artigo em corpo e seção de referências.
    Retorna (corpo, secao_de_referencias).
    """

    for indicador in INDICADORES_REFERENCIAS:
        if indicador in texto:
            posicao = texto.rfind(indicador)
            return texto[:posicao], texto[posicao:]
    return texto, ""


def extrair_referencias(secao: str) -> list[str]:
    """
    Extrai referências individuais da seção de referências.
    Suporta os formatos:
    - [1] Autor, Título, etc.
    - 1. Autor, Título, etc.
    """

    referencias = []
    ref_atual = ""

    for linha in secao.splitlines():
        linha = linha.strip()
        if not linha:
            continue

        # Nova referência começa com [1] ou 1.
        eh_nova_ref = (
            re.match(r'^\[\d+\]', linha) or
            re.match(r'^\d{1,3}\.', linha)
        )

        if eh_nova_ref:
            if ref_atual:
                referencias.append(ref_atual.strip())
            ref_atual = linha
        else:
            ref_atual += " " + linha  # continua a referência anterior

    if ref_atual:
        referencias.append(ref_atual.strip())

    return referencias


def preprocessar(texto: str, stop_words: set, lematizar: bool, stemming: bool) -> list[str]:
    """
    Realiza o pré-processamento:
    - deixa todas as letras minúsculas;
    - remove caracteres que não fazem parte do alfabeto
    - tokenização
    - remove stop-words e tokens menores de 3 caracteres
    - pode realizar a lematização ou stemming
    """

    texto = texto.lower()

    # mantém apenas letras e espaços
    texto = re.sub(r'[^a-z\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()

    # tokenização
    tokens = nltk.word_tokenize(texto)

    # stop-words e tokens curtos
    tokens_filtrados = []
    for t in tokens:
        if t not in stop_words and len(t) > 2:
            tokens_filtrados.append(t)
    tokens = tokens_filtrados

    # lematização ou stemming
    wn_lemmatizer = WordNetLemmatizer()
    porter_stemmer = PorterStemmer()
    if lematizar:
        tokens_normalizados = []
        for t in tokens:
            tokens_normalizados.append(wn_lemmatizer.lemmatize(t))
        tokens = tokens_normalizados

    elif stemming:
        tokens_normalizados = []
        for t in tokens:
            tokens_normalizados.append(porter_stemmer.stem(t))
        tokens = tokens_normalizados

    return tokens


def construir_bow(lista_tokens: list[list[str]]) -> Counter:
    """Constrói um Bag of Words a partir de uma lista de listas de tokens."""

    todos = []

    for tokens in lista_tokens:
        for token in tokens:
            todos.append(token)

    return Counter(todos)



def contar_ngramas(lista_tokens: list[list[str]], n: int = 2) -> Counter:
    """Conta n-gramas no corpus completo."""

    todos_ngramas = []

    for tokens in lista_tokens:
        for ng in ngrams(tokens, n):
            todos_ngramas.append(ng)

    return Counter(todos_ngramas)


def exibir_top(titulo: str, contagem: Counter, n: int = 10, unir_tokens: bool = False):
    """Imprime os N itens mais frequentes de um Counter."""
    print(f"\n{titulo}")
    print("-" * len(titulo))

    for item, freq in contagem.most_common(n):
        if unir_tokens:
            item = " ".join(item)
        print(f"{item}: {freq}")


def exibir_referencias(nome_arquivo: str, refs: list[str], max_exibir: int = 5):
    """Exibe as primeiras N referências de um artigo."""
    print(f"\nArquivo: {nome_arquivo}")

    for ref in refs[:max_exibir]:
        print(f"- {ref}")

    if len(refs) > max_exibir:
        print(f"... e mais {len(refs) - max_exibir} referências.")


def salvar_resultados(dados: dict, caminho: str):
    """Salva os resultados da etapa 1 em JSON para uso nas etapas seguintes."""
    pasta = os.path.dirname(caminho)

    if pasta:
        os.makedirs(pasta, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)

    print(f"Resultados salvos em {caminho}")

def main():
    setup_nltk()
    stop_words = construir_stopwords()

    print("Carregando artigos...")

    corpus = carregar_artigos(DIRETORIO_PDFS)

    lista_tokens = []
    todas_refs = {}
    stats_artigos = {}

    for nome, texto in corpus.items():
        corpo, secao_refs = separar_corpo_referencia(texto)

        referencias = extrair_referencias(secao_refs)
        tokens = preprocessar(corpo, stop_words, lematizacao, stemming)

        lista_tokens.append(tokens)
        todas_refs[nome] = referencias

        stats_artigos[nome] = {
            "tokens": len(tokens),
            "referencias": len(referencias),
            "lista_referencias": referencias,
        }

        print(f"{nome}: {len(tokens)} tokens")

    bow = construir_bow(lista_tokens)
    bigramas = contar_ngramas(lista_tokens, 2)
    trigramas = contar_ngramas(lista_tokens, 3)

    exibir_top("Palavras mais frequentes", bow, TOP_N)
    exibir_top("Bigramas mais frequentes", bigramas, TOP_N, True)
    exibir_top("Trigramas mais frequentes", trigramas, TOP_N, True)

    resultado = {
        "top_termos": dict(bow.most_common(TOP_N)),
        "top_bigramas": {" ".join(k): v for k, v in bigramas.most_common(TOP_N)},
        "top_trigramas": {" ".join(k): v for k, v in trigramas.most_common(TOP_N)},
        "artigos": stats_artigos,
    }

    salvar_resultados(
        resultado,
        os.path.join(DIRETORIO_SAIDA, "etapa1_resultados.json"),
    )

    return bow, bigramas, trigramas, todas_refs


if __name__ == "__main__":
    main()
