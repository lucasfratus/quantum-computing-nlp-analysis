"""
Serializacao dos dados extraidos em formato de ontologia (JSON-LD).

Modelagem da ontologia de artigo cientifico:

Classe ArtigoCientifico
    - identificador      -> nome do arquivo PDF do artigo
    - temObjetivo         -> trechos que descrevem o objetivo do artigo
    - temProblema         -> trechos que descrevem o problema abordado
    - temMetodologia      -> trechos que descrevem o metodo utilizado
    - temContribuicao     -> trechos que descrevem as contribuicoes do artigo
    - temReferencia       -> lista de referencias bibliograficas extraidas

Classe Corpus
    - temArtigo            -> lista de ArtigoCientifico que compoem o corpus
    - termoMaisFrequente   -> termos mais citados em todo o corpus
"""

import os
import json

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTADOS_DIR = os.path.join(BASE_DIR, "resultados")
ONTOLOGIA_DIR  = os.path.join(BASE_DIR, "ontologia")

CAMINHO_ETAPA1 = os.path.join(RESULTADOS_DIR, "etapa1_resultados.json")
CAMINHO_ETAPA2 = os.path.join(RESULTADOS_DIR, "etapa2_resultados.json")
CAMINHO_SAIDA  = os.path.join(ONTOLOGIA_DIR, "ontologia_corpus.jsonld")



def carregar_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    return dados



def montar_contexto():
    """
    Define o vocabulario proprio da ontologia de artigo cientifico,
    usado pelo JSON-LD para dar significado as chaves do documento.
    """
    contexto = {
        "ont": "http://uem-iia-pln.org/ontologia-artigo-cientifico#",
        "ArtigoCientifico":  "ont:ArtigoCientifico",
        "Corpus":            "ont:Corpus",
        "identificador":     "ont:identificador",
        "temObjetivo":       "ont:temObjetivo",
        "temProblema":       "ont:temProblema",
        "temMetodologia":    "ont:temMetodologia",
        "temContribuicao":   "ont:temContribuicao",
        "temReferencia":     "ont:temReferencia",
        "temArtigo":         "ont:temArtigo",
        "termoMaisFrequente": "ont:termoMaisFrequente",
        "termo":             "ont:termo",
        "frequencia":        "ont:frequencia",
    }
    return contexto


def montar_artigo(nome, info_etapa1, info_etapa2):
    artigo = {
        "@type": "ArtigoCientifico",
        "identificador": nome,
        "temObjetivo": info_etapa2.get("objetivo", []),
        "temProblema": info_etapa2.get("problema", []),
        "temMetodologia": info_etapa2.get("metodo", []),
        "temContribuicao": info_etapa2.get("contribuicoes", []),
        "temReferencia": info_etapa1.get("lista_referencias", []),
    }
    return artigo


def montar_termos_frequentes(top_termos):
    lista = []
    for termo, freq in top_termos.items():
        item = {"termo": termo, "frequencia": freq}
        lista.append(item)
    return lista


def main():
    print("\nETAPA 3 — Serializacao em Ontologia (JSON-LD)")
    print("Tema: Quantum Computing | Base: Scopus\n")

    dados_etapa1 = carregar_json(CAMINHO_ETAPA1)
    dados_etapa2 = carregar_json(CAMINHO_ETAPA2)

    # indexa os resultados da etapa 2 pelo nome do arquivo,
    # para facilitar o cruzamento com os dados da etapa 1
    info_etapa2_por_artigo = {}
    for item in dados_etapa2:
        nome = item["arquivo"]
        info_etapa2_por_artigo[nome] = item

    lista_artigos = []

    for nome, info1 in dados_etapa1["artigos"].items():
        info2 = info_etapa2_por_artigo.get(nome, {})
        artigo = montar_artigo(nome, info1, info2)
        lista_artigos.append(artigo)
        print(f"Artigo adicionado a ontologia: {nome}")

    termos_frequentes = montar_termos_frequentes(dados_etapa1["top_termos"])

    ontologia = {
        "@context": montar_contexto(),
        "@type": "Corpus",
        "temArtigo": lista_artigos,
        "termoMaisFrequente": termos_frequentes,
    }

    os.makedirs(ONTOLOGIA_DIR, exist_ok=True)
    with open(CAMINHO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(ontologia, f, ensure_ascii=False, indent=2)

    print(f"\nOntologia salva em: {CAMINHO_SAIDA}")


if __name__ == "__main__":
    main()