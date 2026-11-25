"""
Utilitários para processamento de PDFs e integração com Azure AI Search.
"""

from .pdf_processor import PDFProcessor
from .azure_search import AzureSearchClient
from .cache_manager import CacheManager

__all__ = [
    "PDFProcessor",
    "AzureSearchClient",
    "CacheManager",
]
