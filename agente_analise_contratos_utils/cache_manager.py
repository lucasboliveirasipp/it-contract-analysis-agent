"""Gerenciador de cache desabilitado.

Cache de disco foi removido. Todas as operações retornam valores padrão
sem realizar cache real.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

logger.info("⚠️ Cache de disco DESABILITADO - todas operações serão executadas sem cache")


def get_cache_key(operation: str, *args, **kwargs) -> str:
    """Gera chave de cache (placeholder - cache desabilitado).

    Args:
        operation: Nome da operação
        *args: Argumentos posicionais
        **kwargs: Argumentos nomeados

    Returns:
        String vazia (cache desabilitado)
    """
    return ""


def get_cache_manager() -> Optional[Any]:
    """Retorna instância do gerenciador de cache.

    Returns:
        None (cache desabilitado)
    """
    return None


def cache_get(key: str) -> Optional[Any]:
    """Recupera valor do cache.

    Args:
        key: Chave do cache

    Returns:
        None (cache desabilitado)
    """
    return None


def cache_set(key: str, value: Any, ttl: Optional[int] = None, cache_type: Optional[str] = None) -> bool:
    """Armazena valor no cache.

    Args:
        key: Chave do cache
        value: Valor a armazenar
        ttl: Time to live em segundos
        cache_type: Tipo de cache

    Returns:
        True (operação ignorada - cache desabilitado)
    """
    return True


def cache_clear() -> bool:
    """Limpa todo o cache.

    Returns:
        True (operação ignorada - cache desabilitado)
    """
    return True


class CacheManager:
    """Classe wrapper para gerenciamento de cache (desabilitado).

    Todas as operações retornam valores padrão sem realizar cache.
    """

    def __init__(self, cache_dir=None, **kwargs):
        """Inicializa o gerenciador de cache.

        Args:
            cache_dir: Diretório de cache (ignorado - cache desabilitado)
            **kwargs: Outros parâmetros (ignorados - compatibilidade)
        """
        self.available = False
        logger.debug("CacheManager inicializado (cache desabilitado)")

    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache.

        Args:
            key: Chave do cache

        Returns:
            None (cache desabilitado)
        """
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None, cache_type: Optional[str] = None) -> bool:
        """Armazena valor no cache.

        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Time to live em segundos
            cache_type: Tipo de cache

        Returns:
            True (operação ignorada)
        """
        return True

    def clear(self) -> bool:
        """Limpa todo o cache.

        Returns:
            True (operação ignorada)
        """
        return True

    def limpar_tudo(self) -> bool:
        """Alias para clear().

        Returns:
            True (operação ignorada)
        """
        return True

    def is_available(self) -> bool:
        """Verifica se o cache está disponível.

        Returns:
            False (cache sempre desabilitado)
        """
        return False

    # Stubs para métodos chamados pelas skills (compatibilidade)

    def carregar_cache_texto(self, path: str) -> Optional[Any]:
        return None

    def salvar_cache_texto(self, path: str, data: Any) -> bool:
        return True

    def carregar_cache_classificacao(self, texto: str) -> Optional[Any]:
        return None

    def salvar_cache_classificacao(self, texto: str, data: Any) -> bool:
        return True

    def carregar_cache_clausulas(self, key: str) -> Optional[Any]:
        return None

    def salvar_cache_clausulas(self, key: str, data: Any) -> bool:
        return True
