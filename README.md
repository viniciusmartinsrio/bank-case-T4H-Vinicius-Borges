# 🏦 Banco Ágil - Sistema de Atendimento Inteligente com LLM

Um sistema completo de atendimento bancário automatizado utilizando **LLM (Large Language Models)** e múltiplos agentes de IA especializados orquestrados por **LangGraph**. O sistema oferece conversação natural em português com capacidade de processamento contextual e tomada de decisões inteligentes.

## 📋 Visão Geral do Projeto

O Banco Ágil é uma solução de atendimento ao cliente para um banco digital, implementada com uma arquitetura moderna de agentes conversacionais. O sistema simula um atendimento bancário completo através de **linguagem natural**, desde a autenticação do cliente até operações complexas como solicitação de aumento de limite e recálculo de score de crédito.

### Características Principais

- ✅ **Conversação Natural com LLM**: Uso de Llama 3.1 8B via Groq API para diálogos fluidos e rápidos
- ✅ **Orquestração com LangGraph**: Máquina de estados para gerenciar fluxo entre agentes
- ✅ **Arquitetura que habilita Múltiplos Agentes Especializados**: Arquitetura preparada para utilizar diferentes LLM's para cada escopo de agente
- ✅ **Múltiplos Agentes Especializados**: Cada um com escopo e personalidade definidos
- ✅ **Autenticação Segura**: Validação de CPF e data de nascimento
- ✅ **Cálculo Inteligente de Score**: Entrevista financeira com recálculo automático
- ✅ **Persistência de Dados**: Atualização automática de score e limite em CSV
- ✅ **Consulta de Câmbio em Tempo Real**: Integração com API pública de cotações
- ✅ **Interface Web Moderna**: Streamlit com chat interativo e feedback visual

## 🏗️ Arquitetura do Sistema

### Estrutura Geral

```
bank-case-T4H-Vinicius-Borges/
├── agents/                              # Agentes especializados com LLM
│   ├── base_agent.py                   # Classe base (ChatGroq + prompts)
│   ├── triagem_agent_llm.py            # Autenticação e roteamento
│   ├── credito_agent_llm.py            # Operações de crédito
│   ├── entrevista_credito_agent_llm.py # Recálculo de score
│   └── cambio_agent_llm.py             # Consulta de câmbio
├── tools/                               # Ferramentas auxiliares
│   ├── data_manager.py                 # Gerenciamento de CSV
│   ├── score_calculator.py             # Fórmula de score
│   ├── currency_fetcher.py             # API de cotações
│   └── agent_tools.py                  # Tools do LangChain
├── data/                                # Dados persistentes
│   ├── clientes.csv                    # Base de clientes
│   ├── score_limite.csv                # Tabela score x limite
│   └── solicitacoes_aumento_limite.csv # Histórico de solicitações
├── banco_agil_langgraph.py             # Orquestrador LangGraph
├── app_cred_ai.py                      # Interface Streamlit
├── state.py                            # Definição do estado compartilhado
├── llm_config.py                       # Configuração do LLM
├── .env                                # API key do Groq (não versionado)
└── requirements.txt                    # Dependências Python
```

### Arquitetura da Aplicação

```
┌─────────────────────────────────────────────────────────────┐
│                    app_cred_ai.py                           │
│                  (Interface Streamlit)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              banco_agil_langgraph.py                        │
│            (Orquestrador LangGraph)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Máquina de Estados (StateGraph)            │  │
│  │                                                        │  │
│  │  [triagem] → [credito] → [entrevista] → [cambio]    │  │
│  │                    ↓                                   │  │
│  │              [encerramento]                           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│TriagemAgent  │  │CreditoAgent  │  │CambioAgent   │
│    LLM       │  │    LLM       │  │    LLM       │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────┐
│         Groq API (Llama 3.1 8B)                 │
└─────────────────────────────────────────────────┘
```

### Fluxo de Atendimento com LangGraph

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENTE INICIA CONVERSA                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  AGENTE DE TRIAGEM   │
                  │  (LLM conversacional)│
                  │  - Coleta CPF        │
                  │  - Coleta Data Nasc. │
                  │  - Autentica         │
                  │  - Apresenta Menu    │
                  └──────────┬───────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ CRÉDITO LLM  │    │ SCORE LLM    │    │ CÂMBIO LLM   │
