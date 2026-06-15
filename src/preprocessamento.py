import pypdf
from pathlib import Path
import re

DIRETORIO_PDFS = "artigos"
DIRETORIO_SAIDA = "resultados"
TOP_N = 10


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