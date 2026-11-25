"""Skill: Extrair Cláusulas.

Extrai cláusulas estruturadas de contratos usando LLM com validação Pydantic.
"""

import logging
import json
from typing import Any, Dict, Optional
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from config import llm, ENABLE_CACHE, CACHE_DIR
from agente_analise_contratos_prompts.mapper_prompt import MAPPER_PROMPT
from agente_analise_contratos_schemas.contract_schemas import ContratoCompleto
import sys
from pathlib import Path
_agent_dir = Path(__file__).resolve().parent.parent
if str(_agent_dir) not in sys.path:
    sys.path.insert(0, str(_agent_dir))
from _local_imports import load_local_module
CacheManager = load_local_module("cache_manager", subdir="agente_analise_contratos_utils").CacheManager

logger = logging.getLogger(__name__)
_cache = CacheManager(cache_dir=CACHE_DIR) if ENABLE_CACHE else None


def _valor_numero(val: Any) -> float:
    """Converte valor para float de forma segura (LLM pode retornar str)."""
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
def extrair_clausulas(texto_contrato: str, tipo_clausula: Optional[str] = None) -> str:
    """Extrai cláusulas estruturadas de um contrato.
    
    Analisa o texto do contrato e extrai informações estruturadas como:
    - Dados gerais (número, tipo, objeto)
    - Fornecedor (razão social, CNPJ, contatos)
    - Licenciamento (tipo, quantidade, restrições)
    - Vigência (datas, renovação, rescisão)
    - Custos (valores, reajustes, multas)
    - Suporte e SLA
    - Compliance e LGPD
    - Obrigações legais
    
    Args:
        texto_contrato: Texto completo do contrato
        tipo_clausula: (Opcional) Tipo específico de cláusula a extrair:
                       "licenciamento", "vigencia", "custos", "sla", 
                       "lgpd", "legal". Se não especificado, extrai tudo.
    
    Returns:
        String com as cláusulas extraídas em formato estruturado e legível
    
    Examples:
        >>> extrair_clausulas(texto_contrato)
        >>> extrair_clausulas(texto_contrato, "vigencia")
        >>> extrair_clausulas(texto_contrato, "custos")
    """
    try:
        if not texto_contrato or len(texto_contrato.strip()) < 100:
            return "❌ Erro: Texto do contrato muito curto. Forneça um texto mais completo."
        
        logger.info(f"Extraindo cláusulas do contrato... (tipo: {tipo_clausula or 'todas'})")
        
        # Limitar tamanho do texto
        palavras = texto_contrato.split()
        if len(palavras) > 10000:
            texto_resumido = " ".join(palavras[:10000]) + "\n\n[... texto truncado ...]"
            logger.warning(f"Texto truncado de {len(palavras)} para 10000 palavras")
        else:
            texto_resumido = texto_contrato

        # Cache: chave inclui tipo_clausula para diferenciar extrações parciais (< 5000 chars para o hash)
        cache_key = texto_resumido[:4000] + "|" + (tipo_clausula or "todas")
        if _cache:
            cached = _cache.carregar_cache_clausulas(cache_key)
            if cached:
                return _formatar_clausulas_extraidas(cached, tipo_clausula)

        # Criar prompt personalizado se tipo específico
        prompt_base = MAPPER_PROMPT
        if tipo_clausula:
            prompt_base += f"\n\n**IMPORTANTE**: Foque especialmente na extração de informações relacionadas a: {tipo_clausula.upper()}"
        
        # Criar messages
        messages = [
            SystemMessage(content=prompt_base),
            HumanMessage(content=f"Extraia as cláusulas estruturadas do seguinte contrato:\n\n{texto_resumido}")
        ]
        
        # Chamar LLM
        if not llm:
            return "❌ Erro: LLM não inicializado. Verifique as configurações."
        
        response = llm.invoke(messages)
        resposta_texto = response.content
        
        # Extrair JSON da resposta
        try:
            inicio_json = resposta_texto.find('{')
            fim_json = resposta_texto.rfind('}') + 1
            
            if inicio_json >= 0 and fim_json > inicio_json:
                json_str = resposta_texto[inicio_json:fim_json]
                dados = json.loads(json_str)
                if _cache:
                    _cache.salvar_cache_clausulas(cache_key, dados)
                return _formatar_clausulas_extraidas(dados, tipo_clausula)
            else:
                return f"⚠️ Cláusulas extraídas (sem estruturação completa):\n\n{resposta_texto}"
        
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON: {e}")
            return f"⚠️ Cláusulas extraídas mas houve erro ao estruturar:\n\n{resposta_texto}"
    
    except Exception as e:
        logger.error(f"Erro na skill extrair_clausulas: {e}")
        return f"❌ Erro ao extrair cláusulas: {str(e)}"


