# 🚀 Guia Rápido - Banco Ágil

## Instalação Rápida

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/banco-agil-agentes.git
cd banco-agil-agentes
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar a Aplicação

#### Opção A: Interface Streamlit (Recomendado)
```bash
streamlit run app.py
```
Acesse: `http://localhost:8501`

#### Opção B: Testes Automatizados
```bash
python3 test_sistema.py
```

## 📝 Dados de Teste

Use estes dados para testar o sistema:

| CPF | Data Nascimento | Nome | Limite | Score |
|-----|-----------------|------|--------|-------|
| 12345678901 | 1990-05-15 | João Silva | R$ 5.000 | 750 |
| 98765432109 | 1985-08-22 | Maria Santos | R$ 8.000 | 820 |
| 55555555555 | 1992-03-10 | Pedro Oliveira | R$ 3.000 | 650 |

## 🎯 Fluxos de Teste Recomendados

### Teste 1: Consultar Limite
1. CPF: `12345678901`
2. Data: `1990-05-15`
3. Opção: `1` (Consultar limite)

### Teste 2: Aumento Aprovado
1. CPF: `98765432109`
2. Data: `1985-08-22`
3. Opção: `2` (Solicitar aumento)
4. Novo limite: `10000` (será aprovado)

### Teste 3: Aumento Rejeitado + Entrevista
1. CPF: `55555555555`
2. Data: `1992-03-10`
3. Opção: `2` (Solicitar aumento)
4. Novo limite: `15000` (será rejeitado)
5. Aceitar entrevista: `sim`
6. Responder as 5 perguntas

### Teste 4: Consultar Câmbio
1. Autenticar com qualquer CPF válido
2. Opção: `4` (Consultar câmbio)
3. Moeda: deixar em branco para USD

## 📊 Estrutura de Arquivos

```
banco-agil-agentes/
├── agents/                    # Agentes de IA
│   ├── triagem_agent.py
│   ├── credito_agent.py
│   ├── entrevista_credito_agent.py
│   ├── cambio_agent.py
│   └── __init__.py
├── tools/                     # Ferramentas auxiliares
│   ├── data_manager.py
│   ├── score_calculator.py
│   ├── currency_fetcher.py
│   └── __init__.py
├── data/                      # Dados (CSV)
│   ├── clientes.csv
│   ├── score_limite.csv
│   └── solicitacoes_aumento_limite.csv
├── banco_agil_system.py       # Orquestrador central
├── app.py                     # Interface Streamlit
├── test_sistema.py            # Testes automatizados
├── requirements.txt           # Dependências
└── README.md                  # Documentação completa
```

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install streamlit
```

### Erro: "Arquivo CSV não encontrado"
Certifique-se de estar no diretório correto:
```bash
cd banco-agil-agentes
```

### API de Câmbio não funciona
A API é pública e não requer chave. Se não funcionar:
- Verifique sua conexão com a internet
- Tente novamente em alguns segundos

## 📚 Documentação Completa

Veja [README.md](README.md) para documentação detalhada sobre:
- Arquitetura do sistema
- Descrição de cada agente
- Fórmula de cálculo de score
- Extensões futuras
- Segurança e boas práticas

## 💡 Dicas

1. **Entrevista Financeira**: Para testar o cálculo de score, tente:
   - Renda: 5000
   - Emprego: formal
   - Despesas: 2000
   - Dependentes: 1
   - Dívidas: não
   - Resultado: Score ~780

2. **Múltiplas Moedas**: Teste com EUR, GBP, JPY, etc.

3. **Histórico**: O sidebar mostra informações do cliente autenticado

## ❓ Perguntas Frequentes

**P: Como adicionar novos clientes?**
R: Edite `data/clientes.csv` e adicione uma nova linha com os dados.

**P: Como mudar a fórmula de score?**
R: Edite `tools/score_calculator.py` e ajuste os pesos.

**P: Posso usar com um banco de dados?**
R: Sim, substitua `DataManager` por uma implementação com SQLAlchemy.

**P: Como integrar com um LLM?**
R: Use LangChain/LangGraph para processar linguagem natural dos usuários.

---

**Pronto para começar? Execute:**
```bash
streamlit run app.py
```
