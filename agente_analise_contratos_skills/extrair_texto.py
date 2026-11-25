"""Skill: Extrair Texto de PDF.

Extrai texto de arquivos PDF usando pdfplumber (texto nativo) ou
Azure Document Intelligence (OCR) como fallback.
"""

import logging
from pathlib import Path
from typing import Dict, Any
from langchain_core.tools import tool
import sys
from pathlib import Path
_agent_dir = Path(__file__).resolve().parent.parent
if str(_agent_dir) not in sys.path:
    sys.path.insert(0, str(_agent_dir))
from _local_imports import load_local_module
_pdf_processor_mod = load_local_module("pdf_processor", subdir="agente_analise_contratos_utils")
_cache_manager_mod = load_local_module("cache_manager", subdir="agente_analise_contratos_utils")
PDFProcessor = _pdf_processor_mod.PDFProcessor
CacheManager = _cache_manager_mod.CacheManager
from config import doc_intel_client, ENABLE_CACHE, CACHE_DIR

logger = logging.getLogger(__name__)

pdf_processor = PDFProcessor(doc_intel_client=doc_intel_client)
_cache = CacheManager(cache_dir=CACHE_DIR) if ENABLE_CACHE else None


def _formatar_resposta_extrair_texto(resultado: Dict[str, Any], metadados: Dict[str, Any]) -> str:
    """Monta a string de resposta a partir do resultado e metadados."""
    if not resultado.get("sucesso"):
        return f"❌ Erro ao extrair texto: {resultado.get('erro', 'Erro desconhecido')}"
    metodo = (resultado.get("metodo") or "nativo").upper()
    return f"""✅ Texto extraído com sucesso!

📄 **Arquivo**: {metadados.get('nome_arquivo', 'N/A')}
📊 **Páginas**: {resultado.get('num_paginas', 0)}
🔧 **Método**: {metodo}
📏 **Caracteres**: {len(resultado.get('texto', ''))}

--- TEXTO EXTRAÍDO ---

{resultado.get('texto', '')}
"""


@tool
def extrair_texto(arquivo_pdf: str) -> str:
    """Extrai texto de um arquivo PDF.
    
    Tenta primeiro extração de texto nativo. Se o PDF estiver escaneado
    ou o texto for insuficiente, usa OCR via Azure Document Intelligence.
    
    Args:
        arquivo_pdf: Caminho completo para o arquivo PDF ou nome do arquivo
                     na pasta assets/base de dados de exemplo/
    
    Returns:
        String com o texto extraído do PDF ou mensagem de erro
    
    Examples:
        >>> extrair_texto("contrato_technova.pdf")
        >>> extrair_texto("assets/base de dados de exemplo/CONTRATO CT-2025-0001.pdf")
    """
    try:
        # Resolver caminho: absoluto existente ou nome do arquivo na pasta de exemplos
        arquivo_path = Path(arquivo_pdf)
        if arquivo_path.is_absolute() and arquivo_path.exists():
            pass  # usar como está
        else:
            base_dir = Path(__file__).resolve().parent.parent
            assets_dir = base_dir / "agente_analise_contratos_assets" / "base de dados de exemplo"
            # Usar apenas o nome do arquivo para evitar path traversal
            nome_arquivo = arquivo_path.name or arquivo_pdf.strip() or "documento.pdf"
            arquivo_path = assets_dir / nome_arquivo

        if not arquivo_path.exists():
            return f"❌ Erro: Arquivo não encontrado: {arquivo_pdf}"

        path_str = str(arquivo_path.resolve())

        # Cache: retorno imediato se já tiver extraído este arquivo
        if _cache:
            cached = _cache.carregar_cache_texto(path_str)
            if cached and cached.get("sucesso"):
                metadados = cached.get("metadados") or {}
                return _formatar_resposta_extrair_texto(cached, metadados)

        logger.info(f"Extraindo texto de: {arquivo_path.name}")

        resultado = pdf_processor.extrair_texto(
            arquivo_path=path_str,
            usar_ocr_se_necessario=True
        )

        metadados = pdf_processor.extrair_metadados(path_str)
        if _cache and resultado.get("sucesso"):
            _cache.salvar_cache_texto(path_str, {**resultado, "metadados": metadados})

        return _formatar_resposta_extrair_texto(resultado, metadados)
    
    except Exception as e:
        logger.error(f"Erro na skill extrair_texto: {e}")
        return f"❌ Erro ao extrair texto: {str(e)}"


def extrair_texto_simples(arquivo_pdf: str) -> Dict[str, Any]:
    """Versão simplificada para uso interno (não é uma tool do LangChain).
    
    Retorna dict com mais informações para processamento interno.
    
    Args:
        arquivo_pdf: Caminho para o arquivo PDF
        
    Returns:
        Dict com resultado completo da extração
    """
    try:
        arquivo_path = Path(arquivo_pdf)
        if not arquivo_path.is_absolute() or not arquivo_path.exists():
            base_dir = Path(__file__).resolve().parent.parent
            assets_dir = base_dir / "agente_analise_contratos_assets" / "base de dados de exemplo"
            nome_arquivo = arquivo_path.name or arquivo_pdf.strip() or "documento.pdf"
            arquivo_path = assets_dir / nome_arquivo

        resultado = pdf_processor.extrair_texto(
            arquivo_path=str(arquivo_path),
            usar_ocr_se_necessario=True
        )
        
        metadados = pdf_processor.extrair_metadados(str(arquivo_path))
        
        return {
            **resultado,
            "metadados": metadados
        }
    
    except Exception as e:
        logger.error(f"Erro em extrair_texto_simples: {e}")
        return {
            "texto": "",
            "metodo": None,
            "num_paginas": 0,
            "sucesso": False,
            "erro": str(e),
            "metadados": {}
        }
