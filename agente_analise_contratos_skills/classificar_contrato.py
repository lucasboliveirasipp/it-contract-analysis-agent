"""Skill: Classificar Contrato.

Classifica o tipo do contrato (software, hardware, serviços, mão de obra, etc.)
usando LLM com extração estruturada.
"""

import logging
import json
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from config import llm, ENABLE_CACHE, CACHE_DIR
from agente_analise_contratos_prompts.classifier_prompt import CLASSIFIER_PROMPT
from agente_analise_contratos_schemas.contract_schemas import ClassificacaoContrato
import sys
from pathlib import Path
_agent_dir = Path(__file__).resolve().parent.parent
if str(_agent_dir) not in sys.path:
    sys.path.insert(0, str(_agent_dir))
from _local_imports import load_local_module
CacheManager = load_local_module("cache_manager", subdir="agente_analise_contratos_utils").CacheManager

logger = logging.getLogger(__name__)
_cache = CacheManager(cache_dir=CACHE_DIR) if ENABLE_CACHE else None


def _formatar_classificacao(d: Dict[str, Any]) -> str:
    """Monta a string de resposta a partir do dict de classificação."""
    tipo = d.get("tipo_contrato", "outro")
    if hasattr(tipo, "value"):
        tipo = tipo.value
    tipo_display = str(tipo).upper().replace("_", " ")
    confianca_pct = float(d.get("confianca", 0)) * 100
    justificativa = d.get("justificativa", "")
    palavras = d.get("palavras_chave") or []
    return f"""✅ Contrato classificado com sucesso!

📋 **Tipo de Contrato**: {tipo_display}
📊 **Confiança**: {confianca_pct:.1f}%

💡 **Justificativa**:
{justificativa}

🔑 **Palavras-chave identificadas**:
{', '.join(palavras)}
"""


@tool
def classificar_contrato(texto_contrato: str) -> str:
    """Classifica o tipo de um contrato baseado em seu conteúdo.
    
    Analisa o texto do contrato e determina se é de software, hardware,
    serviços, mão de obra, híbrido ou outro tipo.
    
    Args:
        texto_contrato: Texto completo ou trecho relevante do contrato.
                        Pode ser o texto extraído de um PDF ou digitado.
    
    Returns:
        String com a classificação detalhada do contrato em formato legível
    
    Examples:
        >>> classificar_contrato("CONTRATO DE LICENÇA DE USO DE SOFTWARE...")
        >>> classificar_contrato(texto_extraido)
    """
    try:
        if not texto_contrato or len(texto_contrato.strip()) < 50:
            return "❌ Erro: Texto do contrato muito curto. Forneça um texto com pelo menos 50 caracteres."
        
        logger.info("Classificando contrato...")
        
        # Limitar tamanho do texto para não exceder limite de tokens
        # Usar as primeiras 8000 palavras (~30k tokens) que geralmente é suficiente
        palavras = texto_contrato.split()
        if len(palavras) > 8000:
            texto_resumido = " ".join(palavras[:8000]) + "\n\n[... texto truncado ...]"
            logger.warning(f"Texto truncado de {len(palavras)} para 8000 palavras")
        else:
            texto_resumido = texto_contrato

        # Cache: retorno imediato se já classificou este texto
        if _cache:
            cached = _cache.carregar_cache_classificacao(texto_resumido)
            if cached:
                return _formatar_classificacao(cached)

        # Criar prompt
        messages = [
            SystemMessage(content=CLASSIFIER_PROMPT),
            HumanMessage(content=f"Classifique o seguinte contrato:\n\n{texto_resumido}")
        ]
        
        # Chamar LLM
        if not llm:
            return "❌ Erro: LLM não inicializado. Verifique as configurações."
        
        response = llm.invoke(messages)
        resposta_texto = response.content
        
        # Extrair JSON da resposta
        try:
            # Tentar encontrar JSON na resposta
            inicio_json = resposta_texto.find('{')
            fim_json = resposta_texto.rfind('}') + 1
            
            if inicio_json >= 0 and fim_json > inicio_json:
                json_str = resposta_texto[inicio_json:fim_json]
                resultado = json.loads(json_str)
                
                classificacao = ClassificacaoContrato(**resultado)
                cache_dict = {
                    "tipo_contrato": classificacao.tipo_contrato.value,
                    "confianca": classificacao.confianca,
                    "justificativa": classificacao.justificativa,
                    "palavras_chave": classificacao.palavras_chave,
                }
                if _cache:
                    _cache.salvar_cache_classificacao(texto_resumido, cache_dict)
                return _formatar_classificacao(cache_dict)
            else:
                # Se não encontrou JSON, retornar resposta texto
                return f"⚠️ Classificação realizada (sem estruturação):\n\n{resposta_texto}"
        
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON: {e}")
            return f"⚠️ Classificação realizada mas houve erro ao estruturar a resposta:\n\n{resposta_texto}"
    
    except Exception as e:
        logger.error(f"Erro na skill classificar_contrato: {e}")
        return f"❌ Erro ao classificar contrato: {str(e)}"


def classificar_contrato_estruturado(texto_contrato: str) -> Dict[str, Any]:
    """Versão estruturada para uso interno (não é uma tool do LangChain).
    
    Retorna dict com classificação estruturada para processamento interno.
    
    Args:
        texto_contrato: Texto do contrato
        
    Returns:
        Dict com classificação estruturada ou None se houver erro
    """
    try:
        if not texto_contrato or len(texto_contrato.strip()) < 50:
            return None
        
        # Limitar tamanho do texto
        palavras = texto_contrato.split()
        if len(palavras) > 8000:
            texto_resumido = " ".join(palavras[:8000])
        else:
            texto_resumido = texto_contrato
        
        # Criar prompt
        messages = [
            SystemMessage(content=CLASSIFIER_PROMPT),
            HumanMessage(content=f"Classifique o seguinte contrato:\n\n{texto_resumido}")
        ]
        
        # Chamar LLM
        if not llm:
            return None
        
        response = llm.invoke(messages)
        resposta_texto = response.content
        
        # Extrair JSON
        inicio_json = resposta_texto.find('{')
        fim_json = resposta_texto.rfind('}') + 1
        
        if inicio_json >= 0 and fim_json > inicio_json:
            json_str = resposta_texto[inicio_json:fim_json]
            resultado = json.loads(json_str)
            
            # Validar com Pydantic
            classificacao = ClassificacaoContrato(**resultado)
            
            return {
                "tipo_contrato": classificacao.tipo_contrato.value,
                "confianca": classificacao.confianca,
                "justificativa": classificacao.justificativa,
                "palavras_chave": classificacao.palavras_chave
            }
        
        return None
    
    except Exception as e:
        logger.error(f"Erro em classificar_contrato_estruturado: {e}")
        return None
