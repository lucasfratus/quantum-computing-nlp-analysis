"""
Etapa 3 - Geração da ontologia em JSON-LD.

Este arquivo pega os resultados das etapas anteriores e organiza tudo em
um formato JSON-LD. Representa o corpus como um conjunto de
artigos científicos, cada um com seus trechos extraídos, referências e
estatísticas.
"""

import json
import re
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTADOS_DIR = BASE_DIR / "resultados"
ONTOLOGIA_DIR = BASE_DIR / "ontologia"

CAMINHO_ETAPA1 = RESULTADOS_DIR / "etapa1_resultados.json"
CAMINHO_ETAPA2 = RESULTADOS_DIR / "etapa2_resultados.json"
CAMINHO_OBSERVACOES = RESULTADOS_DIR / "observacoes" / "observacoes_resumo.json"
CAMINHO_SAIDA = ONTOLOGIA_DIR / "ontologia_corpus.jsonld"

# IRI base criada só para este trabalho. Ajuda a dar identificadores aos recursos.
BASE_IRI = "http://example.org/trab2-ia/lucas-matheus/quantum-computing-nlp-analysis/"
ONT_IRI = BASE_IRI + "ontologia#"


def carregar_json(caminho: Path) -> Any:
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(dados: Any, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def texto_para_id(texto: str) -> str:
    """Transforma um texto em uma identificação simples para usar no @id."""
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    texto = texto.strip("-")
    return texto or "item"


def montar_contexto() -> dict:
    """Monta o @context do JSON-LD."""
    return {
        "@vocab": ONT_IRI,
        "schema": "https://schema.org/",
        "dcterms": "http://purl.org/dc/terms/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "Corpus": "Corpus",
        "ArtigoCientifico": "ArtigoCientifico",
        "TrechoExtraido": "TrechoExtraido",
        "ReferenciaBibliografica": "ReferenciaBibliografica",
        "FrequenciaTermo": "FrequenciaTermo",
        "EstatisticasArtigo": "EstatisticasArtigo",
        "Visualizacao": "Visualizacao",
        "TecnicaMencionada": "TecnicaMencionada",
        "EvolucaoTemporalTermo": "EvolucaoTemporalTermo",
        "TrechoTrabalhoFuturo": "TrechoTrabalhoFuturo",
        "arquivo": "arquivo",
        "categoria": "categoria",
        "ordem": "ordem",
        "frequencia": "frequencia",
        "ano": "ano",
        "caminhoArquivo": "caminhoArquivo",
        "quantidadeTokens": "quantidadeTokens",
        "quantidadeReferencias": "quantidadeReferencias",
        "quantidadeObjetivos": "quantidadeObjetivos",
        "quantidadeProblemas": "quantidadeProblemas",
        "quantidadeMetodos": "quantidadeMetodos",
        "quantidadeContribuicoes": "quantidadeContribuicoes",
        "temArtigo": {
            "@id": "temArtigo",
            "@type": "@id",
            "@container": "@list",
        },
        "temObjetivo": {
            "@id": "temObjetivo",
            "@container": "@list",
        },
        "temProblema": {
            "@id": "temProblema",
            "@container": "@list",
        },
        "temMetodologia": {
            "@id": "temMetodologia",
            "@container": "@list",
        },
        "temContribuicao": {
            "@id": "temContribuicao",
            "@container": "@list",
        },
        "temReferencia": {
            "@id": "temReferencia",
            "@container": "@list",
        },
        "temTermoFrequente": {
            "@id": "temTermoFrequente",
            "@container": "@list",
        },
        "temBigramasFrequentes": {
            "@id": "temBigramasFrequentes",
            "@container": "@list",
        },
        "temTrigramasFrequentes": {
            "@id": "temTrigramasFrequentes",
            "@container": "@list",
        },
        "temTecnicaMencionada": {
            "@id": "temTecnicaMencionada",
            "@container": "@list",
        },
        "temEvolucaoTemporal": {
            "@id": "temEvolucaoTemporal",
            "@container": "@list",
        },
        "temTrabalhoFuturo": {
            "@id": "temTrabalhoFuturo",
            "@container": "@list",
        },
        "temVisualizacao": {
            "@id": "temVisualizacao",
            "@container": "@list",
        },
        "temEstatisticas": "temEstatisticas",
        "texto": "schema:text",
        "titulo": "schema:name",
        "cita": "schema:citation",
        "termo": "schema:name",
        "dataCriacao": {
            "@id": "dcterms:created",
            "@type": "xsd:string",
        },
        "descricao": "dcterms:description",
    }


def extrair_titulo(info_etapa1: dict, nome_arquivo: str) -> str:
    """Pega uma linha inicial do corpo do artigo para usar como título."""
    corpo = info_etapa1.get("corpo", "")
    linhas = [linha.strip() for linha in corpo.splitlines() if linha.strip()]

    for linha in linhas[:8]:
        linha_minuscula = linha.lower()
        if linha_minuscula in {"abstract", "article info", "keywords"}:
            continue
        if "journal" in linha_minuscula or "doi" in linha_minuscula or "contents lists" in linha_minuscula:
            continue
        if 15 <= len(linha) <= 220:
            return re.sub(r"\s+", " ", linha)

    return nome_arquivo


def montar_trechos(sentencas: list[str], categoria: str, artigo_id: str) -> list[dict]:
    """Cria os objetos JSON-LD para uma lista de frases extraídas."""
    trechos = []

    for indice, sentenca in enumerate(sentencas, start=1):
        trecho = {
            "@id": f"{artigo_id}/{categoria}/{indice}",
            "@type": "TrechoExtraido",
            "categoria": categoria,
            "ordem": indice,
            "texto": sentenca,
        }
        trechos.append(trecho)

    return trechos


def montar_referencias(referencias: list[str], artigo_id: str) -> list[dict]:
    itens = []

    for indice, referencia in enumerate(referencias, start=1):
        item = {
            "@id": f"{artigo_id}/referencia/{indice}",
            "@type": "ReferenciaBibliografica",
            "ordem": indice,
            "texto": referencia,
        }
        itens.append(item)

    return itens


def montar_frequencias(contagens: dict[str, int], tipo: str) -> list[dict]:
    """Converte as contagens de termos, bigramas ou trigramas em JSON-LD."""
    itens = []

    for indice, (termo, frequencia) in enumerate(contagens.items(), start=1):
        item = {
            "@id": f"{BASE_IRI}{tipo}/{texto_para_id(termo)}",
            "@type": "FrequenciaTermo",
            "ordem": indice,
            "termo": termo,
            "frequencia": int(frequencia),
        }
        itens.append(item)

    return itens


def montar_artigo(nome: str, info_etapa1: dict, info_etapa2: dict) -> dict:
    artigo_id = f"{BASE_IRI}artigo/{texto_para_id(nome)}"

    objetivos = info_etapa2.get("objetivo", [])
    problemas = info_etapa2.get("problema", [])
    metodos = info_etapa2.get("metodo", [])
    contribuicoes = info_etapa2.get("contribuicoes", [])
    referencias = info_etapa1.get("lista_referencias", [])

    artigo = {
        "@id": artigo_id,
        "@type": ["ArtigoCientifico", "schema:ScholarlyArticle"],
        "arquivo": nome,
        "titulo": extrair_titulo(info_etapa1, nome),
        "temObjetivo": montar_trechos(objetivos, "objetivo", artigo_id),
        "temProblema": montar_trechos(problemas, "problema", artigo_id),
        "temMetodologia": montar_trechos(metodos, "metodo", artigo_id),
        "temContribuicao": montar_trechos(contribuicoes, "contribuicao", artigo_id),
        "temReferencia": montar_referencias(referencias, artigo_id),
        "temEstatisticas": {
            "@type": "EstatisticasArtigo",
            "quantidadeTokens": int(info_etapa1.get("tokens", 0)),
            "quantidadeReferencias": int(info_etapa1.get("referencias", len(referencias))),
            "quantidadeObjetivos": len(objetivos),
            "quantidadeProblemas": len(problemas),
            "quantidadeMetodos": len(metodos),
            "quantidadeContribuicoes": len(contribuicoes),
        },
    }

    if referencias:
        artigo["cita"] = referencias

    return artigo



def montar_visualizacoes(caminhos: list[str]) -> list[dict]:
    """Coloca no JSON-LD os arquivos de imagem gerados para a apresentação."""
    itens = []

    for indice, caminho in enumerate(caminhos, start=1):
        itens.append({
            "@id": f"{BASE_IRI}visualizacao/{indice}",
            "@type": "Visualizacao",
            "ordem": indice,
            "caminhoArquivo": caminho,
        })

    return itens


def montar_tecnicas(contagens: dict[str, int]) -> list[dict]:
    """Registra as técnicas mais citadas no corpus."""
    itens = []

    for indice, (tecnica, frequencia) in enumerate(contagens.items(), start=1):
        itens.append({
            "@id": f"{BASE_IRI}tecnica/{texto_para_id(tecnica)}",
            "@type": "TecnicaMencionada",
            "ordem": indice,
            "termo": tecnica,
            "frequencia": int(frequencia),
        })

    return itens


def montar_evolucao_temporal(evolucao: dict) -> list[dict]:
    """Transforma a tabela ano x termo em recursos JSON-LD."""
    itens = []
    frequencias = evolucao.get("frequencias_por_ano", {})

    for ano, termos in frequencias.items():
        for termo, frequencia in termos.items():
            itens.append({
                "@id": f"{BASE_IRI}evolucao/{ano}/{texto_para_id(termo)}",
                "@type": "EvolucaoTemporalTermo",
                "ano": ano,
                "termo": termo,
                "frequencia": int(frequencia),
            })

    return itens


def montar_trabalhos_futuros(dados: dict) -> list[dict]:
    """Adiciona os trechos em que os artigos falam de trabalhos futuros."""
    itens = []
    trechos = dados.get("trabalhos_futuros", {}).get("trechos", [])

    for indice, item in enumerate(trechos, start=1):
        itens.append({
            "@id": f"{BASE_IRI}trabalho-futuro/{indice}",
            "@type": "TrechoTrabalhoFuturo",
            "ordem": indice,
            "arquivo": item.get("arquivo", ""),
            "texto": item.get("trecho", ""),
        })

    return itens


def adicionar_observacoes(ontologia: dict) -> None:
    """
    Inclui no JSON-LD as análises extras do enunciado, caso elas já tenham
    sido geradas pelo script observacoes.py.
    """
    if not CAMINHO_OBSERVACOES.exists():
        return

    dados = carregar_json(CAMINHO_OBSERVACOES)
    ontologia["temVisualizacao"] = montar_visualizacoes(dados.get("visualizacoes_geradas", []))
    ontologia["temTecnicaMencionada"] = montar_tecnicas(dados.get("tecnicas_mais_mencionadas", {}))
    ontologia["temEvolucaoTemporal"] = montar_evolucao_temporal(dados.get("evolucao_temporal", {}))
    ontologia["temTrabalhoFuturo"] = montar_trabalhos_futuros(dados)


def main() -> None:
    print("\nSerialização em Ontologia JSON-LD\n")

    if not CAMINHO_ETAPA1.exists():
        raise FileNotFoundError(f"Execute a Etapa 1 antes. Arquivo não encontrado: {CAMINHO_ETAPA1}")
    if not CAMINHO_ETAPA2.exists():
        raise FileNotFoundError(f"Execute a Etapa 2 antes. Arquivo não encontrado: {CAMINHO_ETAPA2}")

    dados_etapa1 = carregar_json(CAMINHO_ETAPA1)
    dados_etapa2 = carregar_json(CAMINHO_ETAPA2)

    # Facilita buscar o resultado da etapa 2 pelo nome do arquivo PDF.
    info_etapa2_por_artigo = {item["arquivo"]: item for item in dados_etapa2}

    artigos = []
    for nome, info1 in dados_etapa1.get("artigos", {}).items():
        info2 = info_etapa2_por_artigo.get(nome, {})
        artigo = montar_artigo(nome, info1, info2)
        artigos.append(artigo)
        print(f"Artigo adicionado à ontologia: {nome}")

    ontologia = {
        "@context": montar_contexto(),
        "@id": f"{BASE_IRI}corpus/quantum-computing",
        "@type": "Corpus",
        "titulo": "Corpus de artigos científicos sobre Computação Quântica",
        "descricao": (
            "Ontologia JSON-LD gerada a partir das etapas de pré-processamento, "
            "extração de informações e análise de frequência de termos."
        ),
        "temArtigo": artigos,
        "temTermoFrequente": montar_frequencias(dados_etapa1.get("top_termos", {}), "termo"),
        "temBigramasFrequentes": montar_frequencias(dados_etapa1.get("top_bigramas", {}), "bigrama"),
        "temTrigramasFrequentes": montar_frequencias(dados_etapa1.get("top_trigramas", {}), "trigrama"),
    }

    adicionar_observacoes(ontologia)

    salvar_json(ontologia, CAMINHO_SAIDA)
    print(f"\nOntologia salva em: {CAMINHO_SAIDA}")


if __name__ == "__main__":
    main()