│ - Consulta   │    │ - Entrevista │    │ - Cotações   │
│ - Solicita   │    │ - 5 perguntas│    │ - Conversão  │
│ - Aprova/Rej.│    │ - Calcula    │    │ - Tempo real │
└──────┬───────┘    └──────┬───────┘    └──────────────┘
       │                   │
       │ Rejeitado         │ Novo score
       └──────────►────────┘
                   Redireciona
```

### Parâmetros iniciais de LLM's por Agente

```
| Agente | Modelo | Temperature | Top-P | Max Tokens | Característica |
|--------|--------|-------------|-------|------------|----------------|
| Triagem | Llama 3.1 8B | 0.3 | 0.9 | 200 | Preciso, protocolar |
| Crédito | Llama 3.1 8B | 0.4 | 0.85 | 250 | Empático, claro |
| Entrevista | Llama 3.1 8B | 0.7 | 0.95 | 300 | Natural, conversacional |
| Câmbio | Llama 3.1 8B | 0.2 | 0.8 | 150 | Factual, conciso |
```

### Manipulação de Dados (DataManager)

O sistema utiliza operações atômicas sobre arquivos CSV através da classe `DataManager`:

```
┌────────────────────────────────────────────────────────────────┐
│                         DataManager                            │
│                  (tools/data_manager.py)                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. authenticate_client(cpf, data_nascimento)                 │
│     └─> Read clientes.csv                                     │
│     └─> Valida CPF + Data                                     │
│     └─> Return DadosCliente ou None                           │
│                                                                │
│  2. update_client_score(cpf, novo_score)                      │
│     └─> Read clientes.csv (pandas)                            │
│     └─> Update score_credito WHERE cpf = ?                    │
│     └─> Write clientes.csv (atômico)                          │
│                                                                │
│  3. update_client_limit(cpf, novo_limite)                     │
│     └─> Read clientes.csv                                     │
│     └─> Update limite_credito WHERE cpf = ?                   │
│     └─> Write clientes.csv                                    │
│                                                                │
│  4. get_limit_by_score(score)                                 │
│     └─> Read score_limite.csv                                 │
│     └─> Find range WHERE score_min <= score <= score_max      │
│     └─> Return limite_maximo                                  │
│                                                                │
│  5. register_limit_request(cpf, limite_atual, novo_limite,    │
│                             status)                            │
│     └─> Read solicitacoes_aumento_limite.csv                  │
│     └─> Append nova linha com timestamp                       │
│     └─> Write solicitacoes_aumento_limite.csv                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘

                              ▼

┌────────────────────────────────────────────────────────────────┐
│                      Arquivos CSV                              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  clientes.csv                                                  │
│  ├─ cpf (PK)                                                   │
│  ├─ data_nascimento                                            │
│  ├─ nome                                                       │
│  ├─ limite_credito (ATUALIZADO por update_client_limit)       │
│  └─ score_credito (ATUALIZADO por update_client_score)        │
│                                                                │
│  score_limite.csv (READ-ONLY)                                 │
│  ├─ score_minimo                                               │
│  ├─ score_maximo                                               │
│  └─ limite_maximo                                              │
│                                                                │
│  solicitacoes_aumento_limite.csv (APPEND-ONLY)                │
│  ├─ cpf_cliente                                                │
│  ├─ data_hora_solicitacao (timestamp)                         │
│  ├─ limite_atual                                               │
│  ├─ novo_limite_solicitado                                    │
│  └─ status_pedido (aprovado/rejeitado)                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Padrão de Consistência**:
1. **Read-Modify-Write Atômico**: Todas as atualizações seguem o padrão:
   - Ler CSV completo em memória (pandas DataFrame)
   - Aplicar modificações no DataFrame
   - Escrever CSV completo de volta (substitui arquivo)

2. **Append-Only para Auditoria**: `solicitacoes_aumento_limite.csv` nunca é modificado, apenas recebe novas linhas

3. **Validação Sempre via CSV**: Score x Limite sempre consultado em `score_limite.csv`, nunca hard-coded

### Tecnologias Principais

- **Python 3.8+**: Linguagem base
- **LangGraph**: Orquestração de agentes com máquina de estados
- **LangChain**: Framework para aplicações com LLM
- **Groq API**: Inferência ultra-rápida de LLM (Llama 3.1 8B)
- **Streamlit**: Interface web interativa
- **CSV**: Persistência de dados (clientes, scores, solicitações)
- **API Pública**: exchangerate-api.com para cotações

