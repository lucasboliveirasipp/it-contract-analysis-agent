"""Estado do Agente de Análise de Contratos.

Define a estrutura de estado usada pelo LangGraph no padrão ReAct.

Nota: O create_react_agent do LangGraph usa apenas o estado de mensagens por padrão.
AgentState e get_initial_agent_state() estão aqui para uso futuro (estado customizado
ou integração com Streamlit/sessão). O graph_builder não os utiliza atualmente.
"""

from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Estado do agente ReAct para análise de contratos.
    
    O estado mantém o histórico de mensagens e contexto compartilhado
    entre todas as skills do agente.
    
    Attributes:
        messages: Histórico de mensagens (HumanMessage, AIMessage, ToolMessage)
                  Usa add_messages para append automático
        contratos_carregados: Dicionário de contratos carregados em memória
        contexto_busca: Contexto de busca atual
        historico_acoes: Histórico de ações executadas
        erro: Mensagem de erro, se houver
    """
    
    # Mensagens do chat (ReAct)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Contratos carregados na sessão
    contratos_carregados: Dict[str, Any]
    
    # Contexto de busca atual
    contexto_busca: Optional[List[Dict[str, Any]]]
    
    # Histórico de ações (para debugging/logging)
    historico_acoes: List[str]
    
    # Erro (se houver)
    erro: Optional[str]


class SessionState(TypedDict):
    """Estado da sessão Streamlit (complementar ao AgentState).
    
    Mantém informações de UI e cache que não precisam ser passadas
    ao agente em cada iteração.
    
    Attributes:
        contratos_indexados: Lista de contratos já indexados
        ultimo_upload: Timestamp do último upload
        filtros_ativos: Filtros de busca ativos
        modo_debug: Flag de modo debug
    """
    
    contratos_indexados: List[Dict[str, str]]
    ultimo_upload: Optional[str]
    filtros_ativos: Dict[str, Any]
    modo_debug: bool


# Estado inicial do agente
def get_initial_agent_state() -> AgentState:
    """Retorna estado inicial do agente."""
    return AgentState(
        messages=[],
        contratos_carregados={},
        contexto_busca=None,
        historico_acoes=[],
        erro=None
    )


# Estado inicial da sessão
def get_initial_session_state() -> SessionState:
    """Retorna estado inicial da sessão."""
    return SessionState(
        contratos_indexados=[],
        ultimo_upload=None,
        filtros_ativos={},
        modo_debug=False
    )
