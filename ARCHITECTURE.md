# 🏗️ Arquitetura do Sistema - Banco Ágil

## Visão Geral

O Banco Ágil é um sistema de atendimento bancário baseado em **arquitetura de agentes especializados**. Cada agente é responsável por um domínio específico do negócio e trabalha de forma integrada através de um orquestrador central.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFACE STREAMLIT                      │
│                    (app.py)                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ORQUESTRADOR CENTRAL                           │
│           (BancoAgilSystem)                                 │
│  - Gerencia estado da conversa                              │
│  - Roteia mensagens para agentes                            │
│  - Controla fluxo de atendimento                            │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┬─────────────────┐
        │                │                │                 │
        ▼                ▼                ▼                 ▼
    ┌────────┐      ┌──────────┐    ┌──────────────┐   ┌────────┐
    │TRIAGEM │      │ CRÉDITO  │    │ ENTREVISTA   │   │CÂMBIO  │
    │AGENT   │      │ AGENT    │    │ CRÉDITO AGENT│   │AGENT   │
    └────┬───┘      └────┬─────┘    └──────┬───────┘   └───┬────┘
         │               │                 │               │
         └───────────────┼─────────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐   ┌──────────┐
    │DATA     │    │SCORE     │   │CURRENCY  │
    │MANAGER  │    │CALCULATOR│   │FETCHER   │
    └────┬────┘    └──────────┘   └────┬─────┘
         │                             │
         ▼                             ▼
    ┌──────────────┐           ┌────────────────┐
    │CSV FILES     │           │API PÚBLICA     │
    │- clientes    │           │exchangerate-api│
    │- score_limite│           └────────────────┘
    │- solicitações│
    └──────────────┘
```

## Componentes Principais

### 1. Interface (app.py)

**Responsabilidade**: Fornecer interface de usuário para interação com o sistema.

**Características**:
- Construída com Streamlit
- Chat interativo
- Sidebar com informações do cliente
- Histórico de mensagens
- Botão para reiniciar conversa

**Fluxo**:
```
Usuário digita mensagem
        ↓
Streamlit captura entrada
        ↓
Envia para BancoAgilSystem.processar_entrada()
        ↓
Recebe resposta
        ↓
Exibe no chat
```

### 2. Orquestrador Central (BancoAgilSystem)

**Responsabilidade**: Gerenciar o fluxo de atendimento e rotear mensagens para agentes apropriados.

**Atributos**:
```python
class BancoAgilSystem:
    triagem: TriagemAgent          # Agente de triagem
    credito: CreditoAgent          # Agente de crédito
    entrevista: EntrevistaCreditoAgent  # Agente de entrevista
    cambio: CambioAgent            # Agente de câmbio
    
    cliente_autenticado: Dict      # Dados do cliente
    agente_ativo: str              # Agente em uso
    conversa_ativa: bool           # Status da conversa
    historico_mensagens: list      # Histórico
```

**Métodos Principais**:
- `iniciar_atendimento()`: Inicia o fluxo
- `processar_entrada(entrada)`: Roteia entrada para agente apropriado
- `_processar_triagem()`: Lida com autenticação
- `_processar_credito()`: Lida com operações de crédito
- `_processar_entrevista()`: Lida com entrevista financeira
- `_processar_cambio()`: Lida com consultas de câmbio

**Lógica de Roteamento**:
```
if not cliente_autenticado:
    → Processa triagem
elif agente_ativo is None:
    → Processa menu principal
elif agente_ativo == "credito":
    → Processa credito
elif agente_ativo == "entrevista_credito":
    → Processa entrevista
elif agente_ativo == "cambio":
    → Processa cambio
```

### 3. Agentes Especializados

#### 3.1 Agente de Triagem (TriagemAgent)

**Responsabilidade**: Autenticar cliente e direcionar para agente apropriado.

**Fluxo**:
```
1. Saudação inicial
2. Solicita CPF
3. Valida CPF (11 dígitos)
4. Solicita data de nascimento
5. Valida data (YYYY-MM-DD)
6. Busca cliente em clientes.csv
7. Se encontrado:
   - Armazena dados
   - Oferece menu de opções
8. Se não encontrado:
   - Permite até 3 tentativas
   - Encerra após 3 falhas
