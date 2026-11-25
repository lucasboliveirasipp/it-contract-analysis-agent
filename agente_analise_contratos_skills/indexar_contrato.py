"""Skill: Indexar Contrato.

Indexa um contrato processado no Azure AI Search para busca posterior.
"""

import logging
import json
from typing import Dict, Any
from langchain_core.tools import tool
import sys
from pathlib import Path
_agent_dir = Path(__file__).resolve().parent.parent
if str(_agent_dir) not in sys.path:
    sys.path.insert(0, str(_agent_dir))
from _local_imports import load_local_module
AzureSearchClient = load_local_module("azure_search", subdir="agente_analise_contratos_utils").AzureSearchClient

logger = logging.getLogger(__name__)

# Instanciar cliente
search_client = AzureSearchClient()


@tool
def indexar_contrato(dados_contrato_json: str, texto_completo: str) -> str:
    """Indexa um contrato no Azure AI Search.
    
    Recebe os dados estruturados de um contrato e seu texto completo,
    divide em chunks, gera embeddings e indexa para busca semântica.
    
    Args:
        dados_contrato_json: JSON string com dados estruturados do contrato.
                             Deve incluir: numero_contrato, tipo_contrato,
                             fornecedor, vigencia, custos, etc.
        texto_completo: Texto completo do contrato extraído
    
    Returns:
        String confirmando indexação ou erro
    
    Examples:
        >>> dados = {"numero_contrato": "CT-2025-0001", "tipo_contrato": "software", ...}
        >>> indexar_contrato(json.dumps(dados), texto_completo)
    """
    try:
        # Parsear JSON
        try:
            dados_contrato = json.loads(dados_contrato_json)
        except json.JSONDecodeError as e:
            return f"❌ Erro ao parsear dados do contrato: {e}"
        
        if not texto_completo or len(texto_completo) < 100:
            return "❌ Texto do contrato muito curto para indexar"
        
        logger.info(f"Indexando contrato: {dados_contrato.get('numero_contrato', 'sem número')}")
        
        # Indexar
        sucesso = search_client.indexar_contrato(
            dados_contrato=dados_contrato,
            texto_completo=texto_completo
        )
        
        if sucesso:
            numero = dados_contrato.get("numero_contrato", "N/A")
            fornecedor = dados_contrato.get("fornecedor", {})
            if isinstance(fornecedor, dict):
                fornecedor = fornecedor.get("razao_social", "N/A")
            
            return f"""✅ Contrato indexado com sucesso!

📋 **Número**: {numero}
🏢 **Fornecedor**: {fornecedor}
📊 **Tipo**: {dados_contrato.get('tipo_contrato', 'N/A')}

O contrato agora está disponível para busca semântica.
"""
        else:
            return "❌ Erro ao indexar contrato. Verifique os logs."
    
    except Exception as e:
        logger.error(f"Erro na skill indexar_contrato: {e}")
        return f"❌ Erro ao indexar contrato: {str(e)}"
