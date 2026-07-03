# 📄 Pipeline de Tratamento de Textos para Base de Conhecimento de Agente IA

Conjunto de scripts em Python responsável por transformar documentos internos extensos e desorganizados (Word) em uma base de conhecimento estruturada, limpa e pronta para ser vetorizada e consumida por um agente de IA via RAG (Retrieval-Augmented Generation).

> 🔗 Este projeto é a etapa de **preparação de dados** que alimenta o [Agente de IA para Suporte N1](../agente-suporte-farmacia) — foi desativado em repositório próprio por ser um pipeline extenso e com valor técnico independente.

> 🔒 **Nota sobre confidencialidade:** todo o conteúdo real da base de conhecimento (nomes de empresa, procedimentos internos, dados de negócio) foi removido/substituído por exemplos genéricos. Os scripts aqui mantêm 100% da lógica original de processamento, mas sem nenhuma informação proprietária ou credencial real.

---

## 📌 Contexto e Problema

A base de conhecimento original estava em **documentos Word muito longos e desorganizados**: textos corridos, numeração hierárquica inconsistente, blocos de conteúdo excessivamente extensos e sem padronização — o que prejudicava diretamente a qualidade da vetorização (chunks ruins geram embeddings ruins, que geram respostas ruins do agente).

**Objetivo:** transformar esse material bruto em uma base estruturada, hierárquica e "chunkada" de forma inteligente, adequada para gerar embeddings de alta qualidade.

---

## 🧠 Pipeline de Tratamento

O processo foi dividido em **6 scripts especializados**, cada um responsável por uma etapa da transformação:

```
Documento Word (bruto, desorganizado)
            │
            ▼
┌─────────────────────────────┐
│ 1. converter_docs.py         │  → Remove índice redundante, identifica hierarquia
│    (.txt → Markdown)         │    numérica (1 / 1.1 / 1.1.1), separa FAQ, regras
│                               │    para IA e observações, insere placeholders de
│                               │    contexto para revisão humana
└──────────────┬───────────────┘
               ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐
│ 2. formatacao_base_ia.py     │    │ 3. geracao_indices.py        │
│    Gera documento formatado  │    │    Gera índice hierárquico   │
│    no Google Docs (tópicos,  │    │    navegável no Google Docs  │
│    subtópicos, recuo, fonte) │    │    para conferência humana   │
│    para revisão visual       │    │                               │
└──────────────┬───────────────┘    └───────────────┬───────────────┘
               │                                     │
               └──────────────────┬──────────────────┘
                                   ▼
               ┌─────────────────────────────────────┐
               │ 4. conteudos_extensos.py              │
               │    Auditoria automática: identifica   │
               │    subtópicos longos demais (por      │
               │    caracteres/linhas/palavras) que     │
               │    prejudicariam a qualidade do chunk  │
               │    → gera relatório em PDF             │
               └──────────────────┬─────────────────────┘
                                   ▼
               ┌─────────────────────────────────────┐
               │ 5. migrando_para_json.py              │
               │    Converte o texto final, já revisado │
               │    e ajustado, em uma estrutura JSON   │
               │    hierárquica (tópico → subtópico →   │
               │    conteúdo), pronta para embeddar     │
               └──────────────────┬─────────────────────┘
                                   ▼
               ┌─────────────────────────────────────┐
               │ 6. embeddings_supabase.py              │
               │    Gera o embedding de cada chunk      │
               │    (Ollama) e faz o upsert na base      │
               │    vetorial do Supabase (pgvector)      │
               └─────────────────────────────────────────┘
                                   ▼
                  Base vetorial pronta para o agente de IA
```

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Ferramentas |
|---|---|
| Linguagem | **Python** (desenvolvido em notebooks Google Colab) |
| Processamento de texto | **Regex**, manipulação de strings, parsing hierárquico |
| Documentação/Revisão | **Google Docs API** (geração automática de documentos formatados) |
| Geração de relatórios | **ReportLab** (PDF de auditoria de conteúdos extensos) |
| Embeddings | **Ollama** (modelo `qwen3-embedding`) |
| Banco vetorial | **Supabase** (pgvector) |
| Estrutura de dados | **JSON** hierárquico (tópico → subtópico → conteúdo) |