## ✨ Funcionalidades Implementadas

### 1. Autenticação Conversacional
- **Coleta de CPF**: Aceita diversos formatos (12345678901, 123.456.789-01)
- **Coleta de Data**: Normaliza múltiplos formatos (YYYY-MM-DD, DD/MM/YYYY, "15/05/1990")
- **Validação Segura**: Autenticação contra base de clientes em CSV
- **Tentativas Limitadas**: Máximo de 3 tentativas de login
- **Mensagens Claras**: Feedback específico sobre erros de autenticação

### 2. Gestão de Limite de Crédito
- **Consulta de Limite**: Visualização de limite atual e score
- **Solicitação de Aumento**: Processamento conversacional de pedidos
- **Validação Automática**: Regras baseadas em tabela score x limite
- **Aprovação/Rejeição**: Decisão instantânea com explicação detalhada
- **Persistência**: Atualização automática em `clientes.csv` e `solicitacoes_aumento_limite.csv`
- **Histórico**: Registro de data/hora, valores e status de todas as solicitações

### 3. Recálculo de Score de Crédito
- **Entrevista Estruturada**: 5 perguntas financeiras via conversação natural
- **Extração de Dados**: NLP para interpretar respostas livres:
  - "ganho 5 mil" → R$ 5.000,00
  - "trabalho registrado" → formal
  - "tenho dois filhos" → 2 dependentes
- **Cálculo Inteligente**: Fórmula multi-fatorial realista
- **Atualização Imediata**: Novo score salvo em CSV
- **Redirecionamento**: Retorno automático ao agente de crédito

### 4. Consulta de Câmbio em Tempo Real
- **API Pública**: Integração com exchangerate-api.com
- **Múltiplas Moedas**: Suporte a USD, EUR, GBP, JPY, ARS, e mais
- **Detecção Inteligente**: Reconhece "dólar", "euro", "libra" ou códigos ISO
- **Conversão Exemplificada**: Mostra conversões para R$ 1, R$ 100 e R$ 1000
- **Tratamento de Erros**: Mensagens claras sobre falhas de API

### 5. Orquestração com LangGraph
- **Máquina de Estados**: Transições controladas entre agentes
- **Roteamento Dinâmico**: Decisões baseadas em contexto
- **Proteção Anti-Loop**: Contador de iterações com limite de 3
- **Estado Compartilhado**: Contexto mantido entre transições
- **Encerramento Limpo**: Opção de logout a qualquer momento

### 6. Interface Web Interativa
- **Chat em Tempo Real**: Interface Streamlit com mensagens formatadas
- **Botões de Quick Reply**: Atalhos para menu principal
- **Histórico Visual**: Todas as mensagens mantidas na sessão
- **Feedback de Status**: Cliente autenticado exibido na sidebar
- **Reiniciar Conversa**: Botão para logout e nova sessão

---

## 🤖 Agentes Especializados

### 1. **Agente de Triagem** (`TriagemAgentLLM`)
- **Responsabilidade**: Porta de entrada conversacional
- **Funcionalidades**:
  - Saudação natural em português
  - Coleta de CPF com validação de formato (11 dígitos)
  - Coleta de data de nascimento (múltiplos formatos aceitos)
  - Autenticação **imediata** contra `clientes.csv`
  - Até 3 tentativas de login antes de bloquear
  - Apresentação de menu numerado (4 opções)
  - Identificação de intenção do usuário para roteamento
  - Tratamento de solicitação de encerramento
- **Tecnologias**: ChatGroq (Llama 3.1 8B), DataManager
- **Arquivo**: `agents/triagem_agent_llm.py`

### 2. **Agente de Crédito** (`CreditoAgentLLM`)
- **Responsabilidade**: Gestão completa de limite de crédito
- **Funcionalidades**:
  - Consulta de limite atual e score do cliente
  - Processamento de solicitações de aumento em linguagem natural
  - Extração de valores monetários ("quero 8 mil" → R$ 8.000)
  - Validação automática contra tabela `score_limite.csv`
  - Aprovação instantânea se dentro do limite permitido
  - Rejeição com explicação se exceder limite
  - Atualização de limite em `clientes.csv` quando aprovado
  - Oferta proativa de entrevista financeira se rejeitado
  - Registro timestampado em `solicitacoes_aumento_limite.csv`
