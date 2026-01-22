"""
Estado compartilhado entre agentes no LangGraph.

Define a estrutura de dados que flui através do grafo de agentes,
mantendo contexto da conversa, dados do cliente e controle de fluxo.
"""

from typing import TypedDict, Optional, Dict, List, Any, Literal
from datetime import datetime


class EstadoConversacao(TypedDict, total=False):
    """
    Estado global compartilhado entre todos os agentes.

    Este estado é passado de agente para agente no grafo LangGraph,
    permitindo que cada agente acesse e modifique informações relevantes.

    Attributes:
        mensagens: Histórico completo de mensagens (usuario e assistente)
        mensagem_atual: Última mensagem do usuário sendo processada
        agente_ativo: Nome do agente que deve processar a próxima mensagem
        cliente_autenticado: Dados do cliente após autenticação bem-sucedida
        dados_temporarios: Dados coletados durante operações (ex: entrevista)
        tentativas_autenticacao: Contador de tentativas de autenticação
        conversa_ativa: Flag indicando se atendimento está ativo
        contexto_agente: Contexto específico do agente ativo
        proximo_passo: Próxima ação a ser executada
        historico_agentes: Lista de agentes que já processaram esta conversa
    """

    # Mensagens da conversa
    mensagens: List[Dict[str, str]]  # [{"role": "user"|"assistant", "content": "..."}]
    mensagem_atual: str

    # Controle de fluxo
    agente_ativo: Literal["triagem", "credito", "entrevista_credito", "cambio", "encerramento"]
    proximo_passo: Optional[str]
    conversa_ativa: bool
    historico_agentes: List[str]  # Rastreamento de quais agentes foram acionados

    # Dados do cliente
    cliente_autenticado: Optional[Dict[str, Any]]  # Dados de clientes.csv
    tentativas_autenticacao: int

    # Dados temporários durante operações
    dados_temporarios: Dict[str, Any]  # Armazena dados coletados durante fluxos
    contexto_agente: Dict[str, Any]    # Contexto específico do agente ativo

    # Metadados
    timestamp_inicio: str
    timestamp_ultima_mensagem: str


# Estrutura de dados do cliente autenticado
class DadosCliente(TypedDict):
    """Estrutura dos dados do cliente após autenticação."""
    cpf: str
    nome: str
    data_nascimento: str
    limite_credito: float
    score_credito: float


# Estrutura de dados temporários para operações específicas
class DadosTriagem(TypedDict, total=False):
    """Dados temporários coletados durante triagem."""
    cpf_coletado: Optional[str]
    data_nascimento_coletada: Optional[str]
    tentativa_atual: int


class DadosCredito(TypedDict, total=False):
    """Dados temporários durante operação de crédito."""
    solicitacao_em_andamento: bool
    novo_limite_solicitado: Optional[float]
    status_solicitacao: Optional[str]  # "pendente", "aprovado", "rejeitado"
    limite_maximo_permitido: Optional[float]


class DadosEntrevista(TypedDict, total=False):
    """Dados coletados durante entrevista financeira."""
    renda_mensal: Optional[float]
    tipo_emprego: Optional[str]  # "formal", "autônomo", "desempregado"
    despesas_fixas: Optional[float]
    num_dependentes: Optional[int]
    tem_dividas: Optional[str]  # "sim", "não"
    pergunta_atual: int  # 1 a 5
    novo_score_calculado: Optional[float]


class DadosCambio(TypedDict, total=False):
    """Dados temporários para operação de câmbio."""
    moeda_solicitada: Optional[str]
    cotacao_atual: Optional[float]
    data_cotacao: Optional[str]


def criar_estado_inicial() -> EstadoConversacao:
    """
    Cria um estado inicial vazio para nova conversa.

    Returns:
        EstadoConversacao com valores padrão inicializados
    """
    timestamp_agora = datetime.now().isoformat()

    return EstadoConversacao(
        mensagens=[],
        mensagem_atual="",
        agente_ativo="triagem",  # Sempre começa com triagem
        proximo_passo=None,
        conversa_ativa=True,
        historico_agentes=[],
        cliente_autenticado=None,
        tentativas_autenticacao=0,
        dados_temporarios={},
        contexto_agente={},
        timestamp_inicio=timestamp_agora,
        timestamp_ultima_mensagem=timestamp_agora
    )


