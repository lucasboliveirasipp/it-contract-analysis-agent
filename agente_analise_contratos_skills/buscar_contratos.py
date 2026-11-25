"""Skill: Buscar Contratos.

Realiza busca semântica no índice de contratos usando Azure AI Search.
"""

import logging
import json
from typing import Optional, Dict, Any
from langchain_core.tools import tool
import sys
from pathlib import Path
_agent_dir = Path(__file__).resolve().parent.parent
if str(_agent_dir) not in sys.path:
    sys.path.insert(0, str(_agent_dir))
from _local_imports import load_local_module
AzureSearchClient = load_local_module("azure_search", subdir="agente_analise_contratos_utils").AzureSearchClient

logger = logging.getLogger(__name__)

# Instanciar cliente de busca
search_client = AzureSearchClient()


@tool
def buscar_contratos(query: str, filtros: Optional[str] = None) -> str:
    """🔍 BUSCA SEMÂNTICA na base de conhecimento de contratos indexados.

    **USE ESTA FERRAMENTA QUANDO:**
    - O usuário fizer PERGUNTAS sobre conteúdo de contratos já indexados
    - O usuário pedir INFORMAÇÕES que estejam nos contratos
    - O usuário quiser CONSULTAR cláusulas, valores, datas, condições
    - O usuário mencionar palavras-chave como: "quais", "mostre", "encontre", "busque", "liste"

    **NÃO USE quando:**
    - O usuário fornecer um NOME DE ARQUIVO para processar (use extrair_texto)
    - For para classificar TEXTO já extraído (use classificar_contrato)

    Realiza busca híbrida (texto + vetores) no Azure AI Search.

    Args:
        query: Pergunta ou termos de busca sobre contratos indexados.
               Reformule perguntas em termos de busca relevantes.

               Exemplos de perguntas → queries:
               - "Quais as penalidades?" → "penalidades rescisão multa"
               - "Mostre contratos da TECHNOVA" → "TECHNOVA"
               - "Qual o SLA?" → "SLA tempo resposta atendimento"
               - "Contratos que vencem?" → "vencimento término vigência 2025"
               - "Há cláusulas de LGPD?" → "LGPD dados pessoais proteção"

        filtros: (Opcional) Filtros em formato JSON string:
                 {"tipo_contrato": "software", "fornecedor": "TECHNOVA"}

    Returns:
        String com os contratos encontrados e conteúdo relevante formatados.
        Use o conteúdo retornado para responder a pergunta do usuário.

    Examples:
        >>> buscar_contratos("penalidades rescisão")
        >>> buscar_contratos("TECHNOVA")
        >>> buscar_contratos("SLA tempo resposta")
        >>> buscar_contratos("vencimento 2025")
        >>> buscar_contratos("LGPD proteção dados")
    """
    try:
        logger.info(f"Buscando contratos: {query}")
        
        # Parsear filtros se fornecidos
        filtros_dict = None
        if filtros:
            try:
                filtros_dict = json.loads(filtros)
            except json.JSONDecodeError:
                logger.warning(f"Filtros inválidos ignorados: {filtros}")
        
        # Realizar busca
        resultados = search_client.buscar(
            query=query,
            top_k=5,
            filtros=filtros_dict
        )
        
        if not resultados:
            return f"❌ Nenhum contrato encontrado para: '{query}'"
        
        # Formatar resposta
        resposta = [f"✅ Encontrados {len(resultados)} resultado(s) para: '{query}'\n"]
        
        for i, resultado in enumerate(resultados, 1):
            resposta.append(f"\n## 📄 Resultado {i}")
            resposta.append(f"**Score**: {resultado['score']:.2f}")
            
            if resultado.get("numero_contrato"):
                resposta.append(f"**Contrato**: {resultado['numero_contrato']}")
            if resultado.get("fornecedor"):
                resposta.append(f"**Fornecedor**: {resultado['fornecedor']}")
            if resultado.get("tipo_contrato"):
                resposta.append(f"**Tipo**: {resultado['tipo_contrato']}")
            if resultado.get("nome_arquivo"):
                resposta.append(f"**Arquivo**: {resultado['nome_arquivo']}")
            
            resposta.append(f"\n**Conteúdo relevante**:")
            conteudo = resultado.get("content", "")
            # Limitar conteúdo a 500 caracteres
            if len(conteudo) > 500:
                conteudo = conteudo[:500] + "..."
            resposta.append(conteudo)
            resposta.append("---")
        
        return "\n".join(resposta)
    
    except Exception as e:
        logger.error(f"Erro na skill buscar_contratos: {e}")
        return f"❌ Erro ao buscar contratos: {str(e)}"


def buscar_contratos_estruturado(
    query: str,
    filtros: Optional[Dict[str, Any]] = None
) -> Optional[list]:
    """Versão estruturada para uso interno.
    
    Args:
        query: Texto de busca
        filtros: Filtros opcionais
        
    Returns:
        Lista de resultados ou None se erro
    """
    try:
        resultados = search_client.buscar(
            query=query,
            top_k=5,
            filtros=filtros
        )
        return resultados
    except Exception as e:
        logger.error(f"Erro em buscar_contratos_estruturado: {e}")
        return None