```

**Validações**:
- CPF: 11 dígitos, apenas números
- Data: Formato YYYY-MM-DD, valores válidos

**Métodos**:
- `saudacao_inicial()`: Mensagem de boas-vindas
- `solicitar_cpf()`: Pede CPF
- `solicitar_data_nascimento()`: Pede data
- `autenticar()`: Valida contra base de dados
- `identificar_assunto()`: Oferece menu de opções
- `direcionar_agente()`: Mapeia opção para agente

#### 3.2 Agente de Crédito (CreditoAgent)

**Responsabilidade**: Consultar limite e processar solicitações de aumento.

**Fluxo**:
```
1. Exibe limite atual e score
2. Pergunta se quer solicitar aumento
3. Se sim:
   a. Solicita novo limite
   b. Valida novo limite (> atual)
   c. Registra solicitação em CSV
   d. Verifica score contra tabela
   e. Se score permite:
      - Aprova
      - Atualiza status para "aprovado"
   f. Se score não permite:
      - Rejeita
      - Oferece entrevista
4. Se não:
   - Retorna ao menu
```

**Validações**:
- Novo limite > limite atual
- Novo limite ≤ limite máximo para score

**Métodos**:
- `consultar_limite()`: Exibe limite atual
- `solicitar_novo_limite()`: Pede novo valor
- `processar_solicitacao()`: Processa pedido
- `oferecer_entrevista()`: Oferece entrevista

#### 3.3 Agente de Entrevista de Crédito (EntrevistaCreditoAgent)

**Responsabilidade**: Coletar dados financeiros e recalcular score.

**Fluxo**:
```
1. Inicia entrevista
2. Pergunta 1: Renda mensal
3. Pergunta 2: Tipo de emprego (formal/autônomo/desempregado)
4. Pergunta 3: Despesas fixas mensais
5. Pergunta 4: Número de dependentes
6. Pergunta 5: Tem dívidas ativas? (sim/não)
7. Calcula novo score com ScoreCalculator
8. Atualiza score em clientes.csv
9. Redireciona para Agente de Crédito
```

**Validações**:
- Renda ≥ 0
- Despesas ≥ 0
- Dependentes ≥ 0
- Tipo emprego em lista válida
- Dívidas em (sim/não)

**Métodos**:
- `iniciar_entrevista()`: Inicia processo
- `_fazer_proxima_pergunta()`: Retorna próxima pergunta
- `processar_resposta()`: Valida e armazena resposta
- `_calcular_novo_score()`: Calcula e atualiza score

#### 3.4 Agente de Câmbio (CambioAgent)

**Responsabilidade**: Consultar cotações de moedas em tempo real.

**Fluxo**:
```
1. Solicita moeda
2. Se vazio: usa USD padrão
3. Busca cotação via CurrencyFetcher
4. Exibe taxa e exemplos de conversão
5. Oferece consultar outra moeda
6. Se sim: volta ao passo 1
7. Se não: retorna ao menu
```

**Métodos**:
- `solicitar_moeda()`: Pede código da moeda
- `consultar_cotacao()`: Busca cotação
- `calcular_conversao()`: Converte valor
- `encerrar_atendimento_cambio()`: Encerra

### 4. Ferramentas Auxiliares

#### 4.1 DataManager (tools/data_manager.py)

**Responsabilidade**: Gerenciar todas as operações com arquivos CSV.

**Métodos**:
- `authenticate_client(cpf, data_nascimento)`: Autentica cliente
- `get_client_by_cpf(cpf)`: Busca cliente
- `update_client_score(cpf, novo_score)`: Atualiza score
- `get_limit_by_score(score)`: Obtém limite máximo
- `register_limit_request(...)`: Registra solicitação
- `get_all_requests()`: Lista solicitações

**Operações com CSV**:
- Leitura: Usa `csv.DictReader`
- Escrita: Usa `csv.DictWriter`
- Atualização: Lê completo, modifica, escreve

#### 4.2 ScoreCalculator (tools/score_calculator.py)

**Responsabilidade**: Calcular score de crédito com fórmula ponderada.

**Fórmula**:
```
score = (
    (renda_mensal / (despesas + 1)) * peso_renda +
    peso_emprego[tipo_emprego] +
    peso_dependentes[num_dependentes] +
    peso_dividas[tem_dividas]
)
```

**Pesos**:
```python
peso_renda = 30
peso_emprego = {
    "formal": 300,
    "autônomo": 200,
    "desempregado": 0
}
peso_dependentes = {
    0: 100,
    1: 80,
    2: 60,
    "3+": 30
}
peso_dividas = {
    "sim": -100,
    "não": 100
}
```

**Métodos**:
- `calculate_score(...)`: Calcula score
- `get_score_interpretation(score)`: Interpreta score

#### 4.3 CurrencyFetcher (tools/currency_fetcher.py)

**Responsabilidade**: Buscar cotações de moedas em tempo real.

**API**: exchangerate-api.com (pública, sem autenticação)

**Métodos**:
- `get_exchange_rate(from, to)`: Busca taxa
- `get_supported_currencies()`: Lista moedas
- `format_exchange_info(data)`: Formata para exibição

## Fluxos de Dados

### Fluxo 1: Autenticação
```
Usuario: CPF
    ↓
