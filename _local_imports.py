"""
Importação segura de módulos locais por caminho absoluto.

Em um hub multi-agente com Streamlit, o Python cacheia módulos
em sys.modules. Se dois agentes têm arquivos com o mesmo nome
(ex: config_constants.py), o segundo agente pode usar o módulo cacheado
do primeiro — causando ImportError ou comportamento inesperado.

Este módulo usa importlib.util para carregar sempre o arquivo LOCAL,
independente do cache de sys.modules.

Uso:
    from _local_imports import config_constants
    # ou
    from _local_imports import load_local_module
    my_module = load_local_module("meu_modulo")
"""

import importlib.util
from pathlib import Path

_AGENT_DIR = Path(__file__).resolve().parent


def load_local_module(module_name: str, subdir: str = ""):
    """Carrega um módulo .py local por caminho absoluto.

    Args:
        module_name: Nome do módulo (sem .py).
        subdir: Subdiretório relativo ao agente (ex: "nodes", "utils").

    Returns:
        O módulo carregado.
    """
    base = _AGENT_DIR / subdir if subdir else _AGENT_DIR
    module_path = base / f"{module_name}.py"

    # Nome único no namespace para evitar colisão com outros agentes
    unique_name = f"agente_analise_contratos_{subdir}.{module_name}" if subdir else f"agente_analise_contratos.{module_name}"

    spec = importlib.util.spec_from_file_location(unique_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Pré-carrega config_constants (módulo mais afetado pelo conflito de cache)
config_constants = load_local_module("config_constants")
