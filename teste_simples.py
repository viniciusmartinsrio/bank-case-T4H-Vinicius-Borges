"""Teste simples do sistema LLM."""

import warnings
warnings.filterwarnings('ignore')

from banco_agil_langgraph import BancoAgilLangGraph

print("=" * 80)
print("TESTE SIMPLIFICADO DO SISTEMA LLM")
print("=" * 80)

try:
    print("\n1. Inicializando sistema...")
    sistema = BancoAgilLangGraph()
    print("   OK - Sistema inicializado")

    print("\n2. Testando saudacao inicial...")
    resposta = sistema.processar_mensagem("Ola!")
    print(f"\nResposta do sistema:\n{resposta}")

    print("\n" + "=" * 80)
    print("TESTE CONCLUIDO COM SUCESSO!")
    print("=" * 80)

except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()
