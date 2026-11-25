"""Constantes de configuração do Agente de Análise de Contratos.

Separado de config.py para manter segredos e constantes em arquivos distintos.
"""

# ============================================================================
# CHUNKING E INDEXAÇÃO
# ============================================================================

# Tamanho dos chunks para indexação vetorial
CHUNK_SIZE = 4000

# Overlap entre chunks para manter contexto
CHUNK_OVERLAP = 400

# Tamanho do lote para upload ao Azure
BATCH_SIZE = 20

# Limite de armazenamento (GB)
STORAGE_LIMIT_GB = 15.0

# Limites de upload
UPLOAD_LIMIT_FILES = 10
UPLOAD_LIMIT_MB = 50

# ============================================================================
# BUSCA E RETRIEVAL
# ============================================================================

# Número de documentos retornados em buscas
SEARCH_TOP_K = 5

# Score mínimo para considerar resultado relevante (0-1)
SEARCH_SCORE_THRESHOLD = 0.7

# ============================================================================
# LLM E RETRIES
# ============================================================================

# Número máximo de tentativas em caso de falha
LLM_MAX_RETRIES = 4

# Timeout para chamadas LLM (segundos)
LLM_TIMEOUT = 90

# Fator de backoff exponencial para retries
RETRY_BACKOFF_FACTOR = 2

# ============================================================================
# REACT AGENT
# ============================================================================

# Máximo de steps para prevenir loops infinitos
MAX_AGENT_STEPS = 10

# Timeout para execução completa do agente (segundos)
AGENT_TIMEOUT = 300

# ============================================================================
# CACHE
# ============================================================================

# Habilitar cache de operações caras
ENABLE_CACHE = False

# Diretório para armazenar cache
CACHE_DIR = ".cache"

# TTL do cache em segundos (24 horas)
CACHE_TTL_SECONDS = 86400

# ============================================================================
# LOGGING E DEBUG
# ============================================================================

# Nível de log padrão
LOG_LEVEL = "INFO"

# Modo debug (logs verbosos)
DEBUG = False

# ============================================================================
# LIMITES E VALIDAÇÃO
# ============================================================================

# Tamanho máximo de arquivo PDF (MB)
MAX_PDF_SIZE_MB = 50

# Tamanho máximo de texto para processamento (caracteres)
MAX_TEXT_LENGTH = 100000

# Número máximo de contratos para comparação simultânea
MAX_CONTRACTS_COMPARISON = 5