def extrair_clausulas_estruturado(texto_contrato: str) -> Optional[Dict[str, Any]]:
    """Versão estruturada para uso interno (não é uma tool do LangChain).
    
    Retorna dict com dados estruturados para processamento interno.
    
    Args:
        texto_contrato: Texto do contrato
        
    Returns:
        Dict com dados extraídos ou None se houver erro
    """
    try:
        if not texto_contrato or len(texto_contrato.strip()) < 100:
            return None
        
        # Limitar tamanho
        palavras = texto_contrato.split()
        if len(palavras) > 10000:
            texto_resumido = " ".join(palavras[:10000])
        else:
            texto_resumido = texto_contrato
        
        # Criar messages
        messages = [
            SystemMessage(content=MAPPER_PROMPT),
            HumanMessage(content=f"Extraia as cláusulas estruturadas do seguinte contrato:\n\n{texto_resumido}")
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
            dados = json.loads(json_str)
            return dados
        
        return None
    
    except Exception as e:
        logger.error(f"Erro em extrair_clausulas_estruturado: {e}")
        return None


def _formatar_clausulas_extraidas(dados: Dict[str, Any], tipo_filtro: Optional[str] = None) -> str:
    """Formata os dados extraídos em texto legível.
    
    Args:
        dados: Dicionário com dados extraídos
        tipo_filtro: Filtrar apenas seção específica
        
    Returns:
        String formatada
    """
    linhas = ["✅ Cláusulas extraídas com sucesso!", ""]
    
    # Dados Gerais
    if not tipo_filtro or tipo_filtro in ["geral", "dados"]:
        linhas.append("## 📋 DADOS GERAIS")
        if dados.get("numero_contrato"):
            linhas.append(f"- **Número**: {dados['numero_contrato']}")
        if dados.get("tipo_contrato"):
            linhas.append(f"- **Tipo**: {dados['tipo_contrato']}")
        if dados.get("objeto_contrato"):
            linhas.append(f"- **Objeto**: {dados['objeto_contrato']}")
        linhas.append("")
    
    # Fornecedor
    if not tipo_filtro or tipo_filtro == "fornecedor":
        if dados.get("fornecedor"):
            linhas.append("## 🏢 FORNECEDOR")
            fornecedor = dados["fornecedor"]
            if fornecedor.get("razao_social"):
                linhas.append(f"- **Razão Social**: {fornecedor['razao_social']}")
            if fornecedor.get("cnpj"):
                linhas.append(f"- **CNPJ**: {fornecedor['cnpj']}")
            if fornecedor.get("contato_email"):
                linhas.append(f"- **Email**: {fornecedor['contato_email']}")
            linhas.append("")
    
    # Licenciamento
    if not tipo_filtro or tipo_filtro == "licenciamento":
        if dados.get("licenciamento"):
            linhas.append("## 📦 LICENCIAMENTO")
            lic = dados["licenciamento"]
            if lic.get("tipo_licenca"):
                linhas.append(f"- **Tipo de Licença**: {lic['tipo_licenca']}")
            if lic.get("quantidade_licencas"):
                linhas.append(f"- **Quantidade**: {lic['quantidade_licencas']}")
            if lic.get("restricoes_uso"):
                linhas.append(f"- **Restrições**: {lic['restricoes_uso']}")
            linhas.append("")
    
    # Vigência
    if not tipo_filtro or tipo_filtro == "vigencia":
        if dados.get("vigencia"):
            linhas.append("## 📅 VIGÊNCIA")
            vig = dados["vigencia"]
            if vig.get("data_inicio"):
                linhas.append(f"- **Início**: {vig['data_inicio']}")
            if vig.get("data_termino"):
                linhas.append(f"- **Término**: {vig['data_termino']}")
            if vig.get("prazo_meses"):
                linhas.append(f"- **Prazo**: {vig['prazo_meses']} meses")
            if vig.get("renovacao_automatica") is not None:
                linhas.append(f"- **Renovação Automática**: {'Sim' if vig['renovacao_automatica'] else 'Não'}")
            linhas.append("")
    
    # Custos
    if not tipo_filtro or tipo_filtro == "custos":
        if dados.get("custos"):
            linhas.append("## 💰 CUSTOS")
            custos = dados["custos"]
            v_total = _valor_numero(custos.get("valor_total"))
            if v_total:
                linhas.append(f"- **Valor Total**: R$ {v_total:,.2f}")
            v_mensal = _valor_numero(custos.get("valor_mensal"))
            if v_mensal:
                linhas.append(f"- **Valor Mensal**: R$ {v_mensal:,.2f}")
            v_anual = _valor_numero(custos.get("valor_anual"))
            if v_anual:
                linhas.append(f"- **Valor Anual**: R$ {v_anual:,.2f}")
            if custos.get("forma_pagamento"):
                linhas.append(f"- **Forma de Pagamento**: {custos['forma_pagamento']}")
            if custos.get("indice_reajuste"):
                linhas.append(f"- **Índice de Reajuste**: {custos['indice_reajuste']}")
            linhas.append("")
    
    # SLA
    if not tipo_filtro or tipo_filtro == "sla":
        if dados.get("suporte_sla"):
            linhas.append("## 🛠️ SUPORTE E SLA")
            sla = dados["suporte_sla"]
            if sla.get("niveis_suporte"):
                linhas.append(f"- **Níveis de Suporte**: {sla['niveis_suporte']}")
            if sla.get("tempo_resposta_sla"):
                linhas.append(f"- **Tempo de Resposta**: {sla['tempo_resposta_sla']}")
            if sla.get("disponibilidade_garantida"):
                linhas.append(f"- **Disponibilidade**: {sla['disponibilidade_garantida']}")
            linhas.append("")
    
    # LGPD
    if not tipo_filtro or tipo_filtro == "lgpd":
        if dados.get("compliance_lgpd"):
            linhas.append("## 🔒 COMPLIANCE E LGPD")
            lgpd = dados["compliance_lgpd"]
            if lgpd.get("clausulas_lgpd"):
                linhas.append(f"- **Cláusulas LGPD**: {lgpd['clausulas_lgpd']}")
            if lgpd.get("tratamento_dados_pessoais"):
                linhas.append(f"- **Tratamento de Dados**: {lgpd['tratamento_dados_pessoais']}")
            if lgpd.get("direito_auditoria") is not None:
                linhas.append(f"- **Direito de Auditoria**: {'Sim' if lgpd['direito_auditoria'] else 'Não'}")
            linhas.append("")
    
    # Obrigações Legais
    if not tipo_filtro or tipo_filtro == "legal":
        if dados.get("obrigacoes_legais"):
            linhas.append("## ⚖️ OBRIGAÇÕES LEGAIS")
            legal = dados["obrigacoes_legais"]
            if legal.get("foro_jurisdicao"):
                linhas.append(f"- **Foro**: {legal['foro_jurisdicao']}")
            if legal.get("lei_aplicavel"):
                linhas.append(f"- **Lei Aplicável**: {legal['lei_aplicavel']}")
            linhas.append("")
    
    # Observações
    if dados.get("observacoes"):
        linhas.append("## 📝 OBSERVAÇÕES")
        linhas.append(dados["observacoes"])
        linhas.append("")
    
    return "\n".join(linhas)