- **Tecnologias**: ChatGroq (Llama 3.1 8B), DataManager, regex para extração de valores
- **Arquivo**: `agents/credito_agent_llm.py`

### 3. **Agente de Entrevista de Crédito** (`EntrevistaCreditoAgentLLM`)
- **Responsabilidade**: Recálculo de score através de entrevista
- **Funcionalidades**:
  - Entrevista estruturada em 5 etapas sequenciais
  - Extração de dados de linguagem natural:
    - **Renda mensal**: "ganho 5 mil" → R$ 5.000,00
    - **Tipo de emprego**: "CLT" → formal, "freelancer" → autônomo
    - **Despesas fixas**: "pago 2000 de contas" → R$ 2.000,00
    - **Dependentes**: "tenho 2 filhos" → 2
    - **Dívidas**: "não tenho dívida" → False
  - Cálculo de novo score usando `ScoreCalculator`
  - Atualização automática em `clientes.csv`
  - Mensagem final com instrução para voltar ao menu
  - Contexto preservado para redirecionamento ao CreditoAgent
- **Tecnologias**: ChatGroq (Llama 3.1 8B), ScoreCalculator, DataManager, regex avançado
- **Arquivo**: `agents/entrevista_credito_agent_llm.py`

### 4. **Agente de Câmbio** (`CambioAgentLLM`)
- **Responsabilidade**: Consultas de cotação de moedas estrangeiras
- **Funcionalidades**:
  - Busca de cotações em tempo real via API pública
  - Suporte a 30+ moedas (USD, EUR, GBP, JPY, ARS, CAD, etc.)
  - Detecção de moeda em linguagem natural ("dólar" → USD)
  - Apresentação formatada com exemplos de conversão
  - Conversão para múltiplos valores (R$ 1, R$ 100, R$ 1000)
  - Tratamento de erros de API (timeout, moeda inválida)
  - Opção de consultar outra moeda ou retornar ao menu
- **Tecnologias**: ChatGroq (Llama 3.1 8B), CurrencyFetcher (requests + API pública)
- **Arquivo**: `agents/cambio_agent_llm.py`

## 🗄️ Estrutura de Dados

### `data/clientes.csv`
Base de clientes (atualizada automaticamente):

```csv
cpf,data_nascimento,nome,limite_credito,score_credito
12345678901,1990-05-15,João Silva,5000.00,750
98765432109,1985-08-22,Maria Santos,8000.00,820
55555555555,1992-03-10,Pedro Oliveira,10000.00,650
```

### `data/score_limite.csv`
Tabela de relação score x limite máximo:

```csv
score_minimo,score_maximo,limite_maximo
0,500,2000
501,600,5000
601,700,10000
701,800,15000
801,900,25000
901,1000,50000
```

### `data/solicitacoes_aumento_limite.csv`
Histórico de solicitações (append-only):

```csv
cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido
12345678901,2026-01-24T10:30:00.123456,5000.00,8000.00,aprovado
```

## 🚀 Como Executar

### Pré-requisitos

- Python 3.8+
- Conta no Groq (gratuita): https://console.groq.com/keys

### Instalação

1. **Clone o repositório**
```bash
git clone <repo-url>
cd bank-case-T4H-Vinicius-Borges
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Configure a API key do Groq**
```bash
# Copie o template
cp .env.example .env

# Edite .env e adicione sua chave
GROQ_API_KEY=gsk_sua_chave_aqui
```

4. **Execute a aplicação**
```bash
streamlit run app_cred_ai.py
```

A aplicação abrirá em `http://localhost:8501`

### Dados de Teste

Use os seguintes clientes para testar:

| CPF | Data Nascimento | Nome |
|-----|-----------------|------|
| 12345678909 | 1990-05-15 | Vinicius Martins
| 12345678901 | 1985-08-22 | Maria Santos

## 🧪 Fluxos de Teste

### Fluxo 1: Consulta de Limite
1. Digite CPF: `12345678909`
2. Digite data: `1990-05-15`
3. Clique no botão "Crédito" ou digite `1`
4. Visualize limite atual: R$ 5.000,00

### Fluxo 2: Solicitação Aprovada
1. Autentique com CPF `12345678901` (score 820)
2. Escolha "Crédito"
3. Digite: "Quero solicitar aumento para 12000"
4. Sistema valida: 820 permite até R$ 15.000
5. **Aprovação automática** + atualização em CSV

