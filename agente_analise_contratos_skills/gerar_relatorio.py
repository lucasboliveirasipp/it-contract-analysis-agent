"""Skill: Gerar Relatório.

Gera relatórios consolidados sobre contratos analisados.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _to_float(val: Any) -> float:
    """Converte valor para float de forma segura (LLM/JSON pode retornar str)."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val.replace(".", "").replace(",", ".") or 0)
        except ValueError:
            return 0.0
    return 0.0


@tool
def gerar_relatorio(dados_contratos_json: str, formato: str = "markdown") -> str:
    """Gera relatório consolidado sobre contratos.
    
    Cria um relatório estruturado com informações consolidadas de um ou mais
    contratos, incluindo estatísticas, alertas e insights.
    
    Args:
        dados_contratos_json: JSON string com lista de contratos para o relatório
        formato: Formato do relatório: "markdown", "texto", "resumo"
                 (padrão: markdown)
    
    Returns:
        String com o relatório formatado
    
    Examples:
        >>> contratos = [{"numero_contrato": "001", ...}, ...]
        >>> gerar_relatorio(json.dumps(contratos), "markdown")
    """
    try:
        # Parsear contratos
        try:
            if isinstance(dados_contratos_json, str):
                contratos = json.loads(dados_contratos_json)
            else:
                contratos = dados_contratos_json
        except json.JSONDecodeError as e:
            return f"❌ Erro ao parsear contratos: {e}"
        
        # Garantir que é lista
        if not isinstance(contratos, list):
            contratos = [contratos]
        
        logger.info(f"Gerando relatório de {len(contratos)} contrato(s)...")
        
        # Gerar relatório baseado no formato
        if formato == "resumo":
            return _gerar_relatorio_resumo(contratos)
        elif formato == "texto":
            return _gerar_relatorio_texto(contratos)
        else:  # markdown (padrão)
            return _gerar_relatorio_markdown(contratos)
    
    except Exception as e:
        logger.error(f"Erro na skill gerar_relatorio: {e}")
        return f"❌ Erro ao gerar relatório: {str(e)}"


def _gerar_relatorio_markdown(contratos: List[Dict[str, Any]]) -> str:
    """Gera relatório em formato Markdown."""
    linhas = [
        "# 📊 Relatório de Contratos de TI",
        f"\n**Data de Geração**: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"**Total de Contratos**: {len(contratos)}\n",
        "---\n"
    ]
    
    # Estatísticas gerais
    linhas.append("## 📈 Estatísticas Gerais\n")
    
    tipos = {}
    valor_total = 0
    vigentes = 0
    
    for contrato in contratos:
        tipo = contrato.get("tipo_contrato", "Não especificado")
        tipos[tipo] = tipos.get(tipo, 0) + 1
        valor_total += _to_float(contrato.get("custos", {}).get("valor_total"))
        
        # Verificar se está vigente (simplificado)
        if contrato.get("vigencia", {}).get("data_termino"):
            vigentes += 1
    
    linhas.append(f"- **Valor Total**: R$ {valor_total:,.2f}")
    linhas.append(f"- **Contratos Vigentes**: {vigentes}")
    linhas.append("\n**Distribuição por Tipo**:")
    for tipo, qtd in tipos.items():
        linhas.append(f"- {tipo}: {qtd}")
    linhas.append("\n---\n")
    
    # Detalhes de cada contrato
    linhas.append("## 📄 Detalhes dos Contratos\n")
    
    for i, contrato in enumerate(contratos, 1):
        linhas.append(f"### {i}. Contrato {contrato.get('numero_contrato', 'N/A')}\n")
        
        # Fornecedor
        fornecedor = contrato.get("fornecedor", {})
        if isinstance(fornecedor, dict):
            linhas.append(f"**Fornecedor**: {fornecedor.get('razao_social', 'N/A')}")
        else:
            linhas.append(f"**Fornecedor**: {fornecedor}")
        
        # Tipo e Objeto
        linhas.append(f"**Tipo**: {contrato.get('tipo_contrato', 'N/A')}")
        if contrato.get("objeto_contrato"):
            linhas.append(f"**Objeto**: {contrato['objeto_contrato']}")
        
        # Vigência
        if contrato.get("vigencia"):
            vig = contrato["vigencia"]
            linhas.append(f"\n**Vigência**:")
            if vig.get("data_inicio"):
                linhas.append(f"- Início: {vig['data_inicio']}")
            if vig.get("data_termino"):
                linhas.append(f"- Término: {vig['data_termino']}")
        
        # Custos
        if contrato.get("custos"):
            custos = contrato["custos"]
            linhas.append(f"\n**Custos**:")
            v_total = _to_float(custos.get("valor_total"))
            if v_total:
                linhas.append(f"- Total: R$ {v_total:,.2f}")
            v_mensal = _to_float(custos.get("valor_mensal"))
            if v_mensal:
                linhas.append(f"- Mensal: R$ {v_mensal:,.2f}")
        
        linhas.append("\n---\n")
    
    # Alertas
    linhas.append("## ⚠️ Alertas e Observações\n")
    
    for contrato in contratos:
        if contrato.get("alertas"):
            numero = contrato.get("numero_contrato", "N/A")
            linhas.append(f"**Contrato {numero}**:")
            for alerta in contrato["alertas"]:
                linhas.append(f"- {alerta}")
            linhas.append("")
    
    return "\n".join(linhas)


def _gerar_relatorio_resumo(contratos: List[Dict[str, Any]]) -> str:
    """Gera relatório resumido."""
    tipos = {}
    valor_total = 0
    
    for contrato in contratos:
        tipo = contrato.get("tipo_contrato", "outro")
        tipos[tipo] = tipos.get(tipo, 0) + 1
        valor_total += _to_float(contrato.get("custos", {}).get("valor_total"))
    
    return f"""📊 Resumo de Contratos

Total: {len(contratos)} contrato(s)
Valor Total: R$ {valor_total:,.2f}

Distribuição:
{chr(10).join([f'- {tipo}: {qtd}' for tipo, qtd in tipos.items()])}
"""


def _gerar_relatorio_texto(contratos: List[Dict[str, Any]]) -> str:
    """Gera relatório em texto simples."""
    linhas = [
        "=" * 60,
        "RELATÓRIO DE CONTRATOS DE TI",
        "=" * 60,
        f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"Total de Contratos: {len(contratos)}",
        "=" * 60,
        ""
    ]
    
    for i, contrato in enumerate(contratos, 1):
        linhas.append(f"{i}. CONTRATO {contrato.get('numero_contrato', 'N/A')}")
        
        fornecedor = contrato.get("fornecedor", {})
        if isinstance(fornecedor, dict):
            linhas.append(f"   Fornecedor: {fornecedor.get('razao_social', 'N/A')}")
        
        linhas.append(f"   Tipo: {contrato.get('tipo_contrato', 'N/A')}")
        
        v = _to_float(contrato.get("custos", {}).get("valor_total"))
        if v:
            linhas.append(f"   Valor: R$ {v:,.2f}")
        
        linhas.append("")
    
    linhas.append("=" * 60)
    
    return "\n".join(linhas)
