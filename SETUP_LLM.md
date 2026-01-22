# Configuração e Uso do Sistema com LLM

Este documento explica como configurar e testar o **Banco Ágil** com integração LLM completa usando LangGraph + Groq API.

## 📋 Pré-requisitos

- Python 3.8+
- Conta na Groq Cloud (gratuita)
- Dependências instaladas (`pip install -r requirements.txt`)

## 🔑 Passo 1: Obter API Key do Groq

1. Acesse [https://console.groq.com](https://console.groq.com)
2. Faça login ou crie uma conta gratuita
3. Navegue até **API Keys**
4. Clique em **Create API Key**
5. Copie a chave gerada (ela começa com `gsk_...`)

## ⚙️ Passo 2: Configurar API Key

### Opção A: Arquivo .env (Recomendado)

1. Abra o arquivo `.env` na raiz do projeto
2. Adicione sua chave:
   ```
   GROQ_API_KEY=gsk_sua_chave_aqui
   ```
3. Salve o arquivo

### Opção B: Variável de Ambiente

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="gsk_sua_chave_aqui"
```

**Linux/Mac:**
```bash
export GROQ_API_KEY="gsk_sua_chave_aqui"
```

## 🧪 Passo 3: Testar a Integração

### Teste 1: Orquestrador LangGraph

```bash
python banco_agil_langgraph.py
```

**Resultado esperado:**
- Sistema inicializa sem erros
- LLM responde com saudação inicial
- Teste de conversação é executado

### Teste 2: Agentes Individuais

#### Agente de Triagem:
```bash
python agents/triagem_agent_llm.py
```

#### Agente de Crédito:
```bash
python agents/credito_agent_llm.py
```

#### Agente de Entrevista:
```bash
python agents/entrevista_credito_agent_llm.py
```

#### Agente de Câmbio:
```bash
python agents/cambio_agent_llm.py
```

### Teste 3: Interface Web com Streamlit

```bash
streamlit run app_llm.py
```

Acesse `http://localhost:8501` no navegador.

## 🎭 Fluxo de Conversação Completo

### Exemplo de Teste Ponta a Ponta:

1. **Saudação:**
   - Usuário: "Olá!"
   - Sistema: Saudação + solicitação de CPF

2. **Autenticação:**
   - Usuário: "12345678901"
   - Sistema: Solicita data de nascimento
   - Usuário: "1990-05-15"
   - Sistema: Autentica + apresenta menu

3. **Consulta de Crédito:**
   - Usuário: "Quero aumentar meu limite"
   - Sistema: Informa limite atual
   - Usuário: "Quero R$ 8000"
   - Sistema: Aprova ou rejeita baseado no score

4. **Entrevista (se rejeitado):**
   - Sistema: Oferece entrevista financeira
   - Usuário: "Sim, aceito"
   - Sistema: Faz 5 perguntas estruturadas
   - Sistema: Recalcula score

5. **Câmbio:**
   - Usuário: "Quanto está o dólar?"
   - Sistema: Retorna cotação em tempo real

6. **Encerramento:**
   - Usuário: "Encerrar"
   - Sistema: Finaliza atendimento

## 📊 Dados de Teste

### Cliente Exemplo no Banco de Dados:

```
CPF: 12345678901
Data de Nascimento: 1990-05-15
Nome: João Silva
Limite Atual: R$ 5.000,00
Score: 750
```

## 🔧 Arquitetura do Sistema

### Componentes Principais:

```
banco_agil_langgraph.py          # Orquestrador LangGraph
├── agents/
│   ├── base_agent.py            # Classe base com LLM
│   ├── triagem_agent_llm.py     # Autenticação
│   ├── credito_agent_llm.py     # Crédito
│   ├── entrevista_credito_agent_llm.py  # Entrevista
│   └── cambio_agent_llm.py      # Câmbio
├── tools/
│   └── agent_tools.py           # LangChain Tools
├── prompts/
│   └── agent_prompts.py         # System Prompts
├── state.py                     # Estado compartilhado
└── llm_config.py                # Configurações LLM
```

### Fluxo de Estados (LangGraph):

```
[triagem] → (autenticado?) → [menu]
              ↓
    ┌─────────┴─────────┬──────────────┬────────────┐
    ↓                   ↓              ↓            ↓
[crédito]       [entrevista]      [câmbio]    [encerramento]
    ↓                   ↓              ↓            ↓
    └───────────────────┴──────────────┴────────→ [END]
```

## 🎯 Parâmetros LLM por Agente

| Agente | Modelo | Temperature | Top-P | Max Tokens | Característica |
|--------|--------|-------------|-------|------------|----------------|
| Triagem | Llama 3.1 70B | 0.3 | 0.9 | 200 | Preciso, protocolar |
| Crédito | Llama 3.1 70B | 0.4 | 0.85 | 250 | Empático, claro |
| Entrevista | Llama 3.1 70B | 0.7 | 0.95 | 300 | Natural, conversacional |
| Câmbio | Llama 3.1 70B | 0.2 | 0.8 | 150 | Factual, conciso |

## ⚠️ Troubleshooting

### Erro: "GROQ_API_KEY não encontrada"
- Verifique se o arquivo `.env` contém a chave
- Verifique se a chave está no formato `gsk_...`
- Tente reiniciar o terminal

### Erro: "Rate limit exceeded"
- Aguarde 1 minuto e tente novamente
- A tier gratuita do Groq tem limites de requisições

### Erro: "Model not found"
- Verifique se o modelo `llama-3.1-70b-versatile` está disponível
- Consulte documentação do Groq para modelos atualizados

### Interface Streamlit não carrega:
- Verifique se GROQ_API_KEY está configurada
- Execute `streamlit run app_llm.py` (não `app.py`)

## 🚀 Próximos Passos

Após validar que tudo funciona:

1. ✅ **Fase 1 Completa**: LLM Integration
2. ⏳ **Fase 2**: Refinar prompts baseado em testes
3. ⏳ **Fase 3**: Adicionar mais ferramentas (histórico, relatórios)
4. ⏳ **Fase 4**: Implementar persistência de conversação
5. ⏳ **Fase 5**: Deploy em produção

## 📝 Notas Importantes

- **Custo**: Groq oferece tier gratuito generoso
- **Latência**: Groq é extremamente rápido (~200ms por resposta)
- **Privacidade**: Dados de teste são fictícios
- **Produção**: Para produção, implemente rate limiting e caching

## 📚 Referências

- [Groq Documentation](https://console.groq.com/docs)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)

---

**Desenvolvido para o Desafio Técnico de Agentes de IA**
