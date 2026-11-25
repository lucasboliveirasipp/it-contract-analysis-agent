"""Utilitários para integração com Azure AI Search.

Gerencia criação de índice, indexação de contratos e busca semântica.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

try:
    from azure.search.documents.models import VectorizedQuery as VectorQuery
    _VECTOR_QUERY_AVAILABLE = True
except ImportError:
    VectorQuery = None
    _VECTOR_QUERY_AVAILABLE = False
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.core.credentials import AzureKeyCredential
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_KEY,
    AZURE_SEARCH_INDEX,
    embeddings,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

logger = logging.getLogger(__name__)


class AzureSearchClient:
    """Cliente para gerenciar operações no Azure AI Search."""
    
    def __init__(
        self,
        endpoint: str = AZURE_SEARCH_ENDPOINT,
        api_key: str = AZURE_SEARCH_KEY,
        index_name: str = AZURE_SEARCH_INDEX
    ):
        """Inicializa o cliente Azure Search.
        
        Args:
            endpoint: Endpoint do Azure Search
            api_key: Chave de API
            index_name: Nome do índice
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_name = index_name
        self.credential = AzureKeyCredential(api_key) if api_key else None
        
        # Clientes
        self.index_client = None
        self.search_client = None
        
        if self.credential:
            self.index_client = SearchIndexClient(
                endpoint=endpoint,
                credential=self.credential
            )
            self.search_client = SearchClient(
                endpoint=endpoint,
                index_name=index_name,
                credential=self.credential
            )
        
        # Text splitter para chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def criar_indice(self, sobrescrever: bool = False) -> bool:
        """Cria o índice no Azure AI Search.
        
        Args:
            sobrescrever: Se True, deleta índice existente antes de criar
            
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.index_client:
            logger.error("Index client não inicializado")
            return False
        
        try:
            # Verificar se índice já existe
            try:
                self.index_client.get_index(self.index_name)
                logger.info(f"Índice '{self.index_name}' já existe")
                
                if sobrescrever:
                    logger.info(f"Deletando índice existente '{self.index_name}'")
                    self.index_client.delete_index(self.index_name)
                else:
                    return True
            except:
                pass
            
            # Definir campos do índice
            fields = [
                SimpleField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True
                ),
                SimpleField(
                    name="chunk_id",
                    type=SearchFieldDataType.String,
                    filterable=True
                ),
                SearchableField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True
                ),
                SearchField(
                    name="contentVector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="default-profile"
                ),
                SearchableField(
                    name="numero_contrato",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True
                ),
                SearchableField(
                    name="fornecedor",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True
                ),
                SimpleField(
                    name="tipo_contrato",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True
                ),
                SimpleField(
                    name="data_inicio",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True
                ),
                SimpleField(
                    name="data_termino",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True
                ),
                SimpleField(
                    name="valor_total",
                    type=SearchFieldDataType.Double,
                    filterable=True,
                    sortable=True
                ),
                SearchableField(
                    name="nome_arquivo",
                    type=SearchFieldDataType.String,
                    filterable=True
                ),
                SimpleField(
                    name="data_indexacao",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True
                ),
                SearchableField(
                    name="metadados",
                    type=SearchFieldDataType.String
                )
            ]
            
            # Configurar Vector Search
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="default-profile",
                        algorithm_configuration_name="default-config"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(name="default-config")
                ]
            )
            
            # Criar índice
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            self.index_client.create_index(index)
            logger.info(f"✅ Índice '{self.index_name}' criado com sucesso")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erro ao criar índice: {e}")
            return False
    
    def indexar_contrato(
        self,
        dados_contrato: Dict[str, Any],
        texto_completo: str
    ) -> bool:
        """Indexa um contrato no Azure AI Search.
        
        Args:
            dados_contrato: Dicionário com dados estruturados do contrato
            texto_completo: Texto completo do contrato
            
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.search_client:
            logger.error("Search client não inicializado")
            return False
        
        try:
            # Gerar chunks
            chunks = self.text_splitter.split_text(texto_completo)
            logger.info(f"Texto dividido em {len(chunks)} chunks")
            
            # Gerar embeddings
            if not embeddings:
                logger.error("Embeddings não inicializados")
                return False
            
            embeddings_vectors = embeddings.embed_documents(chunks)
            
            # Preparar documentos para indexação
            documentos = []
            id_base = dados_contrato.get("id_documento") or str(uuid.uuid4())
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_vectors)):
                doc = {
                    "id": f"{id_base}_chunk_{i}",
                    "chunk_id": f"chunk_{i}",
                    "content": chunk,
                    "contentVector": embedding,
                    "numero_contrato": dados_contrato.get("numero_contrato"),
                    "fornecedor": self._extrair_fornecedor(dados_contrato),
                    "tipo_contrato": dados_contrato.get("tipo_contrato"),
                    "data_inicio": self._formatar_data(dados_contrato.get("vigencia", {}).get("data_inicio")),
                    "data_termino": self._formatar_data(dados_contrato.get("vigencia", {}).get("data_termino")),
                    "valor_total": dados_contrato.get("custos", {}).get("valor_total"),
                    "nome_arquivo": dados_contrato.get("nome_arquivo"),
                    "data_indexacao": datetime.utcnow().isoformat() + "Z",
                    "metadados": str(dados_contrato)
                }
                documentos.append(doc)
            
            # Upload documents
            result = self.search_client.upload_documents(documents=documentos)
            
            sucesso = all([r.succeeded for r in result])
            if sucesso:
                logger.info(f"✅ Contrato indexado com sucesso: {len(documentos)} chunks")
            else:
                logger.error(f"❌ Erro ao indexar alguns chunks")
            
            return sucesso
        
        except Exception as e:
            logger.error(f"❌ Erro ao indexar contrato: {e}")
            return False
    
    def buscar(
        self,
        query: str,
        top_k: int = 5,
        filtros: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Busca semântica no índice.
        
        Args:
            query: Texto de busca
            top_k: Número de resultados
            filtros: Filtros opcionais (tipo_contrato, fornecedor, etc)
            
        Returns:
            Lista de resultados
        """
        if not self.search_client:
            logger.error("Search client não inicializado (configure AZURE_SEARCH_KEY)")
            return []
        
        try:
            # Construir filtro
            filter_expression = None
            if filtros:
                filter_parts = []
                if filtros.get("tipo_contrato"):
                    filter_parts.append(f"tipo_contrato eq '{filtros['tipo_contrato']}'")
                if filtros.get("fornecedor"):
                    filter_parts.append(f"fornecedor eq '{filtros['fornecedor']}'")
                if filter_parts:
                    filter_expression = " and ".join(filter_parts)
            
            # Tentar busca híbrida (texto + vetores) se embeddings e VectorQuery disponíveis
            if embeddings and _VECTOR_QUERY_AVAILABLE and VectorQuery:
                try:
                    query_vector = embeddings.embed_query(query)
                    # VectorizedQuery já define kind="vector" internamente
                    vector_query = VectorQuery(
                        vector=query_vector,
                        k_nearest_neighbors=top_k,
                        fields="contentVector"
                    )
                    results = self.search_client.search(
                        search_text=query,
                        vector_queries=[vector_query],
                        filter=filter_expression,
                        top=top_k,
                        select=["id", "content", "numero_contrato", "fornecedor", "tipo_contrato", "nome_arquivo"]
                    )
                    logger.info(f"✅ Busca híbrida (texto + vetor) executada com sucesso")
                except (TypeError, AttributeError) as e:
                    logger.warning(f"Busca vetorial falhou ({e}), usando apenas texto")
                    results = self.search_client.search(
                        search_text=query,
                        filter=filter_expression,
                        top=top_k,
                        select=["id", "content", "numero_contrato", "fornecedor", "tipo_contrato", "nome_arquivo"]
                    )
            elif embeddings:
                try:
                    query_vector = embeddings.embed_query(query)
                    # Fallback para dict-based vector query com kind
                    results = self.search_client.search(
                        search_text=query,
                        vector_queries=[{
                            "kind": "vector",
                            "vector": query_vector,
                            "k_nearest_neighbors": top_k,
                            "fields": "contentVector"
                        }],
                        filter=filter_expression,
                        top=top_k,
                        select=["id", "content", "numero_contrato", "fornecedor", "tipo_contrato", "nome_arquivo"]
                    )
                    logger.info(f"✅ Busca híbrida (dict-based) executada com sucesso")
                except Exception as e:
                    logger.warning(f"Busca vetorial dict-based falhou ({e}), usando apenas texto")
                    results = self.search_client.search(
                        search_text=query,
                        filter=filter_expression,
                        top=top_k,
                        select=["id", "content", "numero_contrato", "fornecedor", "tipo_contrato", "nome_arquivo"]
                    )
            else:
                # Busca apenas por texto
                results = self.search_client.search(
                    search_text=query,
                    filter=filter_expression,
                    top=top_k,
                    select=["id", "content", "numero_contrato", "fornecedor", "tipo_contrato", "nome_arquivo"]
                )
            
            resultados_lista = []
            for result in results:
                resultados_lista.append({
                    "id": result.get("id"),
                    "content": result.get("content"),
                    "numero_contrato": result.get("numero_contrato"),
                    "fornecedor": result.get("fornecedor"),
                    "tipo_contrato": result.get("tipo_contrato"),
                    "nome_arquivo": result.get("nome_arquivo"),
                    "score": result.get("@search.score", 0)
                })
            logger.info(f"Busca retornou {len(resultados_lista)} resultados")
            return resultados_lista
        
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return []
    
    def _extrair_fornecedor(self, dados: Dict[str, Any]) -> Optional[str]:
        """Extrai nome do fornecedor dos dados."""
        if dados.get("fornecedor"):
            if isinstance(dados["fornecedor"], dict):
                return dados["fornecedor"].get("razao_social")
            return str(dados["fornecedor"])
        return None
    
    def _formatar_data(self, data: Any) -> Optional[str]:
        """Formata data para formato ISO (Azure Search espera DateTimeOffset)."""
        if not data:
            return None
        if hasattr(data, "isoformat"):
            # date ou datetime
            s = data.isoformat()
            return s + "Z" if "Z" not in s and "+" not in s else s
        if isinstance(data, str):
            try:
                dt = datetime.fromisoformat(data.replace("/", "-").strip())
                s = dt.isoformat()
                return s + "Z" if "Z" not in s and "+" not in s else s
            except Exception:
                return None
        return None