TriagemAgent._validar_cpf()
    ↓
Usuario: Data Nascimento
    ↓
TriagemAgent._validar_data()
    ↓
DataManager.authenticate_client()
    ↓
Busca em clientes.csv
    ↓
Se encontrado: Armazena em cliente_autenticado
Se não: Permite nova tentativa (máx 3)
```

### Fluxo 2: Solicitação de Aumento
```
CreditoAgent.processar_solicitacao()
    ↓
Valida novo limite
    ↓
DataManager.register_limit_request()
    ↓
Registra em solicitacoes_aumento_limite.csv
    ↓
DataManager.get_limit_by_score()
    ↓
Busca em score_limite.csv
    ↓
Se score permite: Aprova
Se score não permite: Rejeita + Oferece entrevista
```

### Fluxo 3: Cálculo de Score
```
EntrevistaCreditoAgent.processar_resposta()
    ↓
Coleta 5 respostas
    ↓
ScoreCalculator.calculate_score()
    ↓
Aplica fórmula ponderada
    ↓
DataManager.update_client_score()
    ↓
Atualiza clientes.csv
    ↓
Redireciona para CreditoAgent
```

## Estrutura de Dados

### clientes.csv
```
cpf,data_nascimento,nome,limite_credito,score_credito
12345678901,1990-05-15,João Silva,5000.00,750
```

### score_limite.csv
```
score_minimo,score_maximo,limite_maximo
0,500,2000
501,600,5000
```

### solicitacoes_aumento_limite.csv
```
cpf_cliente,data_hora_solicitacao,limite_atual,novo_limite_solicitado,status_pedido
12345678901,2024-01-21T10:30:00.123456,5000.00,8000.00,aprovado
```

## Padrões de Design

### 1. Strategy Pattern
Cada agente implementa uma estratégia diferente de processamento.

### 2. State Pattern
O sistema mantém estado (cliente_autenticado, agente_ativo, conversa_ativa).

### 3. Chain of Responsibility
Mensagens são processadas através de uma cadeia de agentes.

### 4. Facade Pattern
BancoAgilSystem fornece interface simples para múltiplos agentes.

## Tratamento de Erros

### Validações em Múltiplas Camadas

1. **Camada de Entrada**: Validação básica de formato
2. **Camada de Agente**: Validação de negócio
3. **Camada de Ferramenta**: Validação de dados
4. **Camada de Persistência**: Tratamento de exceções de I/O

### Estratégia de Recuperação

- Erros de validação: Solicita nova entrada
- Erros de arquivo: Informa ao usuário
- Erros de API: Oferece alternativas
- Erros inesperados: Encerra com mensagem clara

## Extensibilidade

### Adicionar Novo Agente

1. Criar classe em `agents/novo_agent.py`
2. Implementar métodos de processamento
3. Adicionar em `agents/__init__.py`
4. Instanciar em `BancoAgilSystem.__init__()`
5. Adicionar roteamento em `processar_entrada()`

### Adicionar Nova Ferramenta

1. Criar classe em `tools/nova_ferramenta.py`
2. Implementar métodos necessários
3. Adicionar em `tools/__init__.py`
4. Usar em agentes

### Migrar para Banco de Dados

1. Criar `DataManagerDB` com SQLAlchemy
2. Implementar mesmos métodos de `DataManager`
3. Substituir em agentes

## Performance

### Otimizações Atuais

- CSV lido completo (adequado para dados pequenos)
- Sem cache (dados sempre atualizados)
- Sem índices (busca linear)

### Possíveis Melhorias

- Implementar cache em memória
- Usar banco de dados com índices
- Implementar busca assíncrona
- Adicionar paginação para grandes datasets

## Segurança

### Medidas Atuais

- Validação de entrada em múltiplas camadas
- Tratamento de exceções
- Isolamento de agentes

### Recomendações para Produção

- Criptografar dados sensíveis
- Implementar autenticação multi-fator
- Adicionar rate limiting
- Usar HTTPS
- Implementar auditoria completa
- Validar entrada com regex rigoroso

## Testes

### Cobertura Atual

- Teste 1: Consultar limite
- Teste 2: Aumento aprovado
- Teste 3: Aumento rejeitado + Entrevista
- Teste 4: Consultar câmbio
- Teste 5: Falha de autenticação

### Possíveis Testes Adicionais

- Testes unitários de cada agente
- Testes de integração
- Testes de carga
- Testes de segurança
- Testes de usabilidade

---

**Arquitetura versão 1.0**
Última atualização: 2024-01-21