---

## 📈 Desafios e Soluções

- **Documentos muito longos e desorganizados**: os textos originais em Word não seguiam um padrão estrutural único (numeração inconsistente, tópicos misturados, rótulos como "ASSUNTO:" usados de forma irregular). A solução foi um conjunto de funções de normalização via regex (`corrigir_hifens`, `corrigir_rotulos`, `quebrar_blocos_numerados`) que padronizam a numeração hierárquica antes de qualquer outra etapa.
- **Chunks desbalanceados**: alguns subtópicos ficavam grandes demais para gerar embeddings de qualidade. Foi criado um script dedicado (`conteudos_extensos.py`) que audita automaticamente todo o conteúdo e gera um relatório em PDF apontando quais subtópicos ultrapassam limites de caracteres/linhas/palavras definidos, permitindo revisão e quebra manual desses trechos antes da vetorização.
- **Revisão humana necessária**: como o conteúdo trata de procedimentos operacionais sensíveis, o pipeline foi desenhado para **nunca pular a revisão humana** — os scripts 2 e 3 geram documentos formatados e índices navegáveis no Google Docs justamente para facilitar essa conferência antes dos dados irem para produção.

---

## 📊 Resultados

> *(Preencher com os números reais do seu projeto)*

- 📄 **Documentos processados:** `[preencher]`
- 🧩 **Tópicos/subtópicos estruturados:** `[preencher]`
- ✂️ **Chunks gerados para embedding:** `[preencher]`
- ⚠️ **Conteúdos extensos identificados e ajustados:** `[preencher]`
- 🎯 **Impacto direto:** base vetorial mais enxuta e precisa, eliminando a necessidade de fallback para busca direta em documentos no [agente de suporte](../agente-suporte-farmacia) em praticamente 100% dos casos testados

---

## 💡 Principais Aprendizados

- Qualidade de RAG começa na preparação dos dados, não no modelo: um bom pipeline de limpeza e chunking tem impacto tão grande quanto a escolha do LLM ou da estratégia de busca
- Automatizar a **auditoria de qualidade** (script de conteúdos extensos) evita que problemas de chunking só sejam percebidos depois, já em produção
- Manter uma etapa de revisão humana assistida por documentos gerados automaticamente (Google Docs formatado + índice) tornou o processo de curadoria muito mais rápido do que revisar o texto bruto

---

## 📂 Estrutura do Repositório

```
/scripts
  01_formatacao_base_ia.py      → Gera documento formatado no Google Docs
  02_converter_docs.py          → Converte .txt bruto em Markdown estruturado
  03_geracao_indices.py         → Gera índice hierárquico no Google Docs
  04_migrando_para_json.py      → Converte texto estruturado em JSON hierárquico
  05_conteudos_extensos.py      → Audita e reporta chunks longos demais (PDF)
  06_embeddings_supabase.py     → Gera embeddings e faz upsert no Supabase
.env.example                    → Modelo de variáveis de ambiente (sem valores reais)
README.md
```

> ⚠️ Os scripts 01, 03, 04 e 05 foram desenvolvidos como notebooks no Google Colab — a linha `!pip install ...` no topo é sintaxe de célula do Colab/Jupyter, não Python puro. Para rodar localmente, basta instalar as dependências via `pip install` no terminal antes de executar o script.

## 🚀 Como Executar

1. Instale as dependências: `pip install google-api-python-client google-auth google-auth-oauthlib reportlab requests supabase`
2. Copie `.env.example` para `.env` e preencha com suas credenciais do Supabase/Ollama
3. Execute os scripts na ordem do pipeline (converter → formatar/indexar → auditar → migrar para JSON → gerar embeddings)
