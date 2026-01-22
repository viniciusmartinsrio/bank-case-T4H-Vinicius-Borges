# Guia de Teste Rápido - Sistema com LLM

Este guia fornece um roteiro rápido para testar o sistema Banco Ágil com LLM.

## ⚡ Setup Rápido (2 minutos)

### 1. Obter API Key
1. Acesse: https://console.groq.com
2. Faça login (ou crie conta gratuita)
3. Vá em "API Keys" → "Create API Key"
4. Copie a chave (começa com `gsk_`)

### 2. Configurar
```bash
# Abra o arquivo .env e cole sua chave:
GROQ_API_KEY=gsk_sua_chave_aqui
```

### 3. Testar
```bash
# Terminal 1: Teste básico
python banco_agil_langgraph.py

# Terminal 2: Interface web
streamlit run app_llm.py
```

---

## 🎬 Roteiro de Teste Completo

### Cenário 1: Autenticação + Consulta de Crédito ✅

**Objetivo:** Testar fluxo básico de autenticação e consulta

```
👤 Usuário: "Olá!"
🤖 Sistema: [Saudação + solicita CPF]

👤 Usuário: "12345678901"
🤖 Sistema: [Solicita data de nascimento]

👤 Usuário: "15/05/1990"
🤖 Sistema: [Autentica + apresenta menu]

👤 Usuário: "Quero consultar meu limite"
🤖 Sistema: [Informa limite atual de R$ 5.000]

👤 Usuário: "Quero aumentar para 7000"
🤖 Sistema: [Aprova automaticamente - score 750 permite]

👤 Usuário: "Encerrar"
🤖 Sistema: [Despedida]
```

**Resultado esperado:** ✅ Aprovação automática (score 750 > 700)

---

### Cenário 2: Rejeição + Entrevista + Re-análise ✅

**Objetivo:** Testar fluxo completo com recálculo de score

```
👤 Usuário: "Oi"
🤖 Sistema: [Saudação + solicita CPF]

👤 Usuário: "98765432100"
🤖 Sistema: [Solicita data de nascimento]

👤 Usuário: "1985-03-20"
🤖 Sistema: [Autentica Maria + apresenta menu]

👤 Usuário: "Limite de crédito"
🤖 Sistema: [Informa limite atual]

👤 Usuário: "Quero 10000"
🤖 Sistema: [REJEITA - score 580 insuficiente]
             [Oferece entrevista financeira]

👤 Usuário: "Sim, aceito"
🤖 Sistema: [Pergunta 1/5: Renda mensal]

👤 Usuário: "R$ 8000"
🤖 Sistema: [Pergunta 2/5: Tipo de emprego]

👤 Usuário: "CLT"
🤖 Sistema: [Pergunta 3/5: Despesas fixas]

👤 Usuário: "2500"
🤖 Sistema: [Pergunta 4/5: Número de dependentes]

👤 Usuário: "1"
🤖 Sistema: [Pergunta 5/5: Tem dívidas?]

👤 Usuário: "Não"
🤖 Sistema: [Score recalculado! Novo score: XXX]
             [Redireciona para agente de crédito]

👤 Usuário: "Quero 10000 agora"
🤖 Sistema: [Re-analisa com novo score]
```

**Resultado esperado:** ✅ Novo score calculado + re-análise automática

---

### Cenário 3: Consulta de Câmbio ✅

**Objetivo:** Testar integração com API de câmbio

```
👤 Usuário: "Olá"
[... autenticação ...]

👤 Usuário: "Câmbio"
🤖 Sistema: [Entra no agente de câmbio]

👤 Usuário: "Quanto está o dólar?"
🤖 Sistema: [Cotação USD em tempo real + exemplos]

👤 Usuário: "E o euro?"
🤖 Sistema: [Cotação EUR em tempo real + exemplos]

👤 Usuário: "Voltar ao menu"
🤖 Sistema: [Retorna ao menu principal]
```

**Resultado esperado:** ✅ Cotações em tempo real com formatação

---

## 🔍 Pontos de Validação

### Durante os Testes, Verifique:

#### 1. Conversação Natural ✅
- [ ] Sistema responde de forma fluida
- [ ] Adapta tom ao contexto
- [ ] Entende variações de entrada (ex: "dólar", "USD", "dollar")

