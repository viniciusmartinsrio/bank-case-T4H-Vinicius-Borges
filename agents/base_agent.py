"""
Classe base para agentes com LLM do Banco Ágil.

Fornece funcionalidade comum a todos os agentes, incluindo
inicialização de LLM, gerenciamento de conversação e ferramentas.
"""

import os
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
from dotenv import load_dotenv

from llm_config import get_llm_config
from prompts import get_prompt

# Carrega variáveis de ambiente
load_dotenv()


class BaseAgent:
    """
    Classe base para todos os agentes do Banco Ágil.

    Fornece funcionalidade comum como inicialização de LLM,
    gerenciamento de histórico de mensagens e invocação do modelo.
    """

    def __init__(
        self,
        agent_name: str,
        tools: Optional[List[Tool]] = None,
        groq_api_key: Optional[str] = None
    ):
        """
        Inicializa o agente base.

        Args:
            agent_name: Nome do agente (usado para buscar config e prompt)
            tools: Lista de ferramentas disponíveis para o agente
            groq_api_key: API key do Groq (se None, usa variável de ambiente)
        """
        self.agent_name = agent_name
        self.tools = tools or []

        # Obtém API key
        self.api_key = groq_api_key or os.getenv("GROQ_API_KEY")

        # Obtém configuração de LLM para este agente
        self.llm_config = get_llm_config(agent_name)

        # Inicializa o modelo LLM
        self.llm = self._initialize_llm()

        # Obtém system prompt para este agente
        self.system_prompt = get_prompt(agent_name)

        # Histórico de mensagens desta sessão
        self.conversation_history: List[Dict[str, str]] = []

    def _initialize_llm(self) -> ChatGroq:
        """
        Inicializa o modelo LLM com as configurações específicas do agente.

        Returns:
            Instância configurada do ChatGroq
        """
        return ChatGroq(
            groq_api_key=self.api_key,
            model_name=self.llm_config["model_name"],
            temperature=self.llm_config["temperature"],
            top_p=self.llm_config["top_p"],
            max_tokens=self.llm_config["max_tokens"],
            streaming=self.llm_config.get("streaming", False),
        )

    def _build_messages(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List:
        """
        Constrói a lista de mensagens para enviar ao LLM.

        Inclui system prompt, histórico da conversa e mensagem atual.

        Args:
            user_message: Mensagem atual do usuário
            context: Contexto adicional para formatar o system prompt

        Returns:
            Lista de mensagens formatadas para o LLM
        """
        messages = []

        # System prompt (com contexto se fornecido)
        if context:
            # Formata apenas os placeholders que existem no contexto
            # Mantém os outros intactos
            import re
            import string

            class SafeFormatter(string.Formatter):
                def get_value(self, key, args, kwargs):
                    if isinstance(key, str):
                        return kwargs.get(key, '{' + key + '}')
                    else:
                        return super().get_value(key, args, kwargs)

                def format_field(self, value, format_spec):
                    # Se o valor ainda é um placeholder não substituído, retorna como está
                    if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                        return value
                    return super().format_field(value, format_spec)

            formatter = SafeFormatter()
            formatted_prompt = formatter.format(self.system_prompt, **context)
        else:
            formatted_prompt = self.system_prompt

        messages.append(SystemMessage(content=formatted_prompt))

        # Histórico da conversa
        for msg in self.conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Mensagem atual
        messages.append(HumanMessage(content=user_message))

        return messages

    def invoke(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        add_to_history: bool = True
    ) -> str:
        """
        Invoca o LLM com a mensagem do usuário.

        Args:
            user_message: Mensagem do usuário
            context: Contexto adicional (ex: dados do cliente)
            add_to_history: Se True, adiciona mensagem ao histórico

        Returns:
            Resposta do agente (LLM)
        """
        # Constrói mensagens
        messages = self._build_messages(user_message, context)

        # Invoca LLM
        if self.tools:
            # Se há ferramentas, usa bind_tools
            llm_with_tools = self.llm.bind_tools(self.tools)
            response = llm_with_tools.invoke(messages)
        else:
            response = self.llm.invoke(messages)

        # Extrai conteúdo da resposta
        response_content = response.content

        # Adiciona ao histórico se solicitado
        if add_to_history:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response_content
            })

        return response_content

    def reset_history(self):
        """Limpa o histórico de conversação."""
        self.conversation_history = []

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Retorna o histórico de conversação."""
        return self.conversation_history.copy()

    def get_config_summary(self) -> Dict[str, Any]:
        """Retorna resumo da configuração do agente."""
        return {
            "agent_name": self.agent_name,
            "model": self.llm_config["model_name"],
            "temperature": self.llm_config["temperature"],
            "top_p": self.llm_config["top_p"],
            "max_tokens": self.llm_config["max_tokens"],
            "tools_count": len(self.tools),
            "conversation_length": len(self.conversation_history)
        }

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name={self.agent_name} "
            f"model={self.llm_config['model_name']} "
            f"temp={self.llm_config['temperature']}>"
        )
