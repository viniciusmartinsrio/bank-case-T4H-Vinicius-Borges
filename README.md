# 🏦 Banco Ágil - Sistema de Atendimento Inteligente com Agentes de IA

Um sistema completo de atendimento bancário automatizado utilizando múltiplos agentes de IA especializados. Cada agente possui responsabilidades bem definidas e trabalha de forma integrada para oferecer uma experiência de atendimento fluida e eficiente.

## 📋 Visão Geral do Projeto

O Banco Ágil é uma solução de atendimento ao cliente para um banco digital fictício, implementada com uma arquitetura de múltiplos agentes. O sistema simula um atendimento bancário completo, desde a autenticação do cliente até operações complexas como solicitação de aumento de limite e cálculo de score de crédito.

### Características Principais

- ✅ **Autenticação Segura**: Validação de CPF e data de nascimento contra base de dados
- ✅ **Múltiplos Agentes Especializados**: Cada um com escopo bem definido
- ✅ **Cálculo Inteligente de Score**: Fórmula ponderada baseada em dados financeiros
- ✅ **Gerenciamento de Solicitações**: Registro e aprovação/rejeição de pedidos
- ✅ **Consulta de Câmbio**: Integração com API de cotações em tempo real
- ✅ **Interface Amigável**: Streamlit para testes e demonstração
- ✅ **Tratamento de Erros**: Validações robustas em todas as operações

## 🏗️ Arquitetura do Sistema

### Estrutura Geral

```
banco-agil-agentes/
├── agents/                          # Módulo de agentes
│   ├── triagem_agent.py            # Agente de triagem e autenticação
│   ├── credito_agent.py            # Agente de crédito
│   ├── entrevista_credito_agent.py # Agente de entrevista financeira
│   ├── cambio_agent.py             # Agente de câmbio
│   └── __init__.py
├── tools/                           # Módulo de ferramentas
│   ├── data_manager.py             # Gerenciador de CSV
│   ├── score_calculator.py         # Calculadora de score
│   ├── currency_fetcher.py         # Fetcher de cotações
│   └── __init__.py
├── data/                            # Dados (CSV)
│   ├── clientes.csv                # Base de clientes
│   ├── score_limite.csv            # Tabela score x limite
│   └── solicitacoes_aumento_limite.csv # Registro de solicitações
├── banco_agil_system.py            # Orquestrador central
├── app.py                          # Interface Streamlit
└── README.md                       # Este arquivo
```

### Fluxo de Atendimento

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENTE INICIA CONTATO                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  AGENTE DE TRIAGEM   │
                  │  - Saudação          │
                  │  - Coleta CPF        │
                  │  - Coleta Data Nasc. │
                  │  - Autentica         │
                  └──────────┬───────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
        ┌───────────▼────────┐   ┌────▼──────────────┐
        │ AUTENTICADO?       │   │ FALHA 3x?         │
        │ SIM / NÃO          │   │ ENCERRA           │
        └───────────┬────────┘   └───────────────────┘
                    │
        ┌───────────▼────────────────────┐
        │ IDENTIFICAR ASSUNTO            │
        │ 1. Consultar limite            │
        │ 2. Solicitar aumento           │
        │ 3. Entrevista financeira       │
        │ 4. Consultar câmbio            │
        │ 5. Encerrar                    │
        └───────────┬────────────────────┘
                    │
        ┌───────────┴──────────────────────────────────┐
        │                                              │
        ▼                                              ▼
┌──────────────────────┐                    ┌──────────────────────┐
│ AGENTE DE CRÉDITO    │                    │ AGENTE DE CÂMBIO     │
│ - Consulta limite    │                    │ - Solicita moeda     │
│ - Processa pedido    │                    │ - Busca cotação      │
│ - Valida score       │                    │ - Apresenta taxa     │
│ - Aprova/Rejeita     │                    │ - Oferece conversão  │
└──────────┬───────────┘                    └──────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────────────────────┐
│APROVADO │  │ REJEITADO + OFERECER     │
│ENCERRA  │  │ ENTREVISTA FINANCEIRA    │
└─────────┘  └──────────┬───────────────┘
                        │
                        ▼
             ┌──────────────────────────┐
             │ AGENTE DE ENTREVISTA     │
             │ - Coleta renda           │
             │ - Tipo emprego           │
             │ - Despesas fixas         │
             │ - Dependentes            │
             │ - Dívidas ativas         │
             │ - Calcula novo score     │
             │ - Atualiza BD            │
             │ - Redireciona p/ Crédito │
             └──────────────────────────┘
