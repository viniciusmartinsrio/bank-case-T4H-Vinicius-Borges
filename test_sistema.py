"""
Script de teste automatizado para o sistema Banco Ágil.
Simula diferentes fluxos de atendimento.
"""

from banco_agil_system import BancoAgilSystem


def print_separador(titulo=""):
    """Imprime um separador visual."""
    if titulo:
        print(f"\n{'='*60}")
        print(f"  {titulo}")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'-'*60}\n")


def teste_fluxo_1():
    """Teste 1: Consultar limite de crédito"""
    print_separador("TESTE 1: Consultar Limite de Crédito")
    
    sistema = BancoAgilSystem()
    
    # Inicia atendimento
    print("Sistema:", sistema.iniciar_atendimento())
    
    # Fornece CPF
    print("\nUsuário: 12345678901")
    resposta = sistema.processar_entrada("12345678901")
    print("Sistema:", resposta)
    
    # Fornece data
    print("\nUsuário: 1990-05-15")
    resposta = sistema.processar_entrada("1990-05-15")
    print("Sistema:", resposta)
    
    # Escolhe opção 1 (Consultar limite)
    print("\nUsuário: 1")
    resposta = sistema.processar_entrada("1")
    print("Sistema:", resposta)
    
    print_separador("✅ Teste 1 Concluído")


def teste_fluxo_2():
    """Teste 2: Solicitar aumento aprovado"""
    print_separador("TESTE 2: Solicitar Aumento Aprovado")
    
    sistema = BancoAgilSystem()
    
    # Inicia e autentica
    print("Sistema:", sistema.iniciar_atendimento())
    
    print("\nUsuário: 98765432109")
    resposta = sistema.processar_entrada("98765432109")
    print("Sistema:", resposta)
    
    print("\nUsuário: 1985-08-22")
    resposta = sistema.processar_entrada("1985-08-22")
    print("Sistema:", resposta)
    
    # Escolhe opção 2 (Solicitar aumento)
    print("\nUsuário: 2")
    resposta = sistema.processar_entrada("2")
    print("Sistema:", resposta)
    
    # Responde "sim" para solicitar aumento
    print("\nUsuário: sim")
    resposta = sistema.processar_entrada("sim")
    print("Sistema:", resposta)
    
    # Fornece novo limite
    print("\nUsuário: 10000")
    resposta = sistema.processar_entrada("10000")
    print("Sistema:", resposta)
    
    print_separador("✅ Teste 2 Concluído")


def teste_fluxo_3():
    """Teste 3: Solicitar aumento rejeitado + Entrevista"""
    print_separador("TESTE 3: Solicitar Aumento Rejeitado + Entrevista")
    
    sistema = BancoAgilSystem()
    
    # Inicia e autentica
    print("Sistema:", sistema.iniciar_atendimento())
    
    print("\nUsuário: 55555555555")
    resposta = sistema.processar_entrada("55555555555")
    print("Sistema:", resposta)
    
    print("\nUsuário: 1992-03-10")
    resposta = sistema.processar_entrada("1992-03-10")
    print("Sistema:", resposta)
    
    # Escolhe opção 2 (Solicitar aumento)
    print("\nUsuário: 2")
    resposta = sistema.processar_entrada("2")
    print("Sistema:", resposta)
    
    # Responde "sim" para solicitar aumento
    print("\nUsuário: sim")
    resposta = sistema.processar_entrada("sim")
    print("Sistema:", resposta)
    
    # Fornece novo limite (que será rejeitado)
    print("\nUsuário: 15000")
    resposta = sistema.processar_entrada("15000")
    print("Sistema:", resposta)
    
    # Aceita entrevista
    print("\nUsuário: sim")
    resposta = sistema.processar_entrada("sim")
    print("Sistema:", resposta)
    
    # Responde perguntas da entrevista
    print("\nUsuário: 5000")
    resposta = sistema.processar_entrada("5000")
    print("Sistema:", resposta)
    
    print("\nUsuário: formal")
    resposta = sistema.processar_entrada("formal")
    print("Sistema:", resposta)
    
    print("\nUsuário: 2000")
    resposta = sistema.processar_entrada("2000")
    print("Sistema:", resposta)
    
    print("\nUsuário: 1")
    resposta = sistema.processar_entrada("1")
    print("Sistema:", resposta)
    
    print("\nUsuário: não")
    resposta = sistema.processar_entrada("não")
    print("Sistema:", resposta)
    
    print_separador("✅ Teste 3 Concluído")


def teste_fluxo_4():
    """Teste 4: Consultar câmbio"""
    print_separador("TESTE 4: Consultar Câmbio")
    
    sistema = BancoAgilSystem()
    
    # Inicia e autentica
    print("Sistema:", sistema.iniciar_atendimento())
    
    print("\nUsuário: 12345678901")
    resposta = sistema.processar_entrada("12345678901")
    print("Sistema:", resposta)
    
    print("\nUsuário: 1990-05-15")
    resposta = sistema.processar_entrada("1990-05-15")
    print("Sistema:", resposta)
    
    # Escolhe opção 4 (Câmbio)
    print("\nUsuário: 4")
    resposta = sistema.processar_entrada("4")
    print("Sistema:", resposta)
    
    # Deixa em branco para usar USD padrão
    print("\nUsuário: (deixa em branco)")
    resposta = sistema.processar_entrada("")
    print("Sistema:", resposta)
    
    # Não quer consultar outra moeda
    print("\nUsuário: não")
    resposta = sistema.processar_entrada("não")
    print("Sistema:", resposta)
    
    print_separador("✅ Teste 4 Concluído")


def teste_autenticacao_falha():
    """Teste: Falha de autenticação"""
    print_separador("TESTE: Falha de Autenticação")
    
    sistema = BancoAgilSystem()
    
    print("Sistema:", sistema.iniciar_atendimento())
    
    # Tenta 3 vezes com dados errados
    for tentativa in range(1, 4):
        print(f"\nTentativa {tentativa}:")
        print("Usuário: 00000000000")
        resposta = sistema.processar_entrada("00000000000")
        print("Sistema:", resposta)
        
        if tentativa < 3:
            print("\nUsuário: 2000-01-01")
            resposta = sistema.processar_entrada("2000-01-01")
            print("Sistema:", resposta)
    
    print_separador("✅ Teste de Falha Concluído")


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("  TESTES DO SISTEMA BANCO ÁGIL")
    print("="*60)
    
    try:
        teste_fluxo_1()
        teste_fluxo_2()
        teste_fluxo_3()
        teste_fluxo_4()
        teste_autenticacao_falha()
        
        print("\n" + "="*60)
        print("  ✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
