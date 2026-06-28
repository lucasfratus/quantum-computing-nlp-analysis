# Trabalho de PLN - Análise de Artigos sobre Computação Quântica

Trabalho desenvolvido para a disciplina de **Introdução à Inteligência Artificial**, ministrada pelo professor Wagner Igarasi.

O projeto aplica técnicas de Processamento de Linguagem Natural (PLN) em um conjunto de artigos científicos em PDF sobre computação quântica. A partir dos textos extraídos, o sistema realiza pré-processamento, extração de informações, geração de uma ontologia, avaliação dos resultados e visualizações.

## Tema

O tema escolhido foi:

**Quantum Computing**

Os artigos utilizados no corpus principal ficam na pasta:

```text
artigos/
```

## Estrutura do projeto

```text
.
├── artigos/                  # artigos em PDF usados no corpus principal
├── ontologia/                # ontologia gerada em JSON-LD
├── resultados/               # saídas das etapas do trabalho
│   └── observacoes/          # gráficos e análises adicionais
├── src/                      # código-fonte
│   ├── preprocessamento.py
│   ├── extracao_informacoes.py
│   ├── ontologia.py
│   ├── avaliacao.py
│   └── visualizacao.py
├── README.md
└── requirements.txt
```

## Instalação

Recomenda-se usar um ambiente virtual.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Depois, instale as dependências:

```bash
pip install -r requirements.txt
```

Caso seja necessário baixar os recursos do NLTK manualmente, execute:

```bash
python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"
```

## Ordem de execução

A ordem recomendada segue a ordem das etapas do trabalho:

```bash
python3 src/preprocessamento.py
python3 src/extracao_informacoes.py
python3 src/ontologia.py
python3 src/avaliacao.py
python3 src/visualizacao.py
```

## 1. Pré-processamento

Arquivo:

```text
src/preprocessamento.py
```

Essa etapa lê os PDFs da pasta `artigos/` e extrai o texto dos documentos. Depois disso, o texto passa por uma limpeza inicial e por etapas simples de PLN, como remoção de stopwords, lematização e contagem de palavras.

Também são gerados os termos mais frequentes, bigramas e trigramas do corpus.

Saída principal:

```text
resultados/etapa1_resultados.json
```

Essa saída contém informações como:

- corpo textual dos artigos;
- referências extraídas;
- quantidade de tokens por artigo;
- termos mais frequentes;
- bigramas mais frequentes;
- trigramas mais frequentes.

## 2. Extração de informações

Arquivo:

```text
src/extracao_informacoes.py
```

Essa etapa tenta identificar, em cada artigo, trechos relacionados a:

- objetivo;
- problema;
- método ou metodologia;
- contribuições.

A extração foi feita com regras heurísticas, usando padrões textuais e palavras-chave. Como os artigos possuem formatos diferentes, algumas informações são mais fáceis de encontrar do que outras.

Saída principal:

```text
resultados/etapa2_resultados.json
```

## 3. Ontologia

Arquivo:

```text
src/ontologia.py
```

Essa etapa organiza os dados extraídos em uma ontologia simples no formato **JSON-LD**.

A ontologia representa informações como:

- artigos analisados;
- trechos extraídos;
- referências bibliográficas;
- termos frequentes;
- estatísticas dos artigos;
- visualizações geradas;
- trechos relacionados a trabalhos futuros.

Saída principal:

```text
ontologia/ontologia_corpus.jsonld
```

## 4. Avaliação

Arquivo:

```text
src/avaliacao.py
```

Essa etapa compara os trechos extraídos automaticamente com um gabarito manual. A ideia é medir o desempenho da extração de informações.

As métricas usadas foram:

- **TP**: verdadeiro positivo;
- **FP**: falso positivo;
- **FN**: falso negativo;
- **precisão**;
- **cobertura**;
- **taxa de falsos positivos**;
- **taxa de falsos negativos**.

Saídas principais:

```text
resultados/etapa4_metricas.json
resultados/etapa4_detalhes.csv
resultados/etapa4_metricas.png
```

Na versão final, os resultados globais foram:

```text
Precisão global: 0.4029
Cobertura/recall global: 0.1633
```

O desempenho foi melhor nas categorias de objetivo e contribuições. A categoria método foi a mais difícil, pois a metodologia aparece de formas diferentes dependendo do artigo.

## 5. Visualização e observações

Arquivo:

```text
src/visualizacao.py
```

Essa etapa gera as visualizações pedidas no enunciado do trabalho.

Foram geradas visualizações para:

- palavras mais citadas nos artigos;
- nuvem de palavras geral;
- técnicas mais mencionadas;
- evolução temporal dos termos;
- termos encontrados em trechos de trabalhos futuros;
- heatmap artigo × termo.

Saídas principais:

```text
resultados/observacoes/palavras_mais_citadas.png
resultados/observacoes/nuvem_palavras_geral.png
resultados/observacoes/tecnicas_mais_mencionadas.png
resultados/observacoes/evolucao_temporal_termos.png
resultados/observacoes/termos_trabalhos_futuros.png
resultados/observacoes/heatmap_artigo_termo.png
resultados/observacoes/observacoes_resumo.json
resultados/observacoes/trechos_trabalhos_futuros.txt
```

## Observação sobre os arquivos gerados

Os arquivos das pastas `resultados/` e `ontologia/` podem conter trechos copiados diretamente dos artigos analisados. Esses trechos são saídas do sistema de PLN e servem para mostrar o resultado da extração automática, não sendo texto autoral do membros da dupla.

## Autores

Lucas de Oliveira Fratus  
Matheus Cenerini Jacomini

## Artigos Analisados

Termo de busca: **"Quantum Computing"**, Base: **Scopus**
 
1. GARCÍA PINEDA, Vanessa et al. Integrating artificial intelligence and quantum computing: a systematic literature review of features and applications. **International Journal of Cognitive Computing in Engineering**, v. 7, p. 26–39, 2026. DOI: [10.1016/j.ijcce.2025.08.002](https://doi.org/10.1016/j.ijcce.2025.08.002)
2. PANDEY, Shyambabu; PAKRAY, Partha; ZANZOTTO, Fabio Massimo. Quantum recurrent neural network for sequential labeling. **Knowledge and Information Systems**, v. 68, n. 84, 2026. DOI: [10.1007/s10115-026-02685-6](https://doi.org/10.1007/s10115-026-02685-6)
3. BHARATHI, Indira; SONAI, Veeramani; SRIDEVI, S. Quantum-driven enhanced machine learning algorithm for intrusion detection in Internet of Things environment. **EPJ Quantum Technology**, v. 13, n. 20, 2026. DOI: [10.1140/epjqt/s40507-026-00463-5](https://doi.org/10.1140/epjqt/s40507-026-00463-5)
4. LARASATI, Harashta Tatimma; CHOI, Byung-Soo. Circuit-based vs. measurement-based quantum computing: a comparative analysis, layered metrics, and decision flow for approach selection. **EPJ Quantum Technology**, v. 13, n. 39, 2026. DOI: [10.1140/epjqt/s40507-026-00483-1](https://doi.org/10.1140/epjqt/s40507-026-00483-1)
5. MENGONI, Riccardo et al. Efficient gate reordering for distributed quantum compiling in data centers. **EPJ Quantum Technology**, v. 13, n. 65, 2026. DOI: [10.1140/epjqt/s40507-026-00513-y](https://doi.org/10.1140/epjqt/s40507-026-00513-y)
6. LIU, Ang et al. Semi-quantum blockchain. **Discover Computing**, v. 29, n. 124, 2026. DOI: [10.1007/s10791-026-09990-2](https://doi.org/10.1007/s10791-026-09990-2)
7. SINGH, Siddhant et al. Modular architectures and entanglement schemes for error-corrected distributed quantum computation. **npj Quantum Information**, 2025. DOI: [10.1038/s41534-025-01146-2](https://doi.org/10.1038/s41534-025-01146-2)
8. NGUYEN, Nam et al. Quantum computing for corrosion simulation: workflow and resource analysis. **npj Quantum Information**, 2025. DOI: [10.1038/s41534-025-01171-1](https://doi.org/10.1038/s41534-025-01171-1)
9. GAO, Dingchao et al. Optimal compilation strategies for QFT circuits in neutral-atom quantum computing. **Scientific Reports**, v. 16, n. 2719, 2026. DOI: [10.1038/s41598-025-32572-z](https://doi.org/10.1038/s41598-025-32572-z)
10. ALSUBAI, Shtwai et al. Quantum transfer learning for cross-domain cybersecurity threat detection and categorization. **Scientific Reports**, v. 16, n. 10258, 2026. DOI: [10.1038/s41598-026-40634-z](https://doi.org/10.1038/s41598-026-40634-z)
11. LELLA, Kranthi Kumar; KRISHNA, Mallu Shiva Rama. QRGEC: quantum reinforcement learning with golden jackal optimization for resilient edge cloud coordination in internet computing. **Scientific Reports**, v. 16, n. 12766, 2026. DOI: [10.1038/s41598-026-42859-4](https://doi.org/10.1038/s41598-026-42859-4)
12. NALINI, S. et al. Quantum enabled cloud IoT collaboration for ultra low latency data processing in cyber physical systems. **Discover Internet of Things**, v. 6, n. 53, 2026. DOI: [10.1007/s43926-026-00316-8](https://doi.org/10.1007/s43926-026-00316-8)