```

### Agentes Especializados

#### 1. **Agente de Triagem** (`TriagemAgent`)
- **Responsabilidade**: Porta de entrada do atendimento
- **Funcionalidades**:
  - Saudação inicial
  - Coleta de CPF e data de nascimento
  - Validação contra `clientes.csv`
  - Permite até 3 tentativas de autenticação
  - Direcionamento para agente apropriado
- **Arquivo**: `agents/triagem_agent.py`

#### 2. **Agente de Crédito** (`CreditoAgent`)
- **Responsabilidade**: Operações de crédito
- **Funcionalidades**:
  - Consulta de limite de crédito atual
  - Processamento de solicitação de aumento
  - Validação contra tabela `score_limite.csv`
  - Aprovação automática se score permite
  - Rejeição com oferta de entrevista se necessário
  - Registro em `solicitacoes_aumento_limite.csv`
- **Arquivo**: `agents/credito_agent.py`

#### 3. **Agente de Entrevista de Crédito** (`EntrevistaCreditoAgent`)
- **Responsabilidade**: Cálculo de score de crédito
- **Funcionalidades**:
  - Entrevista estruturada com 5 perguntas
  - Coleta de dados financeiros
  - Cálculo de novo score usando fórmula ponderada
  - Atualização de score em `clientes.csv`
  - Redirecionamento para Agente de Crédito
- **Arquivo**: `agents/entrevista_credito_agent.py`

#### 4. **Agente de Câmbio** (`CambioAgent`)
- **Responsabilidade**: Consultas de câmbio
- **Funcionalidades**:
  - Busca cotação em tempo real via API
  - Suporta múltiplas moedas
  - Cálculo de conversão
  - Apresentação formatada de taxas
- **Arquivo**: `agents/cambio_agent.py`

### Ferramentas Auxiliares

#### 1. **DataManager** (`tools/data_manager.py`)
Gerencia todas as operações com arquivos CSV:
- `authenticate_client()`: Autentica cliente
- `get_client_by_cpf()`: Busca cliente por CPF
- `update_client_score()`: Atualiza score
- `get_limit_by_score()`: Obtém limite máximo por score
- `register_limit_request()`: Registra solicitação
- `get_all_requests()`: Lista todas as solicitações

#### 2. **ScoreCalculator** (`tools/score_calculator.py`)
Implementa a fórmula de cálculo de score:

```
score = (
    (renda_mensal / (despesas + 1)) * peso_renda +
    peso_emprego[tipo_emprego] +
    peso_dependentes[num_dependentes] +
    peso_dividas[tem_dividas]
)
```

**Pesos utilizados:**
- `peso_renda`: 30
- `peso_emprego`: formal=300, autônomo=200, desempregado=0
- `peso_dependentes`: 0=100, 1=80, 2=60, 3+=30
- `peso_dividas`: sim=-100, não=100

#### 3. **CurrencyFetcher** (`tools/currency_fetcher.py`)
Busca cotações de moedas:
- Integração com API pública `exchangerate-api.com`
- Sem necessidade de autenticação
- Suporta todas as moedas principais

### Orquestrador Central

**`BancoAgilSystem`** (`banco_agil_system.py`):
- Gerencia todos os agentes
- Mantém estado da conversa
- Roteia mensagens para agente apropriado
- Controla fluxo de atendimento
- Mantém histórico de mensagens

## 🗄️ Estrutura de Dados

### `data/clientes.csv`
Base de dados de clientes para autenticação:

```csv
cpf,data_nascimento,nome,limite_credito,score_credito
12345678901,1990-05-15,João Silva,5000.00,750
98765432109,1985-08-22,Maria Santos,8000.00,820
...
```

### `data/score_limite.csv`
Tabela de relação entre score e limite máximo:

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
Registro de todas as solicitações de aumento:

```csv
cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido
12345678901,2024-01-21T10:30:00.123456,5000.00,8000.00,aprovado
98765432109,2024-01-21T11:15:00.654321,8000.00,15000.00,rejeitado
...
```

## ✨ Funcionalidades Implementadas

### 1. Autenticação de Cliente
- Validação de CPF (11 dígitos, sem repetição)
- Validação de data de nascimento (formato YYYY-MM-DD)
- Busca em base de dados
- Até 3 tentativas permitidas
- Encerramento após falhas consecutivas

### 2. Consulta de Limite de Crédito
- Exibição do limite atual
- Exibição do score de crédito
- Opção de solicitar aumento

### 3. Solicitação de Aumento de Limite
- Validação de novo limite (deve ser maior que atual)
- Verificação contra tabela de score x limite
- Aprovação automática se score permite
- Rejeição com oferta de entrevista se necessário
- Registro em arquivo CSV com timestamp ISO 8601

### 4. Entrevista Financeira
- 5 perguntas estruturadas
- Coleta de renda mensal
- Tipo de emprego (formal, autônomo, desempregado)
- Despesas fixas mensais
- Número de dependentes
- Existência de dívidas ativas
- Cálculo de novo score com fórmula ponderada
- Atualização automática em base de dados

### 5. Consulta de Câmbio
- Busca de cotação em tempo real
- Suporte a múltiplas moedas
- Cálculo de conversão
- Tratamento de erros de conectividade

### 6. Tratamento de Erros
- Validação de entrada do usuário
- Mensagens de erro claras
- Recuperação de falhas
- Logging de operações

## 🚀 Como Executar

### Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

### Instalação de Dependências

```bash
pip install langgraph langchain langchain-core python-dotenv pandas requests streamlit
```

Ou usando o arquivo de requisitos (se disponível):

```bash
pip install -r requirements.txt
```

### Execução da Aplicação

#### Opção 1: Interface Streamlit (Recomendado)

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

#### Opção 2: Teste em Linha de Comando

```bash
python3 -c "
from banco_agil_system import BancoAgilSystem

