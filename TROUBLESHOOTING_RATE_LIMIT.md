# Troubleshooting: Rate Limit do Groq

## 🚨 Problema: "Rate limit reached for model llama-3.3-70b-versatile"

Você está vendo este erro porque atingiu o **limite diário de 100.000 tokens** do plano gratuito do Groq.

```
groq.RateLimitError: Error code: 429 - {'error': {'message': 'Rate limit reached for model `llama-3.3-70b-versatile` in organization `org_...` on tokens per day (TPD): Limit 100000, Used 99717, Requested 1207. Please try again in 13m18.336s...
```

---

## ✅ Soluções Rápidas

### Solução 1: Usar Modelo Menor (RECOMENDADO)

O modelo **Llama 3.1 8B** consome aproximadamente **10x menos tokens** que o 3.3 70B, permitindo muito mais interações por dia.

**Passos:**

1. Abra o arquivo `llm_config.py`
2. Localize a linha (aproximadamente linha 15):
   ```python
   ACTIVE_MODEL = DEFAULT_MODEL  # Ou FALLBACK_MODEL se preferir economizar tokens
   ```
3. Mude para:
   ```python
   ACTIVE_MODEL = FALLBACK_MODEL  # Modelo menor e econômico
   ```
4. Salve o arquivo
5. **Reinicie a aplicação Streamlit** (Ctrl+C e execute novamente)

**Comparação de Consumo:**

| Modelo | Parâmetros | Tokens/Interação (média) | Interações/Dia (100k tokens) |
|--------|------------|-------------------------|------------------------------|
| Llama 3.3 70B | 70 bilhões | ~1500 tokens | ~66 interações |
| Llama 3.1 8B | 8 bilhões | ~150 tokens | ~666 interações |

---

### Solução 2: Aguardar Reset Diário

O limite de tokens **reseta automaticamente** todos os dias às:
- **00:00 UTC**
- **21:00 horário de Brasília (BRT)**

Aguarde o tempo indicado no erro (ex: "try again in 13m18s") e tente novamente.

---

### Solução 3: Upgrade para Plano Pago

Se você precisa de mais tokens imediatamente:

1. Acesse: https://console.groq.com/settings/billing
2. Faça upgrade para o **Dev Tier**
3. Custos aproximados:
   - **Llama 3.3 70B**: $0.59 por milhão de tokens de input
   - **Llama 3.1 8B**: $0.05 por milhão de tokens de input

**Estimativa mensal (uso intenso):**
- 1 milhão de tokens/mês com 70B = ~$0.60/mês
- 1 milhão de tokens/mês com 8B = ~$0.05/mês

---

## 🔍 Como Monitorar seu Uso de Tokens

### Via Console do Groq

1. Acesse: https://console.groq.com/
2. Vá em **Usage** ou **Dashboard**
3. Verifique o consumo diário de tokens

### Via Código (Futuro)

Você pode adicionar um contador de tokens no código para monitorar localmente. Exemplo:

```python
# Adicionar em app_llm_improved.py ou banco_agil_langgraph.py

def log_token_usage(response):
    """Registra uso de tokens."""
    if hasattr(response, 'usage'):
        usage = response.usage
        print(f"Tokens usados: {usage.total_tokens}")
        print(f"- Input: {usage.prompt_tokens}")
        print(f"- Output: {usage.completion_tokens}")
```

---

## 💡 Boas Práticas para Economizar Tokens

### 1. Use Mensagens Mais Curtas
- ❌ Ruim: Descrever todo o contexto a cada mensagem
- ✅ Bom: O sistema já mantém histórico, seja direto

### 2. Limite o Histórico de Conversação
- O sistema envia todo o histórico a cada mensagem
- Considere limitar a 10-20 mensagens recentes

### 3. Ajuste max_tokens nos Agentes
Em `llm_config.py`, você pode reduzir `max_tokens`:

```python
"triagem": {
    "max_tokens": 150,  # Era 200, reduzido para economizar
    ...
}
```

### 4. Use o Modelo Menor por Padrão
Se você não precisa de respostas super sofisticadas, use sempre o 8B:

```python
ACTIVE_MODEL = FALLBACK_MODEL  # Economiza 90% dos tokens
```

---

## 🛠️ Troubleshooting Adicional

### Erro persiste mesmo após trocar modelo

**Causa:** Aplicação não foi reiniciada corretamente.

**Solução:**
1. No terminal onde o Streamlit está rodando, pressione `Ctrl+C`
2. Aguarde o processo terminar completamente
3. Execute novamente: `python -m streamlit run app_llm_improved.py`

### Erro: "Module 'llm_config' has no attribute 'FALLBACK_MODEL'"

**Causa:** Versão antiga do arquivo `llm_config.py`.

**Solução:**
Verifique se o arquivo contém as linhas:
```python
DEFAULT_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"
ACTIVE_MODEL = DEFAULT_MODEL
```

### Aplicação não carrega nem com modelo menor

**Causa:** Cache do Streamlit pode estar usando configuração antiga.

**Solução:**
```bash
# Limpa cache do Streamlit
streamlit cache clear

# Ou reinicie com flag --server.headless
python -m streamlit run app_llm_improved.py --server.headless true
```

---

## 📊 Comparação: Llama 3.3 70B vs Llama 3.1 8B

| Aspecto | Llama 3.3 70B | Llama 3.1 8B |
|---------|---------------|--------------|
| **Qualidade de Resposta** | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐⭐ Muito Boa |
| **Velocidade** | 🐌 ~2-4s por resposta | 🚀 ~0.5-1s por resposta |
| **Consumo de Tokens** | 🔥 Alto (~1500/interação) | ✅ Baixo (~150/interação) |
| **Complexidade de Raciocínio** | ⭐⭐⭐⭐⭐ Superior | ⭐⭐⭐ Bom |
| **Seguir Instruções** | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐⭐ Muito Bom |
| **Recomendação** | Produção/Qualidade | Desenvolvimento/Economia |

**Veredicto:**
- Use **70B** se qualidade é crítica e você tem budget
- Use **8B** para desenvolvimento, testes e quando tokens são limitados

Para este projeto bancário, o **8B é mais que suficiente** para:
- ✅ Autenticação de clientes
- ✅ Consultas de limite
- ✅ Entrevistas financeiras
- ✅ Consultas de câmbio

A diferença de qualidade só seria notável em tarefas muito complexas como análise jurídica, tradução técnica, ou código sofisticado.

---

## 🎯 Recomendação Final

**Para uso diário e desenvolvimento:**
```python
# Em llm_config.py
ACTIVE_MODEL = FALLBACK_MODEL  # Llama 3.1 8B
```

**Para demonstrações importantes ou produção:**
```python
# Em llm_config.py
ACTIVE_MODEL = DEFAULT_MODEL  # Llama 3.3 70B
```

---

## 📞 Suporte

Se o problema persistir:

1. Verifique logs no terminal onde o Streamlit está rodando
2. Consulte documentação do Groq: https://console.groq.com/docs
3. Verifique status do serviço: https://status.groq.com/

---

**Última atualização:** 2026-01-22
