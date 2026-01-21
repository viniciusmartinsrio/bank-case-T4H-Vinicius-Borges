# Banco Ágil - Documentação Claude Code

## Visão Geral do Projeto

Este é um sistema de atendimento bancário inteligente desenvolvido em Python, utilizando uma arquitetura de múltiplos agentes especializados. O projeto simula um atendimento completo de banco digital, desde autenticação até operações financeiras complexas.

**Propósito:** Demonstrar implementação de sistema multi-agente para atendimento bancário automatizado.

**Tecnologias Principais:**
- Python 3.8+
- Streamlit (interface web)
- LangGraph/LangChain (orquestração de agentes)
- CSV para persistência de dados
- APIs públicas (cotações de câmbio)

## Estrutura do Projeto

```
bank-case-T4H-Vinicius-Borges/
├── agents/                          # Agentes especializados
│   ├── __init__.py
│   ├── triagem_agent.py            # Autenticação e roteamento
│   ├── credito_agent.py            # Operações de crédito
│   ├── entrevista_credito_agent.py # Cálculo de score
│   └── cambio_agent.py             # Consulta de câmbio
├── tools/                           # Ferramentas auxiliares
│   ├── __init__.py
│   ├── data_manager.py             # Gerenciamento de CSV
│   ├── score_calculator.py         # Fórmula de score
│   └── currency_fetcher.py         # API de cotações
├── data/                            # Arquivos de dados
│   ├── clientes.csv                # Base de clientes
│   ├── score_limite.csv            # Tabela score x limite
│   └── solicitacoes_aumento_limite.csv # Histórico de solicitações
├── banco_agil_system.py            # Orquestrador central
├── app.py                          # Interface Streamlit
├── test_sistema.py                 # Testes
├── requirements.txt                # Dependências
├── config.toml                     # Configurações
├── README.md                       # Documentação principal
├── ARCHITECTURE.md                 # Arquitetura detalhada
├── QUICKSTART.md                   # Guia rápido
└── claude.md                       # Este arquivo
```

## Arquitetura de Agentes

### 1. TriagemAgent (triagem_agent.py)
**Responsabilidade:** Porta de entrada do sistema
**Funcionalidades:**
- Saudação inicial e coleta de dados
- Validação de CPF (11 dígitos)
- Validação de data de nascimento (YYYY-MM-DD)
- Autenticação contra base de dados
- Até 3 tentativas de login
- Roteamento para agentes especializados

**Métodos Principais:**
- `saudacao_inicial()`: Mensagem de boas-vindas
- `solicitar_cpf()`: Coleta CPF
- `solicitar_data_nascimento()`: Coleta data
- `autenticar(cpf, data)`: Valida credenciais
- `identificar_assunto()`: Menu de opções
- `direcionar_agente(opcao)`: Mapeia opção para agente

### 2. CreditoAgent (credito_agent.py)
**Responsabilidade:** Gestão de limite de crédito
**Funcionalidades:**
- Consulta limite e score atual
- Processa solicitações de aumento
- Valida contra tabela score_limite.csv
- Aprova/rejeita automaticamente
- Oferece entrevista se rejeitado
- Registra todas as solicitações

**Métodos Principais:**
- `consultar_limite()`: Exibe informações de crédito
- `solicitar_novo_limite()`: Pede novo valor
- `processar_solicitacao(valor)`: Analisa e decide
- `oferecer_entrevista()`: Oferece recálculo de score

### 3. EntrevistaCreditoAgent (entrevista_credito_agent.py)
**Responsabilidade:** Recálculo de score de crédito
**Funcionalidades:**
- Entrevista estruturada com 5 perguntas
- Coleta dados financeiros (renda, despesas, etc.)
- Calcula novo score usando ScoreCalculator
- Atualiza score em clientes.csv
- Redireciona para CreditoAgent

**Perguntas da Entrevista:**
1. Renda mensal (R$)
2. Tipo de emprego (formal/autônomo/desempregado)
3. Despesas fixas mensais (R$)
4. Número de dependentes
5. Tem dívidas ativas? (sim/não)

### 4. CambioAgent (cambio_agent.py)
**Responsabilidade:** Consultas de câmbio
**Funcionalidades:**
- Busca cotações em tempo real
- Suporta múltiplas moedas (USD, EUR, etc.)
- Calcula conversões
- Tratamento de erros de API