sistema = BancoAgilSystem()
print(sistema.iniciar_atendimento())

# Simula entrada do usuário
entrada = input('> ')
resposta = sistema.processar_entrada(entrada)
print(resposta)
"
```

### Dados de Teste

Use os seguintes dados para testar autenticação:

| CPF | Data Nascimento | Nome |
|-----|-----------------|------|
| 12345678901 | 1990-05-15 | João Silva |
| 98765432109 | 1985-08-22 | Maria Santos |
| 55555555555 | 1992-03-10 | Pedro Oliveira |

## 🧪 Testes e Fluxos

### Fluxo 1: Consultar Limite de Crédito
1. Iniciar atendimento
2. Fornecer CPF: `12345678901`
3. Fornecer data: `1990-05-15`
4. Escolher opção: `1` (Consultar limite)
5. Visualizar limite atual

### Fluxo 2: Solicitar Aumento Aprovado
1. Autenticar com `98765432109` / `1985-08-22` (score 820)
2. Escolher opção: `2` (Solicitar aumento)
3. Solicitar novo limite: `10000` (permitido para score 820)
4. Receber aprovação

### Fluxo 3: Solicitar Aumento Rejeitado + Entrevista
1. Autenticar com `55555555555` / `1992-03-10` (score 650)
2. Escolher opção: `2` (Solicitar aumento)
3. Solicitar novo limite: `15000` (não permitido para score 650)
4. Receber rejeição
5. Aceitar entrevista financeira
6. Responder perguntas (exemplo: renda 5000, formal, despesas 2000, 1 dependente, sem dívidas)
7. Novo score calculado (aproximadamente 780)
8. Retornar ao Agente de Crédito para nova análise

### Fluxo 4: Consultar Câmbio
1. Autenticar
2. Escolher opção: `4` (Consultar câmbio)
3. Fornecer moeda: `USD` (ou deixar em branco para padrão)
4. Visualizar cotação USD/BRL
5. Optar por consultar outra moeda

## 🎯 Desafios Enfrentados e Soluções

### 1. **Validação de CPF**
**Desafio**: Validar CPF de forma simples sem algoritmo complexo
**Solução**: Implementar validação básica (11 dígitos, sem repetição) que é suficiente para o caso de uso

### 2. **Fluxo de Redirecionamento Implícito**
**Desafio**: Redirecionar entre agentes sem o cliente perceber a transição
**Solução**: Implementar orquestrador central que gerencia transições de forma transparente

### 3. **Cálculo de Score Ponderado**
**Desafio**: Implementar fórmula que normaliza diferentes escalas de entrada
**Solução**: Usar fórmula ponderada com normalização para escala 0-1000

### 4. **Persistência de Dados**
**Desafio**: Manter dados consistentes entre execuções
**Solução**: Usar CSV com operações ACID simples (leitura completa, modificação, escrita)

### 5. **Tratamento de Erros de API**
**Desafio**: Lidar com indisponibilidade de API de câmbio
**Solução**: Implementar try-catch com mensagens amigáveis ao usuário

## 🔧 Escolhas Técnicas e Justificativas

### 1. **Python como Linguagem Principal**
- Excelente para prototipagem rápida
- Bibliotecas maduras para manipulação de dados (pandas, csv)
- Suporte nativo para integração com LLMs

### 2. **CSV para Armazenamento de Dados**
- Simplicidade de implementação
- Fácil visualização e edição manual
- Suficiente para escopo do desafio
- Pode ser facilmente migrado para banco de dados relacional

### 3. **Streamlit para Interface**
- Desenvolvimento rápido de UI
- Excelente para demonstrações
- Suporte nativo para chat
- Ideal para prototipagem

### 4. **Arquitetura de Agentes Especializados**
- Separação clara de responsabilidades
- Fácil manutenção e extensão
- Simula comportamento de equipe humana
- Escalável para novos agentes

### 5. **API Pública para Câmbio**
- Sem necessidade de autenticação
- Dados em tempo real
- Confiável e gratuita

## 📈 Possíveis Extensões

1. **Integração com LLM**
   - Usar LangChain para processamento de linguagem natural
   - Melhorar compreensão de intenção do usuário

2. **Banco de Dados Relacional**
   - Migrar de CSV para PostgreSQL/MySQL
   - Melhorar performance e segurança

3. **Autenticação Biométrica**
   - Adicionar validação de face/digital
   - Aumentar segurança

4. **Histórico de Transações**
   - Registrar todas as operações
   - Auditoria completa

5. **Recomendações Personalizadas**
   - Sugerir produtos baseado em perfil
   - Aumentar satisfação do cliente

6. **Integração com Sistemas Externos**
   - Conectar com sistemas de pagamento
   - Integrar com redes de ATM

## 📝 Estrutura de Código

### Padrões Utilizados

1. **Class-based Architecture**: Cada agente é uma classe com métodos bem definidos
2. **Separation of Concerns**: Ferramentas separadas de agentes
3. **Single Responsibility**: Cada classe tem uma responsabilidade clara
4. **Error Handling**: Validações em múltiplas camadas

### Convenções de Código

- Nomes descritivos em português (domínio do negócio)
- Type hints em todas as funções
- Docstrings em formato Google
- Comentários explicativos para lógica complexa

## 🔐 Segurança

### Medidas Implementadas

1. **Validação de Entrada**: Todas as entradas são validadas
2. **Tratamento de Exceções**: Erros são capturados e tratados
3. **Isolamento de Agentes**: Cada agente trabalha com dados específicos
4. **Auditoria**: Todas as solicitações são registradas

### Recomendações para Produção

1. Usar HTTPS para comunicação
2. Implementar autenticação multi-fator
3. Criptografar dados sensíveis
4. Usar banco de dados com controle de acesso
5. Implementar rate limiting
6. Adicionar logging centralizado

## 📞 Suporte e Contato

Para dúvidas ou sugestões sobre o sistema, consulte a documentação ou abra uma issue no repositório.

## 📄 Licença

Este projeto é fornecido como solução para desafio técnico.

---

**Desenvolvido como solução para Desafio Técnico: Agente Bancário Inteligente**