### Fluxo 3: Solicitação Rejeitada + Entrevista
1. Autentique com CPF `12345678909` (score 650)
2. Escolha "Crédito"
3. Digite: "Quero 15000 de limite"
4. Sistema rejeita (650 permite apenas R$ 10.000)
5. Sistema oferece entrevista financeira
6. Digite: "Sim" ou "1"
7. Responda as 5 perguntas
8. Novo score calculado e atualizado
9. Redirecionamento automático para crédito

### Fluxo 4: Consulta de Câmbio
1. Autentique normalmente
2. Clique em "Câmbio" ou digite `3`
3. Digite: "USD" ou "Quanto está o dólar?"
4. Visualize cotação em tempo real
5. Sistema oferece consultar outra moeda

## 🚧 Desafios Enfrentados e Soluções

### 1. Engenharia de Prompts dos Agentes de IA
**Desafio**: Decidir quais funcionalidades os LLM's + Placeholders absorviriam Versus quais funcionalidades seriam em Python (hardcode), presando por boas práticas de Engenharia de Prompt e otimização de custos + performance dos LLM's.

**Solução Implementada**: Implementar funcionalidades hardcode para otimizar performance e número de tokens ($$$) e deixar os LLM's focados em performar apenas como "atendente de linguagem natural" (sem "reasonings" que podem absorver alguma funcionalidade do projeto - como buscar publicamente cotação de moeda por exemplo)

### 2. Dinâmica de estados dos agentes
**Desafio**: Definir melhor solução para controle de estados dos Agentes

**Solução Implementada**: Uso do TypedDict: Type safety; Auto-complete no IDE; Documentação implícita; Compatibilidade com LangGraph

### 3. Loop Infinito no LangGraph
**Desafio**: Sistema ficava processando indefinidamente após receber input do usuário, causando travamento da interface.

**Causa Raiz**: A função `_decidir_proximo_passo()` retornava o nome de um agente (ex: `"triagem"`) ao invés de `END` quando aguardava nova mensagem do usuário. Isso causava um loop: triagem → decisão → triagem → decisão...

**Solução Implementada**:
```python
# ANTES (causava loop)
if not estado.get("cliente_autenticado"):
    return "triagem"  # Loop infinito!

# DEPOIS (correção)
if not estado.get("cliente_autenticado"):
    return END  # Aguarda próxima mensagem do usuário
```

**Proteção Adicional**: Implementado contador de loops com limite de 3 iterações para detectar e prevenir futuros loops.

**Arquivo**: `banco_agil_langgraph.py:_decidir_proximo_passo()`

---


## 💡 Escolhas Técnicas e Justificativas

### 1. Por que LangGraph ao invés de Chain simples?

**Decisão**: Utilizar LangGraph como orquestrador principal.

**Alternativas consideradas**:
- LangChain Chains simples (sequenciais)
- CrewAI
- AutoGen
- Implementação manual com classes Python

**Justificativas**:
1. **Máquina de Estados Explícita**: LangGraph permite definir claramente todos os estados possíveis (triagem, crédito, entrevista, câmbio, encerramento) e transições entre eles. Isso facilita raciocínio sobre o fluxo.

2. **Roteamento Condicional**: A função `add_conditional_edges()` permite decisões dinâmicas baseadas no estado, essencial para um sistema bancário onde diferentes clientes seguem diferentes fluxos.

3. **Controle de Loops**: Diferente de chains sequenciais, LangGraph permite voltar a estados anteriores (ex: entrevista → crédito) sem causar loops infinitos graças ao uso de `END`.

4. **Debug e Observabilidade**: Cada nó do grafo é isolado, facilitando debug. Logs mostram claramente qual nó está executando.

5. **Escalabilidade**: Adicionar novos agentes é simples: criar nó → adicionar transições. Não requer reestruturar todo o código.

**Trade-off**: Maior complexidade inicial comparado a chains simples, mas ganho significativo em manutenibilidade para sistemas multi-agente complexos.

---

### 2. Por que Groq API ao invés de outros providers?

**Decisão**: Utilizar Groq para inferência de LLM.

**Alternativas consideradas**:
- OpenAI API (GPT-4)
- Anthropic Claude API
- Modelos locais (Ollama)
- Azure OpenAI

