"""
Skills do Agente de Análise de Contratos.

Cada skill é uma ferramenta especializada que pode ser invocada pelo agente.
"""

from .extrair_texto import extrair_texto
from .classificar_contrato import classificar_contrato
from .extrair_clausulas import extrair_clausulas
from .buscar_contratos import buscar_contratos
from .comparar_contratos import comparar_contratos
from .gerar_relatorio import gerar_relatorio
from .indexar_contrato import indexar_contrato

__all__ = [
    "extrair_texto",
    "classificar_contrato",
    "extrair_clausulas",
    "buscar_contratos",
    "comparar_contratos",
    "gerar_relatorio",
    "indexar_contrato",
]
