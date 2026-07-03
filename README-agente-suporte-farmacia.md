# 🤖 Agente de IA para Suporte N1 — Software de Gestão Farmacêutica

Agente conversacional inteligente que automatiza o atendimento de suporte nível 1 (dúvidas frequentes e solução de problemas) para os usuários de um software de gestão de farmácias, reduzindo o tempo de resposta e a carga sobre a equipe humana de suporte.

> 🔒 **Nota sobre confidencialidade:** por se tratar de um projeto desenvolvido para uma empresa real, nomes, dados de clientes e credenciais foram removidos/anonimizados. O código e os fluxos aqui apresentados servem para demonstrar a arquitetura e a solução técnica.

---

## 📌 Contexto e Problema

A empresa recebia um alto volume de chamados de suporte repetitivos — em sua maioria dúvidas frequentes e problemas simples (nível 1) — que consumiam tempo da equipe de suporte humano e geravam filas de espera para os usuários do software.

**Objetivo:** criar um agente de IA capaz de entender a pergunta do usuário, buscar a resposta correta na base de conhecimento da empresa e responder automaticamente, escalando para um humano apenas quando necessário.

---

## 🧠 Solução

Foi desenvolvido um agente de IA com **abordagem híbrida de busca de conhecimento**:

1. O usuário envia uma pergunta (texto **ou áudio**) pelo canal de atendimento
2. O n8n recebe a mensagem e orquestra todo o fluxo
3. A pergunta é transformada em embedding e comparada com a base vetorizada no **Supabase (pgvector)**
4. Caso não haja um resultado satisfatório na base vetorial, o agente busca diretamente nos documentos originais (fallback)
5. O modelo de linguagem (LLM) gera a resposta com base no contexto recuperado
6. A resposta é enviada de volta ao usuário

```
Usuário (texto/áudio)
        │
        ▼
   Workflow n8n
        │
        ▼
 Transcrição de áudio (se aplicável)
        │
        ▼
 Geração de embedding da pergunta
        │
        ▼
 Busca vetorial no Supabase (pgvector)
        │
   ┌────┴────┐
   │ achou?  │
   └────┬────┘
     não│  sim
        ▼    ▼
 Busca no   Contexto
 documento  recuperado
 original       │
        └──────►│
                 ▼
        LLM gera resposta
        (GPT → migrado para Claude)
                 ▼
        Resposta ao usuário
```

*(Substituir pelo diagrama real exportado do n8n / print da interface)*

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Ferramentas |
|---|---|
| Orquestração / Automação | **n8n** |
| Infraestrutura | **Google Cloud** |
| Banco vetorial | **Supabase** (pgvector) |
| IA / NLP | Embeddings, técnicas de PNL com **Python** |
| LLM | GPT (versão inicial) → migrado para **Claude** |
| Entrada de dados | Texto e **áudio** (transcrição) |

---

## 📈 Resultados e Impacto

- ⏱️ **Redução de ~60% no tempo de resposta**: de 40s–1min para menos de 25s por atendimento, após otimizações na arquitetura de busca e no fluxo do agente
- 🎙️ **Novo canal de entrada**: implementação do suporte a **mensagens de áudio**, ampliando a acessibilidade para os usuários
- 🎯 **Base vetorial enxuta e eficiente**: a vetorização foi tão bem ajustada que, em todos os testes realizados, o agente nunca precisou recorrer ao fallback de busca direta no documento — a base vetorial supabase deu conta de praticamente 100% dos casos
- 🔁 **Flexibilidade de LLM**: arquitetura desacoplada permitiu migrar de GPT para Claude sem redesenhar o fluxo

---

## 🖼️ Demonstração

*(Inserir aqui os prints: fluxo completo no n8n, exemplo de conversa do agente respondendo, print do Supabase com os embeddings)*

`/screenshots/fluxo-n8n.png`
`/screenshots/agente-respondendo.png`

---

## 💡 Principais Aprendizados

- Arquiteturas híbridas (vetorial + fallback documental) aumentam a robustez sem comprometer performance quando a vetorização é bem projetada
- A escolha do LLM pode e deve ser desacoplada da lógica de orquestração, facilitando testes A/B entre modelos
- Otimizações no pipeline de busca (redução de ~60% no tempo de resposta) tiveram tanto impacto na experiência do usuário quanto a qualidade da resposta em si

---

## 🚀 Possíveis Evoluções

- Dashboard de métricas de atendimento (taxa de resolução automática, tempo médio, temas mais recorrentes)
- Escalonamento automático para humano baseado em confiança da resposta
- Fine-tuning ou prompt-tuning específico para o domínio farmacêutico

---

## 📂 Estrutura do Repositório

```
/workflows        → exports do n8n (JSON)
/scripts          → scripts Python (embeddings, PNL, integrações)
/screenshots      → prints do fluxo e da interface
README.md
```