#### 2. Extração de Dados ✅
- [ ] CPF extraído corretamente (11 dígitos)
- [ ] Data normalizada (DD/MM/YYYY → YYYY-MM-DD)
- [ ] Valores monetários identificados

#### 3. Roteamento ✅
- [ ] Menu funciona (opções 1-5)
- [ ] Keywords funcionam ("crédito", "câmbio")
- [ ] Transições entre agentes são suaves

#### 4. Regras de Negócio ✅
- [ ] Aprovação/rejeição baseada em score
- [ ] Cálculo de limite máximo correto
- [ ] Recálculo de score funciona
- [ ] Cotações atualizadas

#### 5. Estado Persistente ✅
- [ ] Dados do cliente mantidos
- [ ] Histórico de conversação preservado
- [ ] Transições entre agentes não perdem contexto

---

## 📊 Clientes de Teste

### Cliente 1: João Silva (Score Alto)
```
CPF: 12345678901
Data Nascimento: 1990-05-15
Limite Atual: R$ 5.000,00
Score: 750
Resultado Esperado: Aprovações fáceis
```

### Cliente 2: Maria Santos (Score Baixo)
```
CPF: 98765432100
Data Nascimento: 1985-03-20
Limite Atual: R$ 2.000,00
Score: 580
Resultado Esperado: Rejeições, precisa entrevista
```

### Cliente 3: Carlos Oliveira (Score Médio)
```
CPF: 11122233344
Data Nascimento: 1988-11-30
Limite Atual: R$ 3.500,00
Score: 680
Resultado Esperado: Aprovações moderadas
```

---

## 🐛 Troubleshooting

### "GROQ_API_KEY não encontrada"
```bash
# Verifique o .env
cat .env  # Linux/Mac
type .env  # Windows

# Deve conter:
GROQ_API_KEY=gsk_...
```

### "Rate limit exceeded"
- Aguarde 60 segundos
- Tier gratuito tem limites
- Considere upgrade se necessário

### Respostas muito lentas
- Primeira requisição é sempre mais lenta (cold start)
- Groq geralmente responde em < 500ms
- Verifique sua conexão internet

### Sistema não entende entrada
- Tente ser mais explícito
- Use números do menu (1-5)
- Evite ambiguidades na fase de autenticação

---

## 🎯 Checklist de Validação Final

Após completar os 3 cenários:

- [ ] Autenticação funciona com variações de formato
- [ ] LLM gera respostas naturais (não hardcoded)
- [ ] Aprovação/rejeição seguem regras de score
- [ ] Entrevista coleta 5 dados corretamente
- [ ] Score é recalculado e aplicado
- [ ] Câmbio retorna cotações reais
- [ ] Menu e navegação funcionam
- [ ] Encerramento finaliza corretamente
- [ ] Sidebar mostra dados corretos (Streamlit)
- [ ] Sem crashes ou erros de execução

---

## 📈 Métricas de Performance

### Esperado (com Groq):
- **Latência média:** 200-500ms por resposta
- **Taxa de sucesso:** > 95%
- **Conversações naturais:** Sim
- **Custo:** $0 (tier gratuito)

### Se encontrar problemas:
- Verifique GROQ_API_KEY
- Verifique conexão internet
- Consulte logs: `data/logs/` (se implementado)

---

## 🚀 Próximos Testes

Após validar o básico:

1. **Teste de Estresse**
   - Múltiplas conversações simultâneas
   - Entradas malformadas
   - CPFs inválidos

2. **Teste de Edge Cases**
   - Valores extremos (R$ 1, R$ 1.000.000)
   - Datas inválidas
   - Moedas não suportadas

3. **Teste de Segurança**
   - Injection attacks
   - Acesso sem autenticação
   - Tentativas de bypass

---

## ✅ Conclusão do Teste

Se todos os checkboxes acima foram marcados:

**🎉 SISTEMA VALIDADO!**

O Banco Ágil com LLM está:
- ✅ Funcional
- ✅ Conversacional
- ✅ Inteligente
- ✅ Seguindo regras de negócio
- ✅ Pronto para apresentação

---

**Tempo estimado de teste:** 15-20 minutos
**Última atualização:** 22/01/2026