def adicionar_mensagem(
    estado: EstadoConversacao,
    role: Literal["user", "assistant"],
    content: str
) -> EstadoConversacao:
    """
    Adiciona uma mensagem ao histórico do estado.

    Args:
        estado: Estado atual da conversa
        role: "user" para mensagem do usuário, "assistant" para resposta do agente
        content: Conteúdo da mensagem

    Returns:
        Estado atualizado com nova mensagem
    """
    nova_mensagem = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }

    estado["mensagens"].append(nova_mensagem)
    estado["timestamp_ultima_mensagem"] = nova_mensagem["timestamp"]

    return estado


def atualizar_agente_ativo(
    estado: EstadoConversacao,
    novo_agente: str
) -> EstadoConversacao:
    """
    Atualiza o agente ativo e registra no histórico.

    Args:
        estado: Estado atual da conversa
        novo_agente: Nome do novo agente a ser ativado

    Returns:
        Estado atualizado com novo agente ativo
    """
    # Registra transição no histórico
    if estado["agente_ativo"] != novo_agente:
        estado["historico_agentes"].append(
            f"{estado['agente_ativo']} -> {novo_agente}"
        )

    estado["agente_ativo"] = novo_agente

    # Limpa contexto do agente anterior
    estado["contexto_agente"] = {}

    return estado


def autenticar_cliente(
    estado: EstadoConversacao,
    dados_cliente: DadosCliente
) -> EstadoConversacao:
    """
    Registra cliente autenticado no estado.

    Args:
        estado: Estado atual da conversa
        dados_cliente: Dados do cliente autenticado

    Returns:
        Estado atualizado com dados do cliente
    """
    estado["cliente_autenticado"] = dados_cliente
    estado["tentativas_autenticacao"] = 0  # Reseta contador

    return estado


def incrementar_tentativa_autenticacao(
    estado: EstadoConversacao
) -> EstadoConversacao:
    """
    Incrementa contador de tentativas de autenticação.

    Args:
        estado: Estado atual da conversa

    Returns:
        Estado atualizado com contador incrementado
    """
    estado["tentativas_autenticacao"] += 1
    return estado


def encerrar_conversa(estado: EstadoConversacao) -> EstadoConversacao:
    """
    Marca conversa como encerrada.

    Args:
        estado: Estado atual da conversa

    Returns:
        Estado atualizado com flag de conversa inativa
    """
    estado["conversa_ativa"] = False
    estado["agente_ativo"] = "encerramento"
    return estado


def obter_resumo_estado(estado: EstadoConversacao) -> str:
    """
    Gera um resumo textual do estado atual (útil para debug).

    Args:
        estado: Estado atual da conversa

    Returns:
        String formatada com resumo do estado
    """
    resumo = []
    resumo.append("=" * 60)
    resumo.append("RESUMO DO ESTADO DA CONVERSA")
    resumo.append("=" * 60)

    resumo.append(f"\n🤖 Agente Ativo: {estado.get('agente_ativo', 'N/A')}")
    resumo.append(f"🔴 Conversa Ativa: {estado.get('conversa_ativa', False)}")

    if estado.get("cliente_autenticado"):
        cliente = estado["cliente_autenticado"]
        resumo.append(f"\n👤 Cliente Autenticado:")
        resumo.append(f"   Nome: {cliente.get('nome', 'N/A')}")
        resumo.append(f"   CPF: {cliente.get('cpf', 'N/A')}")
        resumo.append(f"   Score: {cliente.get('score_credito', 'N/A')}")
    else:
        resumo.append(f"\n👤 Cliente: Não autenticado")
        resumo.append(f"   Tentativas: {estado.get('tentativas_autenticacao', 0)}/3")

    resumo.append(f"\n💬 Mensagens Trocadas: {len(estado.get('mensagens', []))}")

    if estado.get("historico_agentes"):
        resumo.append(f"\n📊 Fluxo de Agentes:")
        for transicao in estado["historico_agentes"]:
            resumo.append(f"   • {transicao}")

    if estado.get("dados_temporarios"):
        resumo.append(f"\n📦 Dados Temporários: {len(estado['dados_temporarios'])} itens")

    resumo.append("\n" + "=" * 60)

    return "\n".join(resumo)


if __name__ == "__main__":
    # Teste básico da estrutura de estado
    print("Testando estrutura de estado...")

    estado = criar_estado_inicial()
    print("\nEstado inicial criado:")
    print(obter_resumo_estado(estado))

    # Simula algumas operações
    estado = adicionar_mensagem(estado, "user", "Olá!")
    estado = adicionar_mensagem(estado, "assistant", "Bem-vindo ao Banco Ágil!")
    estado = incrementar_tentativa_autenticacao(estado)

    print("\nApós algumas operações:")
    print(obter_resumo_estado(estado))

    print("\n✅ Estrutura de estado funcionando corretamente!")