**Justificativas**:
1. **Velocidade de Inferência**: Groq entrega respostas em < 1 segundo graças à sua arquitetura LPU (Language Processing Unit), crucial para UX de chat em tempo real.

2. **Free Tier Generoso**: 100k tokens/dia gratuitos, suficiente para prototipagem e testes extensivos sem custos.

3. **Modelo Rápido e Eficiente**: Llama 3.1 8B oferece boa capacidade de conversação em português com inferência extremamente rápida (< 500ms) e consumo eficiente de tokens.

4. **Simplicidade de Integração**: LangChain tem integração nativa (`langchain-groq`), reduzindo complexidade.

5. **Sem Infraestrutura**: Diferente de modelos locais, não requer GPU, VRAM, ou configuração complexa.

**Trade-off**: Dependência de API externa (requer conexão internet). Mitigado com tratamento robusto de erros de rede.

**Nota sobre Modelo Ativo**: O projeto está configurado para usar **Llama 3.1 8B** (linha 32 de `llm_config.py`). O modelo maior **Llama 3.3 70B** está disponível mas desativado para economizar tokens do free tier. Para ativar o modelo maior:
```python
# Em llm_config.py, linha 32
ACTIVE_MODEL = DEFAULT_MODEL  # Troca para 70B (mais capaz, mais lento, mais tokens)
```

---

### 3. Por que não sugerir um SGBD ao invés de usar CSV?

**Decisão**: Utilizar arquivos CSV para persistência.

**Alternativas consideradas**:
- PostgreSQL / MySQL (relacional)
- MongoDB (NoSQL)
- SQLite (embedded)

**Justificativas**:
1. **Prototipagem Rápida**: Foco em validar lógica de negócio e agentes, não em engenharia de dados.

2. **Simplicidade de Setup**: Zero configuração - basta ter Python e pandas. Não requer instalar/configurar servidor de banco.

3. **Portabilidade**: Arquivos CSV funcionam em qualquer ambiente (Windows, Linux, Mac) sem dependências adicionais.

4. **Inspeção Manual Fácil**: Qualquer pessoa pode abrir CSV em Excel/LibreOffice e verificar dados. Essencial para debug e validação.

5. **Operações Atômicas**: Implementamos padrão read-modify-write que funciona bem para volumes baixos (< 1000 clientes).

6. **Migração Futura Simples**: Estrutura tabular se traduz diretamente para tabelas SQL. Migrar para PostgreSQL é trivial:
   ```python
   # Migração futura (1 linha)
   df.to_sql('clientes', engine, if_exists='replace')
   ```

**Trade-off**: Não escalável para produção com múltiplos usuários concorrentes. Adequado para protótipo e demo.

**Quando migrar para BD**: Quando houver:
- > 1000 clientes
- Necessidade de transações ACID
- Múltiplos processos concorrentes
- Requisitos de auditoria avançada

---

### 4. Por que Streamlit ao invés de outras interfaces?

**Decisão**: Utilizar Streamlit para interface web.

**Alternativas consideradas**:
- Flask/FastAPI + React
- Gradio
- CLI puro (terminal)
- Jupyter Notebook

**Justificativas**:
1. **Desenvolvimento Rápido**: Streamlit permite criar interface interativa em < 50 linhas de código Python puro, sem HTML/CSS/JS.

2. **Componentes de Chat Nativos**: `st.chat_message()` e `st.chat_input()` são perfeitos para aplicações conversacionais.

3. **Reatividade Automática**: Sistema de rerun automático mantém UI sincronizada com estado.

4. **Session State Integrado**: `st.session_state` permite manter contexto entre interações sem backend complexo.

5. **Deploy Simples**: Streamlit Cloud permite deploy gratuito com 1 clique.

**Trade-off**: Menos controle sobre UI comparado a React. Adequado para demos e protótipos, não para aplicações enterprise complexas.

---

### 5. Por que Arquitetura de Agentes Especializados?

**Decisão**: Criar agentes separados (Triagem, Crédito, Entrevista, Câmbio) ao invés de um único agente monolítico.

**Alternativas consideradas**:
- Agente único com prompt gigante
- Sistema de sub-prompts dinâmicos
- Função calling sem agentes

**Justificativas**:
1. **Separação de Responsabilidades**: Cada agente tem escopo bem definido, facilitando manutenção e testes.

