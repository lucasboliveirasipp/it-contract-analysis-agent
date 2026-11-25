"""Construtor do Agente ReAct para Análise de Contratos.

Cria o agente usando LangGraph com padrão ReAct (Reasoning + Acting).
"""

import logging
from typing import List
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from config import llm
from agente_analise_contratos_prompts.system_prompt import SYSTEM_PROMPT

# Importar todas as skills
from agente_analise_contratos_skills.extrair_texto import extrair_texto
from agente_analise_contratos_skills.classificar_contrato import classificar_contrato
from agente_analise_contratos_skills.extrair_clausulas import extrair_clausulas
from agente_analise_contratos_skills.buscar_contratos import buscar_contratos
from agente_analise_contratos_skills.comparar_contratos import comparar_contratos
from agente_analise_contratos_skills.gerar_relatorio import gerar_relatorio
from agente_analise_contratos_skills.indexar_contrato import indexar_contrato

logger = logging.getLogger(__name__)


def construir_agente():
    """Constrói o agente ReAct com todas as skills.

    Returns:
        Agente LangGraph compilado e pronto para uso
    """
    logger.info("=" * 60)
    logger.info("🔨 Construindo agente de análise de contratos...")
    logger.info("=" * 60)

    # Verificar se LLM está disponível
    if not llm:
        logger.error("❌ LLM não inicializado!")
        raise RuntimeError("LLM não inicializado. Verifique as configurações em config.py")

    logger.info(f"✅ LLM disponível: {type(llm).__name__}")

    # Lista de todas as skills (tools)
    logger.info("📦 Carregando skills...")
    tools: List[BaseTool] = [
        extrair_texto,
        classificar_contrato,
        extrair_clausulas,
        buscar_contratos,
        comparar_contratos,
        gerar_relatorio,
        indexar_contrato,
    ]

    skills_names = [tool.name for tool in tools]
    logger.info(f"✅ {len(tools)} skills carregadas: {', '.join(skills_names)}")

    # Configurar memória para manter estado entre execuções
    logger.info("💾 Configurando MemorySaver...")
    memory = MemorySaver()
    logger.info("✅ MemorySaver configurado")

    # Criar agente ReAct
    logger.info("🤖 Criando agente ReAct com create_react_agent...")
    try:
        agent = create_react_agent(
            model=llm,
            tools=tools,
            state_modifier=SYSTEM_PROMPT,
            checkpointer=memory
        )
        logger.info("✅ Agente ReAct criado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao criar agente: {e}", exc_info=True)
        raise

    logger.info("=" * 60)
    logger.info("✅ AGENTE CONSTRUÍDO COM SUCESSO")
    logger.info("=" * 60)

    return agent


