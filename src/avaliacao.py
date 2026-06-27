"""
Etapa 4 - Avaliação automática da extração de informações.

O gabarito é preenchido manualmente com as sentenças corretas.
O programa compara esse gabarito com a saída da Etapa 2 e calcula:

- TP: sentença relevante encontrada
- FP: sentença extraída, mas não relevante
- FN: sentença relevante não encontrada
- precisão
- cobertura
- taxa de falsos positivos = 1 - precisão
- taxa de falsos negativos = 1 - cobertura
"""

import csv
import json
import re
import matplotlib.pyplot as plt
from pathlib import Path
from difflib import SequenceMatcher


RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"

CAMINHO_PREDICOES = RESULTADOS / "etapa2_resultados.json"
CAMINHO_GABARITO = "src/gabarito_manual.json"
CAMINHO_METRICAS = RESULTADOS / "etapa4_metricas.json"
CAMINHO_DETALHES = RESULTADOS / "etapa4_detalhes.csv"
CAMINHO_GRAFICO = RESULTADOS / "etapa4_metricas.png"

CATEGORIAS = ["objetivo", "problema", "metodo", "contribuicoes"]

ROTULOS = {
    "objetivo": "Objetivo",
    "problema": "Problema",
    "metodo": "Método",
    "contribuicoes": "Contribuições",
}


def carregar_json(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(dados, caminho):
    RESULTADOS.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def normalizar(texto):
    """
    Normaliza diferenças de formatação causadas pela extração do PDF.
    """
    texto = texto.lower()
    # Junta palavras quebradas por hífen entre letras.
    texto = re.sub(r"(?<=\w)-\s*(?=\w)", "", texto)
    # Remove pontuação e padroniza os espaços.
    texto = re.sub(r"[^a-z0-9]+", " ", texto)

    return " ".join(texto.split())

def sentencas_correspondem(texto_a, texto_b):
    normal_a = normalizar(texto_a)
    normal_b = normalizar(texto_b)
    # Primeiro tenta a igualdade normal.
    if normal_a == normal_b:
        return True
    # Ignora também diferenças de espaços e hífens.
    compacto_a = normal_a.replace(" ", "")
    compacto_b = normal_b.replace(" ", "")
    if compacto_a == compacto_b:
        return True
    # Aceita diferenças muito pequenas causadas pelo PDF.
    semelhanca = SequenceMatcher(
        None,
        compacto_a,
        compacto_b,
    ).ratio()

    return semelhanca >= 0.95

def comparar_sentencas(preditas, esperadas):
    """
    Compara as sentenças da Etapa 2 com as sentenças do gabarito.

    Cada sentença esperada só pode ser associada uma vez.
    """
    esperadas_usadas = set()
    tp = 0

    for predita in preditas:
        melhor_indice = None
        melhor_similaridade = 0.0
        for indice, esperada in enumerate(esperadas):
            if indice in esperadas_usadas:
                continue
            normal_predita = normalizar(predita).replace(" ", "")
            normal_esperada = normalizar(esperada).replace(" ", "")
            similaridade = SequenceMatcher(
                None,
                normal_predita,
                normal_esperada,
            ).ratio()
            if sentencas_correspondem(predita, esperada):
                if similaridade > melhor_similaridade:
                    melhor_similaridade = similaridade
                    melhor_indice = indice
        if melhor_indice is not None:
            tp += 1
            esperadas_usadas.add(melhor_indice)
    fp = len(preditas) - tp
    fn = len(esperadas) - tp

    return tp, fp, fn


def calcular_metricas(tp, fp, fn):
    precisao = tp / (tp + fp) if tp + fp > 0 else 0.0
    cobertura = tp / (tp + fn) if tp + fn > 0 else 0.0
    taxa_fp = 1 - precisao if tp + fp > 0 else 0.0
    taxa_fn = 1 - cobertura if tp + fn > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precisao": round(precisao, 4),
        "cobertura": round(cobertura, 4),
        "taxa_falsos_positivos": round(taxa_fp, 4),
        "taxa_falsos_negativos": round(taxa_fn, 4),
    }

