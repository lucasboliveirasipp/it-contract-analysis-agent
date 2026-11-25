"""Skill: Comparar Contratos.

Compara dois ou mais contratos baseado em critérios específicos.
"""

import logging
import json
from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from config import llm

logger = logging.getLogger(__name__)


@tool
def comparar_contratos(contratos_json: str, criterios: str) -> str:
    """Compara dois ou mais contratos baseado em critérios específicos.
    
    Analisa as diferenças e semelhanças entre contratos em aspectos como
    valores, vigências, SLA, cláusulas de rescisão, etc.
    
    Args:
        contratos_json: JSON string com lista de contratos a comparar.
                        Cada contrato deve ter: numero_contrato, dados estruturados
        criterios: Critérios de comparação separados por vírgula.
                   Ex: "custos", "vigencia", "SLA", "rescisao", "todos"
    
    Returns:
        String com análise comparativa detalhada
    
    Examples:
        >>> contratos = [{"numero_contrato": "001", ...}, {"numero_contrato": "002", ...}]
        >>> comparar_contratos(json.dumps(contratos), "custos,vigencia,SLA")
    """
    try:
        # Parsear contratos
        try:
            contratos = json.loads(contratos_json)
        except json.JSONDecodeError as e:
            return f"❌ Erro ao parsear contratos: {e}"
        
        if not isinstance(contratos, list) or len(contratos) < 2:
            return "❌ É necessário fornecer pelo menos 2 contratos para comparação"
        
        logger.info(f"Comparando {len(contratos)} contratos...")
        
        # Criar prompt de comparação
        system_prompt = """Você é um especialista em análise comparativa de contratos.

Sua tarefa é comparar os contratos fornecidos e identificar:
1. Diferenças significativas
2. Semelhanças importantes
3. Pontos de atenção
4. Recomendações baseadas na comparação

Seja objetivo, claro e destaque os pontos mais relevantes."""
        
        # Formatar contratos para o prompt
        contratos_texto = []
        for i, contrato in enumerate(contratos, 1):
            numero = contrato.get("numero_contrato", f"Contrato {i}")
            contratos_texto.append(f"### Contrato {i}: {numero}")
            contratos_texto.append(json.dumps(contrato, indent=2, ensure_ascii=False))
            contratos_texto.append("")
        
        user_prompt = f"""Compare os seguintes contratos focando em: {criterios}

{chr(10).join(contratos_texto)}

Forneça uma análise comparativa detalhada."""
        
        # Chamar LLM
        if not llm:
            return "❌ LLM não inicializado"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        
        return f"""✅ Análise comparativa de {len(contratos)} contratos

{response.content}
"""
    
    except Exception as e:
        logger.error(f"Erro na skill comparar_contratos: {e}")
        return f"❌ Erro ao comparar contratos: {str(e)}"