def executar_agente(agente, mensagem: str, thread_id: str = "default"):
    """Executa o agente com uma mensagem do usuário.
    
    Args:
        agente: Agente compilado
        mensagem: Mensagem do usuário
        thread_id: ID da thread/sessão para manter contexto
        
    Returns:
        Resposta do agente
    """
    try:
        if not mensagem or not str(mensagem).strip():
            return {"resposta": "Por favor, envie uma mensagem.", "eventos": [], "sucesso": False, "erro": "Mensagem vazia"}
        mensagem = str(mensagem).strip()
        logger.info(f"Executando agente com mensagem: {mensagem[:100]}...")
        
        # Configuração da thread
        config = {"configurable": {"thread_id": thread_id}}
        
        # Executar agente
        resposta_final = None
        eventos = []
        
        for evento in agente.stream(
            {"messages": [("user", mensagem)]},
            config=config,
            stream_mode="values"
        ):
            eventos.append(evento)
            
            # Último evento contém a resposta final
            if "messages" in evento:
                messages = evento["messages"]
                if messages:
                    ultima_msg = messages[-1]
                    if hasattr(ultima_msg, 'content'):
                        resposta_final = ultima_msg.content
        
        logger.info("✅ Execução do agente concluída")
        
        return {
            "resposta": resposta_final,
            "eventos": eventos,
            "sucesso": True
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao executar agente: {e}")
        return {
            "resposta": f"Erro ao processar: {str(e)}",
            "eventos": [],
            "sucesso": False,
            "erro": str(e)
        }


def executar_agente_streaming(agente, mensagem: str, thread_id: str = "default"):
    """Executa o agente com streaming de eventos.

    Útil para interface que quer mostrar o progresso em tempo real.

    Args:
        agente: Agente compilado
        mensagem: Mensagem do usuário
        thread_id: ID da thread/sessão

    Yields:
        Eventos do agente conforme são gerados
    """
    logger.info("=" * 60)
    logger.info(f"🚀 INICIANDO STREAMING")
    logger.info(f"📝 Mensagem: {mensagem[:100]}{'...' if len(mensagem) > 100 else ''}")
    logger.info(f"🔗 Thread ID: {thread_id}")
    logger.info("=" * 60)

    try:
        config = {"configurable": {"thread_id": thread_id}}
        logger.info(f"⚙️ Config: {config}")

        evento_num = 0
        for evento in agente.stream(
            {"messages": [("user", mensagem)]},
            config=config,
            stream_mode="values"
        ):
            evento_num += 1
            logger.info(f"📦 Evento #{evento_num} recebido")
            logger.debug(f"   Chaves: {list(evento.keys())}")

            if "messages" in evento:
                messages = evento["messages"]
                logger.info(f"   📨 {len(messages)} mensagem(ns) no evento")

                # Log da última mensagem
                if messages:
                    ultima = messages[-1]
                    msg_type = type(ultima).__name__
                    logger.info(f"   📬 Última mensagem: tipo={msg_type}")

                    if hasattr(ultima, "content"):
                        content = str(ultima.content)[:150]
                        logger.info(f"   💬 Conteúdo: {content}...")

                    if hasattr(ultima, "tool_calls") and ultima.tool_calls:
                        for tc in ultima.tool_calls:
                            logger.info(f"   🔧 Tool call: {tc.get('name', 'unknown')}")

            yield evento

        logger.info("=" * 60)
        logger.info(f"✅ STREAMING CONCLUÍDO - Total: {evento_num} eventos")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ ERRO NO STREAMING: {e}")
        logger.error("=" * 60)
        logger.error(f"Detalhes do erro:", exc_info=True)
        yield {"erro": str(e)}


# Instância global do agente (lazy loading)
_agente_global = None


def obter_agente():
    """Obtém instância do agente (singleton).

    Returns:
        Agente compilado
    """
    global _agente_global

    if _agente_global is None:
        logger.info("🆕 Primeira inicialização do agente - criando nova instância...")
        _agente_global = construir_agente()
        logger.info("✅ Instância global do agente criada e armazenada")
    else:
        logger.info("♻️ Reutilizando instância existente do agente")

    return _agente_global


# Função de conveniência para executar rapidamente
def processar_mensagem(mensagem: str, thread_id: str = "default"):
    """Função de conveniência para processar uma mensagem.
    
    Args:
        mensagem: Mensagem do usuário
        thread_id: ID da thread/sessão
        
    Returns:
        Dict com resposta e metadados
    """
    agente = obter_agente()
    return executar_agente(agente, mensagem, thread_id)




if __name__ == "__main__":
    # Teste básico
    logging.basicConfig(level=logging.INFO)
    
    print("🤖 Testando agente de análise de contratos...\n")
    
    # Construir agente
    agente = construir_agente()
    
    # Testar mensagem simples
    mensagem_teste = "Olá! Quais são suas capacidades?"
    print(f"Usuário: {mensagem_teste}\n")
    
    resultado = executar_agente(agente, mensagem_teste)
    
    if resultado["sucesso"]:
        print(f"Agente: {resultado['resposta']}\n")
    else:
        print(f"Erro: {resultado['erro']}\n")
    
    print("✅ Teste concluído!")