def salvar_csv(detalhes):
    campos = [
        "arquivo",
        "categoria",
        "quantidade_esperada",
        "quantidade_extraida",
        "tp",
        "fp",
        "fn",
        "precisao",
        "cobertura",
        "taxa_falsos_positivos",
        "taxa_falsos_negativos",
    ]
    with open(CAMINHO_DETALHES, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(detalhes)


def gerar_grafico(metricas):
    nomes = [ROTULOS[categoria] for categoria in CATEGORIAS]
    precisoes = [metricas[categoria]["precisao"] for categoria in CATEGORIAS]
    coberturas = [metricas[categoria]["cobertura"] for categoria in CATEGORIAS]
    posicoes = list(range(len(CATEGORIAS)))
    largura = 0.35

    plt.figure(figsize=(9, 5))
    plt.bar(
        [x - largura / 2 for x in posicoes],
        precisoes,
        largura,
        label="Precisão",
    )
    plt.bar(
        [x + largura / 2 for x in posicoes],
        coberturas,
        largura,
        label="Cobertura",
    )

    plt.xticks(posicoes, nomes)
    plt.ylim(0, 1)
    plt.ylabel("Valor")
    plt.title("Desempenho da extração por categoria")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CAMINHO_GRAFICO, dpi=200)
    plt.close()


def exibir_resultados(metricas, global_):
    print("\nDesempenho por categoria")
    print("-" * 99)
    print(
        f"{'Categoria':<16} {'TP':>4} {'FP':>4} {'FN':>4} "
        f"{'Precisão':>10} {'Cobertura':>10} "
        f"{'Taxa FP':>10} {'Taxa FN':>10}"
    )
    print("-" * 99)

    for categoria in CATEGORIAS:
        m = metricas[categoria]

        print(
            f"{ROTULOS[categoria]:<16} "
            f"{m['tp']:>4} {m['fp']:>4} {m['fn']:>4} "
            f"{m['precisao']:>10.4f} "
            f"{m['cobertura']:>10.4f} "
            f"{m['taxa_falsos_positivos']:>10.4f} "
            f"{m['taxa_falsos_negativos']:>10.4f}"
        )

    print("-" * 99)

    print(
        f"{'Global':<16} "
        f"{global_['tp']:>4} {global_['fp']:>4} {global_['fn']:>4} "
        f"{global_['precisao']:>10.4f} "
        f"{global_['cobertura']:>10.4f} "
        f"{global_['taxa_falsos_positivos']:>10.4f} "
        f"{global_['taxa_falsos_negativos']:>10.4f}"
    )


def main():
    if not CAMINHO_PREDICOES.exists():
        raise FileNotFoundError(
            f"Execute a Etapa 2 antes. Arquivo não encontrado: "
            f"{CAMINHO_PREDICOES}"
        )

    predicoes_lista = carregar_json(CAMINHO_PREDICOES)
    gabarito_lista = carregar_json(CAMINHO_GABARITO)
    predicoes = {
        artigo["arquivo"]: artigo
        for artigo in predicoes_lista
    }
    totais = {
        categoria: {"tp": 0, "fp": 0, "fn": 0}
        for categoria in CATEGORIAS
    }

    detalhes = []

    for esperado in gabarito_lista:
        nome_arquivo = esperado["arquivo"]
        predito = predicoes.get(nome_arquivo, {})
        for categoria in CATEGORIAS:
            sentencas_preditas = predito.get(categoria, [])
            sentencas_esperadas = esperado.get(categoria, [])
            tp, fp, fn = comparar_sentencas(
                sentencas_preditas,
                sentencas_esperadas,
            )
            metricas_artigo = calcular_metricas(tp, fp, fn)
            totais[categoria]["tp"] += tp
            totais[categoria]["fp"] += fp
            totais[categoria]["fn"] += fn
            detalhes.append({
                "arquivo": nome_arquivo,
                "categoria": categoria,
                "quantidade_esperada": len(sentencas_esperadas),
                "quantidade_extraida": len(sentencas_preditas),
                **metricas_artigo,
            })

    metricas_categoria = {}

    for categoria in CATEGORIAS:
        total = totais[categoria]
        metricas_categoria[categoria] = calcular_metricas(
            total["tp"],
            total["fp"],
            total["fn"],
        )

    tp_global = sum(total["tp"] for total in totais.values())
    fp_global = sum(total["fp"] for total in totais.values())
    fn_global = sum(total["fn"] for total in totais.values())

    metricas_globais = calcular_metricas(
        tp_global,
        fp_global,
        fn_global,
    )

    resultado = {
        "quantidade_artigos_avaliados": len(gabarito_lista),
        "por_categoria": metricas_categoria,
        "global": metricas_globais,
    }

    salvar_json(resultado, CAMINHO_METRICAS)
    salvar_csv(detalhes)
    gerar_grafico(metricas_categoria)
    exibir_resultados(metricas_categoria, metricas_globais)

    print(f"\nMétricas salvas em: {CAMINHO_METRICAS}")
    print(f"Detalhes salvos em: {CAMINHO_DETALHES}")
    print(f"Gráfico salvo em: {CAMINHO_GRAFICO}")


if __name__ == "__main__":
    main()