2. **Prompts Otimizados**: Cada agente tem prompt específico para sua tarefa, diminuindo a chance de alucinações e melhorando qualidade das respostas e guardrails.

3. **Contexto Isolado**: Dados temporários de cada agente não poluem o contexto global.

4. **Testabilidade**: Cada agente pode ser testado isoladamente com mocks.

5. **Reutilização e Hybrid-LLM's**: Agentes podem ser usados em outros contextos (ex: CambioAgent em outro sistema) em com diferentes LLM's.

6. **Escalabilidade**: Novos serviços bancários = novos agentes, sem modificar existentes (Open/Closed Principle).

**Padrão de Design**: Strategy Pattern - cada agente é uma estratégia de processamento diferente.

---

### 6. Por que BaseAgent com Herança?

**Decisão**: Criar classe `BaseAgent` com lógica comum de LLM.

**Alternativas consideradas**:
- Composição (passar LLM como dependência)
- Funções utilitárias ao invés de classes
- Cada agente implementar do zero

**Justificativas**:
1. **DRY (Don't Repeat Yourself)**: Configuração do LLM, carregamento de prompts, e invocação são idênticos. Código comum fica em um só lugar.

2. **Consistência**: Todos os agentes usam mesma configuração (temperatura, modelo, max_tokens).

3. **Facilidade de Mudança**: Trocar de Groq para OpenAI requer alterar apenas `BaseAgent.__init__()`.

4. **Hierarquia Clara**: Relação "É-UM" (TriagemAgent **é um** BaseAgent) é semanticamente correta.

**Padrão de Design**: Template Method Pattern - `BaseAgent` define estrutura, subclasses implementam `processar_mensagem()`.

---

### 7. Por que Validação de Score em CSV ao invés de Hard-coded?

**Decisão**: Tabela `score_limite.csv` configurável ao invés de constantes no código.

**Alternativas consideradas**:
- Constantes Python (`SCORE_RANGES = {...}`)
- Fórmula matemática (ex: `limite = score * 50`)
- Regras hard-coded com if/elif

**Justificativas**:
1. **Configurabilidade**: Gerente do banco pode alterar tabela sem mexer em código Python.

2. **Auditabilidade**: Mudanças em limites ficam registradas no histórico do arquivo CSV.

3. **Validação de Negócio**: Não programadores podem revisar e validar regras.

4. **Flexibilidade**: Regras complexas (ex: limites diferentes por região) são possíveis apenas adicionando colunas.

**Trade-off**: Leitura de CSV a cada validação (custo negligível para volumes baixos). Otimização futura: cache em memória.

---

### 8. Por que "proteção contra loops com contador"?

**Decisão**: Implementar contador de loops com limite de 3 iterações.

**Justificativas**:
1. **Fail-Safe**: Mesmo com bugs futuros, sistema não trava indefinidamente.

2. **Debug Facilitado**: Logs mostram claramente quando limite é atingido.

3. **UX**: Usuário não fica esperando infinitamente.

**Implementação**:
```python
self._contador_loop = 0

if self._contador_loop > 3:
    print("[AVISO] Loop detectado!")
    return END
```

**Trade-off**: Limita fluxos legítimos muito complexos. Valor de 3 escolhido empiricamente (suficiente para casos reais, protege contra bugs).

## 📈 Possíveis Próximas Melhorias

1. **RAG (Retrieval Augmented Generation)**
   - Consulta a documentos bancários
   - Respostas baseadas em regulamentação

2. **Banco de Dados Relacional**
   - Migrar de CSV para PostgreSQL
   - Transações ACID

3. **Autenticação Multi-fator**
   - SMS/Email de verificação
   - Biometria

4. **Dashboard de Analytics**
   - Métricas de atendimento
   - Taxa de aprovação/rejeição

5. **Suporte a Mais Idiomas**
   - Inglês, Espanhol
   - Detecção automática


## 📞 Suporte

Para dúvidas ou sugestões:
- Consulte o desenvolvedor do projeto, Vinicius Borges
- E-mail - vinicius.borges.rio@gmail.com
- Linkedin - https://www.linkedin.com/in/viniciusmartinsrio

---

**Desenvolvido por "https://github.com/viniciusmartinsrio/" como solução para Desafio Técnico: Agente Bancário Inteligente com LLM**

**Versão**: 1.0 (com LangGraph e conversação natural)
**Última atualização**: Janeiro 2026