## Ferramentas Auxiliares

### DataManager (data_manager.py)
Gerencia todas as operações com CSV:
- `authenticate_client(cpf, data)`: Autentica usuário
- `get_client_by_cpf(cpf)`: Busca dados do cliente
- `update_client_score(cpf, score)`: Atualiza score
- `get_limit_by_score(score)`: Retorna limite máximo
- `register_limit_request(...)`: Registra solicitação
- `get_all_requests()`: Lista todas as solicitações

### ScoreCalculator (score_calculator.py)
Implementa fórmula de cálculo de score:

```python
score = (
    (renda_mensal / (despesas + 1)) * 30 +
    peso_emprego[tipo] +
    peso_dependentes[num] +
    peso_dividas[tem_dividas]
)
```

**Pesos:**
- Renda: 30
- Emprego: formal=300, autônomo=200, desempregado=0
- Dependentes: 0=100, 1=80, 2=60, 3+=30
- Dívidas: sim=-100, não=100

### CurrencyFetcher (currency_fetcher.py)
Integração com API exchangerate-api.com:
- Busca cotações em tempo real
- Sem necessidade de autenticação
- Suporte a todas as moedas principais

## Orquestrador Central

### BancoAgilSystem (banco_agil_system.py)
Gerencia todo o fluxo de atendimento:
- Instancia todos os agentes
- Mantém estado da conversa
- Roteia mensagens para agente apropriado
- Controla autenticação e sessão
- Mantém histórico de mensagens

**Atributos de Estado:**
- `cliente_autenticado`: Dados do cliente logado
- `agente_ativo`: Agente atualmente em uso
- `conversa_ativa`: Flag de sessão ativa
- `historico_mensagens`: Lista de mensagens trocadas

**Fluxo de Roteamento:**
1. Cliente não autenticado → TriagemAgent
2. Cliente autenticado sem agente → Menu principal
3. Opção selecionada → Agente específico

## Estrutura de Dados

### clientes.csv
```csv
cpf,data_nascimento,nome,limite_credito,score_credito
12345678901,1990-05-15,João Silva,5000.00,750
98765432109,1985-08-22,Maria Santos,8000.00,820
55555555555,1992-03-10,Pedro Oliveira,10000.00,650
```

### score_limite.csv
Tabela de mapeamento score → limite máximo:
```csv
score_minimo,score_maximo,limite_maximo
0,500,2000
501,600,5000
601,700,10000
701,800,15000
801,900,25000
901,1000,50000
```

### solicitacoes_aumento_limite.csv
Histórico de todas as solicitações:
```csv
cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido
12345678901,2024-01-21T10:30:00.123456,5000.00,8000.00,aprovado
```

## Como Executar

### Instalação de Dependências
```bash
pip install -r requirements.txt
```

### Iniciar Aplicação Web
```bash
streamlit run app.py
```
Abre em: http://localhost:8501

### Dados de Teste
| CPF | Data Nascimento | Nome | Score | Limite |
|-----|-----------------|------|-------|--------|
| 12345678901 | 1990-05-15 | João Silva | 750 | 5000 |
| 98765432109 | 1985-08-22 | Maria Santos | 820 | 8000 |
| 55555555555 | 1992-03-10 | Pedro Oliveira | 650 | 10000 |

## Fluxos de Uso Comuns

### Fluxo 1: Consulta de Limite
1. Iniciar atendimento
2. Fornecer CPF e data de nascimento
3. Escolher opção 1 (Consultar limite)
4. Visualizar informações
5. Voltar ao menu ou encerrar

### Fluxo 2: Solicitar Aumento (Aprovado)
1. Autenticar com score alto (ex: 820)
2. Escolher opção 2 (Solicitar aumento)
3. Informar novo limite dentro do permitido
4. Receber aprovação automática

### Fluxo 3: Solicitar Aumento (Rejeitado) + Entrevista
1. Autenticar com score médio (ex: 650)
2. Escolher opção 2 (Solicitar aumento)
3. Informar limite acima do permitido
4. Receber rejeição
5. Aceitar entrevista financeira
6. Responder 5 perguntas
7. Novo score é calculado
8. Retornar automaticamente ao CreditoAgent
9. Tentar novamente a solicitação

