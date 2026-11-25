"""Configurações Azure OpenAI, Document Intelligence e AI Search.

Todas as credenciais vêm de variáveis de ambiente (arquivo .env na raiz do
agente). Veja .env.example para a lista completa.
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from _local_imports import config_constants

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

LLM_MAX_RETRIES = config_constants.LLM_MAX_RETRIES
LLM_TIMEOUT = config_constants.LLM_TIMEOUT

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Reduzir ruído nos logs
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdffont").setLevel(logging.ERROR)

# Proxy: não há configuração fixa. Se a sua rede exigir, defina HTTP_PROXY /
# HTTPS_PROXY / NO_PROXY no .env — as bibliotecas HTTP leem essas variáveis.


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# Azure OpenAI - LLM Principal
AZURE_OPENAI_ENDPOINT = _env("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = _env("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = _env("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
OPENAI_API_VERSION = _env("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

# Azure OpenAI Embeddings (por padrão usa o mesmo recurso do LLM)
AZURE_EMBEDDINGS_ENDPOINT = _env("AZURE_EMBEDDINGS_ENDPOINT", AZURE_OPENAI_ENDPOINT)
AZURE_EMBEDDINGS_KEY = _env("AZURE_EMBEDDINGS_API_KEY", AZURE_OPENAI_KEY)
AZURE_EMBEDDINGS_DEPLOYMENT = _env("AZURE_EMBEDDINGS_DEPLOYMENT", "text-embedding-ada-002")
AZURE_EMBEDDINGS_API_VERSION = _env("AZURE_EMBEDDINGS_API_VERSION", "2023-05-15")

# Azure Document Intelligence - OCR
AZURE_DOC_INTEL_ENDPOINT = _env("AZURE_DOC_INTEL_ENDPOINT")
AZURE_DOC_INTEL_KEY = _env("AZURE_DOC_INTEL_KEY")
AZURE_DOC_INTEL_API_VERSION = _env("AZURE_DOC_INTEL_API_VERSION", "2024-02-29-preview")

# Azure AI Search
AZURE_SEARCH_ENDPOINT = _env("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = _env("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = _env("AZURE_SEARCH_INDEX", "contratos-ti")
AZURE_SEARCH_API_VERSION = _env("AZURE_SEARCH_API_VERSION", "2024-05-01-preview")

# Expor credenciais com os nomes que ingest.py espera
os.environ.setdefault("ENDPOINT_DOC", AZURE_DOC_INTEL_ENDPOINT)
os.environ.setdefault("KEY_DOC", AZURE_DOC_INTEL_KEY)
os.environ.setdefault("ENDPOINT_SEARCH", AZURE_SEARCH_ENDPOINT)
os.environ.setdefault("KEY_SEARCH", AZURE_SEARCH_KEY)
os.environ.setdefault("INDEX_NAME", AZURE_SEARCH_INDEX)

# --- LLM ---
logger.info("🔧 Inicializando Azure OpenAI LLM (deployment: %s)", AZURE_OPENAI_DEPLOYMENT)
llm = None
if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY:
    try:
        llm = AzureChatOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            azure_deployment=AZURE_OPENAI_DEPLOYMENT,
            api_version=OPENAI_API_VERSION,
            temperature=0,
            max_retries=LLM_MAX_RETRIES,
            timeout=LLM_TIMEOUT,
        )
        logger.info("✅ Azure OpenAI LLM configurado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Azure OpenAI: {e}", exc_info=True)
else:
    logger.warning("⚠️ AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY não definidos no .env")

# --- Document Intelligence ---
doc_intel_client = None
if AZURE_DOC_INTEL_ENDPOINT and AZURE_DOC_INTEL_KEY:
    try:
        doc_intel_client = DocumentIntelligenceClient(
            endpoint=AZURE_DOC_INTEL_ENDPOINT,
            credential=AzureKeyCredential(AZURE_DOC_INTEL_KEY),
            api_version=AZURE_DOC_INTEL_API_VERSION,
        )
        logger.info("✅ Azure Document Intelligence configurado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Document Intelligence: {e}", exc_info=True)
else:
    logger.warning("⚠️ Document Intelligence não configurado - PDFs escaneados (OCR) não funcionarão")

# --- Embeddings ---
embeddings = None
if AZURE_EMBEDDINGS_ENDPOINT and AZURE_EMBEDDINGS_KEY:
    try:
        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=AZURE_EMBEDDINGS_ENDPOINT,
            api_key=AZURE_EMBEDDINGS_KEY,
            azure_deployment=AZURE_EMBEDDINGS_DEPLOYMENT,
            api_version=AZURE_EMBEDDINGS_API_VERSION,
            chunk_size=1000,
        )
        logger.info("✅ Azure OpenAI Embeddings configurado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Embeddings: {e}", exc_info=True)

# --- AI Search (opcional nas páginas atuais) ---
search_client = None
if AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY:
    try:
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(AZURE_SEARCH_KEY),
        )
        logger.info("✅ Azure AI Search configurado (índice: %s)", AZURE_SEARCH_INDEX)
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Azure AI Search: {e}", exc_info=True)
else:
    logger.info("ℹ️ Azure AI Search não configurado (opcional)")

# Configurações gerais
FILES_DIR = BASE_DIR / "agente_analise_contratos_assets" / "uploads"
OUTPUT_DIR = BASE_DIR / "output"

FILES_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Importar constantes
CHUNK_SIZE = config_constants.CHUNK_SIZE
CHUNK_OVERLAP = config_constants.CHUNK_OVERLAP
SEARCH_TOP_K = config_constants.SEARCH_TOP_K
SEARCH_SCORE_THRESHOLD = config_constants.SEARCH_SCORE_THRESHOLD
ENABLE_CACHE = config_constants.ENABLE_CACHE
CACHE_DIR = config_constants.CACHE_DIR
DEBUG = config_constants.DEBUG

logger.info(
    "📊 Serviços: LLM=%s | DocIntel=%s | Embeddings=%s | Search=%s",
    "OK" if llm else "FALHOU",
    "OK" if doc_intel_client else "-",
    "OK" if embeddings else "-",
    "OK" if search_client else "-",
)
if not llm:
    logger.error("❌ LLM não inicializado - o agente NÃO funcionará! Preencha o .env.")
