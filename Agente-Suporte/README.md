# 🤖 Agente de IA para Suporte N1 — Software de Gestão Farmacêutica

Agente conversacional inteligente que automatiza o atendimento de suporte nível 1 (dúvidas frequentes e solução de problemas) para os usuários de um software de gestão de farmácias, reduzindo o tempo de resposta e a carga sobre a equipe humana de suporte.

> 🔒 **Nota sobre confidencialidade:** por se tratar de um projeto desenvolvido para uma empresa real, nomes, dados de clientes e credenciais foram removidos/anonimizados. O código e os fluxos aqui apresentados servem para demonstrar a arquitetura e a solução técnica.

---

## 📌 Contexto e Problema

A empresa recebia um alto volume de chamados de suporte repetitivos — em sua maioria dúvidas frequentes e problemas simples (nível 1) — que consumiam tempo da equipe de suporte humano e geravam filas de espera para os usuários do software.

**Objetivo:** criar um agente de IA capaz de entender a pergunta do usuário, buscar a resposta correta na base de conhecimento da empresa e responder automaticamente, escalando para um humano apenas quando necessário.

---

## 🧠 Solução

A solução é composta por **dois workflows complementares no n8n**:

### 🔹 Fluxo 1 — Atendimento em tempo real (via WhatsApp)

1. **WhatsApp Trigger**: usuário envia uma mensagem
2. **Tem áudio?**: roteamento condicional
   - Se **sim** → baixa o áudio e transcreve (Whisper) antes de seguir
   - Se **não** → segue direto com o texto
3. **Extrair texto** / **Normalizar campo pergunta**: padroniza a pergunta do usuário
4. **Buscar no Supabase**: gera o embedding da pergunta e busca por similaridade na base vetorial (pgvector)
5. **Avaliar resultados**: verifica a qualidade/relevância do que foi encontrado
6. **Agente de IA**: recebe o contexto recuperado e gera a resposta
   - **Modelo de LLM**: GPT (versão inicial) → migrado para Claude
   - **Postgres Chat Memory**: mantém o histórico da conversa por usuário
   - **Tool — Get a document in Google Docs**: dá ao agente a capacidade de buscar sob demanda o conteúdo completo de um documento específico do Google Docs, como fonte de contexto adicional além da busca vetorial
7. **Enviar resposta**: retorno automático ao usuário via WhatsApp

### 🔹 Fluxo 2 — Indexação automática da base de conhecimento

1. **Trigger agendado**: executa em intervalos programados
2. **Listar documentos**: busca arquivos numa pasta do Google Drive
3. **Processar 1 por vez**: itera sobre os documentos encontrados
4. **Baixar e converter**: faz download do arquivo do Drive
5. **Preparar conteúdo** → **Default Data Loader + Text Splitter**: quebra o documento em chunks
6. **Upsert no Supabase**: gera os embeddings de cada chunk e grava/atualiza na base vetorial

Esse segundo fluxo é o que mantém a base de conhecimento sempre atualizada automaticamente, sem intervenção manual — bastando adicionar/atualizar documentos na pasta do Drive.

![Fluxo do agente de suporte no n8n](./screenshots/fluxo-n8n.png)

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

**Fluxos no n8n** (atendimento em tempo real + indexação automática):

![Fluxo do agente de suporte no n8n](./screenshots/fluxo-n8n.png)

**Exemplo de resposta do agente** (nome do produto ocultado por confidencialidade):

![Exemplo de conversa com o agente](./screenshots/agente-respondendo-anonimizado.png)

*O exemplo acima mostra o agente guiando um usuário passo a passo em um procedimento operacional do sistema (envio de inventário obrigatório a um órgão regulador), com formatação clara e organizada para leitura via WhatsApp.*

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