### Fluxo 4: Consulta de Câmbio
1. Autenticar
2. Escolher opção 4 (Consultar câmbio)
3. Informar código da moeda (ex: USD)
4. Visualizar cotação atual
5. Optar por consultar outra moeda ou voltar

## Padrões de Design Utilizados

1. **Strategy Pattern**: Cada agente implementa estratégia específica
2. **State Pattern**: Sistema mantém estado da conversa
3. **Chain of Responsibility**: Mensagens processadas em cadeia
4. **Facade Pattern**: BancoAgilSystem simplifica interface

## Validações e Segurança

### Validações Implementadas
- CPF: 11 dígitos, apenas números
- Data: Formato YYYY-MM-DD, valores válidos
- Valores monetários: Positivos e realistas
- Score: Escala 0-1000
- Status de solicitação: Enum controlado

### Tratamento de Erros
- Validação em múltiplas camadas
- Mensagens de erro claras ao usuário
- Recuperação de falhas sem crash
- Limite de 3 tentativas de autenticação

## Extensibilidade

### Adicionar Novo Agente
1. Criar arquivo em `agents/novo_agent.py`
2. Implementar classe com métodos necessários
3. Adicionar em `agents/__init__.py`
4. Instanciar em `BancoAgilSystem.__init__()`
5. Adicionar lógica de roteamento em `processar_entrada()`
6. Adicionar opção no menu do TriagemAgent

### Adicionar Nova Ferramenta
1. Criar arquivo em `tools/nova_ferramenta.py`
2. Implementar métodos estáticos
3. Adicionar em `tools/__init__.py`
4. Usar nos agentes necessários

### Migrar para Banco de Dados
1. Criar classe `DataManagerDB` usando SQLAlchemy
2. Implementar mesma interface de `DataManager`
3. Substituir import nos agentes
4. Configurar connection string em `config.toml`

## Testes

### Executar Suite de Testes
```bash
python test_sistema.py
```

### Testes Cobertos
1. Autenticação válida e inválida
2. Consulta de limite
3. Solicitação aprovada
4. Solicitação rejeitada
5. Entrevista financeira
6. Cálculo de score
7. Consulta de câmbio

## Performance

### Otimizações Atuais
- Leitura completa de CSV (adequado para dados pequenos)
- Sem cache (dados sempre atualizados)
- Busca linear em arquivos

### Melhorias Futuras Possíveis
- Implementar cache em memória para dados estáticos
- Migrar para banco de dados relacional com índices
- Adicionar paginação para datasets grandes
- Implementar busca assíncrona para APIs externas

## Troubleshooting

### Problema: Arquivo CSV não encontrado
**Solução:** Verificar se a pasta `data/` existe e contém os 3 arquivos CSV necessários.

### Problema: Erro ao buscar cotação de câmbio
**Solução:** Verificar conexão com internet. A API exchangerate-api.com pode estar temporariamente indisponível.

### Problema: Score calculado incorreto
**Solução:** Verificar se os pesos no `ScoreCalculator` estão corretos e se todas as 5 perguntas foram respondidas.

### Problema: Autenticação falha com dados corretos
**Solução:** Verificar formato da data (deve ser YYYY-MM-DD) e CPF (11 dígitos sem pontuação).

## Informações de Desenvolvimento

### Dependências Principais
```
langgraph>=0.0.1      # Orquestração de agentes
langchain>=0.1.0      # Framework LLM
langchain-core>=0.1.0 # Core do LangChain
python-dotenv>=1.0.0  # Variáveis de ambiente
pandas>=2.0.0         # Manipulação de dados
requests>=2.31.0      # Requisições HTTP
streamlit>=1.28.0     # Interface web
```

### Configurações (config.toml)
- Configurações do Streamlit
- Temas e aparência
- Porta do servidor (padrão: 8501)

## Contato e Suporte

Para dúvidas sobre este projeto, consulte:
- README.md (visão geral)
- ARCHITECTURE.md (arquitetura detalhada)
- QUICKSTART.md (guia rápido de início)
- Este arquivo (documentação Claude)

## Changelog

### v1.0 - Versão Inicial
- Implementação de 4 agentes especializados
- Sistema de autenticação
- Cálculo de score ponderado
- Interface Streamlit
- Integração com API de câmbio
- Persistência em CSV

---

**Última atualização:** 2026-01-21
**Desenvolvido como solução para:** Desafio Técnico - Agentes de IA para Banco Ágil
