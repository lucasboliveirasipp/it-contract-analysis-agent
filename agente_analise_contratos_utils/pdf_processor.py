"""Processador de PDFs com extração de texto nativo e OCR fallback.

Utiliza pdfplumber para extração de texto nativo e Azure Document Intelligence
para OCR quando necessário.
"""

import io
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pdfplumber
from azure.ai.documentintelligence.models import AnalyzeResult

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processador de PDFs com suporte a texto nativo e OCR."""
    
    def __init__(self, doc_intel_client=None):
        """Inicializa o processador.
        
        Args:
            doc_intel_client: Cliente Azure Document Intelligence (opcional)
        """
        self.doc_intel_client = doc_intel_client
        
    def extrair_texto(
        self,
        arquivo_path: str,
        usar_ocr_se_necessario: bool = True,
        min_texto_por_pagina: int = 50
    ) -> Dict[str, Any]:
        """Extrai texto de um PDF.
        
        Tenta primeiro extração nativa com pdfplumber. Se o texto extraído
        for muito curto (indicando PDF escaneado), usa OCR via Azure DI.
        
        Args:
            arquivo_path: Caminho para o arquivo PDF
            usar_ocr_se_necessario: Se True, usa OCR quando texto nativo for insuficiente
            min_texto_por_pagina: Mínimo de caracteres por página para considerar sucesso
            
        Returns:
            Dict com:
                - texto: Texto extraído
                - metodo: "nativo" ou "ocr"
                - num_paginas: Número de páginas
                - sucesso: True/False
                - erro: Mensagem de erro se houver
        """
        arquivo_path = Path(arquivo_path)
        
        if not arquivo_path.exists():
            return {
                "texto": "",
                "metodo": None,
                "num_paginas": 0,
                "sucesso": False,
                "erro": f"Arquivo não encontrado: {arquivo_path}"
            }
        
        logger.info(f"Extraindo texto de: {arquivo_path.name}")
        
        # Tentar extração nativa primeiro
        resultado_nativo = self._extrair_texto_nativo(arquivo_path)
        
        if resultado_nativo["sucesso"]:
            # Verificar se o texto extraído é suficiente
            texto = resultado_nativo["texto"]
            num_paginas = resultado_nativo["num_paginas"]
            
            if len(texto) > (min_texto_por_pagina * num_paginas):
                logger.info(f"✅ Texto extraído com sucesso (nativo): {len(texto)} caracteres")
                return resultado_nativo
            else:
                logger.warning(
                    f"⚠️ Texto nativo insuficiente ({len(texto)} chars para {num_paginas} páginas). "
                    f"PDF pode estar escaneado."
                )
        
        # Usar OCR se necessário e disponível
        if usar_ocr_se_necessario and self.doc_intel_client:
            logger.info("Tentando extração via OCR...")
            resultado_ocr = self._extrair_texto_ocr(arquivo_path)
            
            if resultado_ocr["sucesso"]:
                logger.info(f"✅ Texto extraído com sucesso (OCR): {len(resultado_ocr['texto'])} caracteres")
                return resultado_ocr
            else:
                logger.error(f"❌ Erro no OCR: {resultado_ocr['erro']}")
        
        # Se chegou aqui, usar o resultado nativo mesmo que insuficiente
        if resultado_nativo["texto"]:
            logger.warning("⚠️ Retornando texto nativo mesmo sendo insuficiente")
            return resultado_nativo
        
        return {
            "texto": "",
            "metodo": None,
            "num_paginas": 0,
            "sucesso": False,
            "erro": "Não foi possível extrair texto do PDF"
        }
    
    def _extrair_texto_nativo(self, arquivo_path: Path) -> Dict[str, Any]:
        """Extrai texto nativo usando pdfplumber.

        Inclui valores de campos de formulário (annotations/widgets) que
        podem conter dados como data de assinatura digital.

        Args:
            arquivo_path: Caminho para o arquivo PDF

        Returns:
            Dict com resultado da extração
        """
        try:
            texto_completo = []
            num_paginas = 0

            with pdfplumber.open(arquivo_path) as pdf:
                num_paginas = len(pdf.pages)

                # Extrair valores de campos de formulário (annotations/widgets)
                campos_formulario = self._extrair_campos_formulario(pdf)

                for i, page in enumerate(pdf.pages, 1):
                    texto = page.extract_text()
                    if texto:
                        texto_completo.append(f"--- Página {i} ---\n{texto}")

                # Anexar campos de formulário ao final se encontrados
                if campos_formulario:
                    texto_completo.append("--- Campos de Formulário / Assinatura Digital ---")
                    for campo, valor in campos_formulario.items():
                        texto_completo.append(f"{campo}: {valor}")

            texto_final = "\n\n".join(texto_completo)

            return {
                "texto": texto_final,
                "metodo": "nativo",
                "num_paginas": num_paginas,
                "sucesso": True,
                "erro": None
            }

        except Exception as e:
            logger.error(f"Erro na extração nativa: {e}")
            return {
                "texto": "",
                "metodo": "nativo",
                "num_paginas": 0,
                "sucesso": False,
                "erro": str(e)
            }

    def _extrair_campos_formulario(self, pdf) -> Dict[str, str]:
        """Extrai valores de campos de formulário (AcroForm/widgets) do PDF.

        Campos de formulário são usados em assinaturas digitais e podem
        conter dados como data de assinatura que não aparecem no texto nativo.

        Args:
            pdf: Objeto pdfplumber aberto

        Returns:
            Dict campo -> valor
        """
        campos = {}
        try:
            # Acesso ao AcroForm via pdfplumber (resolve objetos internos do PDF)
            pdf_dict = pdf.doc.catalog
            if not pdf_dict:
                return campos

            acroform = pdf_dict.get("AcroForm")
            if not acroform:
                return campos

            from pdfminer.pdftypes import resolve1
            acroform = resolve1(acroform)
            fields = acroform.get("Fields", [])

            for field_ref in fields:
                try:
                    field = resolve1(field_ref)
                    nome = field.get("T")
                    valor = field.get("V")

                    if nome and valor:
                        # Decodificar bytes para string
                        if isinstance(nome, bytes):
                            nome = nome.decode("utf-8", errors="replace")
                        if isinstance(valor, bytes):
                            valor = valor.decode("utf-8", errors="replace")

                        nome = str(nome).strip()
                        valor = str(valor).strip()

                        if valor and valor.lower() not in ("", "none", "null"):
                            campos[nome] = valor
                            logger.info(f"Campo de formulário encontrado: {nome} = {valor}")
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Sem campos de formulário ou erro ao extrair: {e}")

        return campos
    
    def _extrair_texto_ocr(self, arquivo_path: Path) -> Dict[str, Any]:
        """Extrai texto usando Azure Document Intelligence (OCR).
        
        Args:
            arquivo_path: Caminho para o arquivo PDF
            
        Returns:
            Dict com resultado da extração
        """
        if not self.doc_intel_client:
            return {
                "texto": "",
                "metodo": "ocr",
                "num_paginas": 0,
                "sucesso": False,
                "erro": "Cliente Azure Document Intelligence não inicializado"
            }
        
        try:
            # Ler arquivo
            with open(arquivo_path, "rb") as f:
                documento_bytes = f.read()

            # Analisar documento usando a API correta do Azure Document Intelligence
            # O segundo argumento (body) deve ser IO[bytes] diretamente
            poller = self.doc_intel_client.begin_analyze_document(
                "prebuilt-read",  # model_id como primeiro argumento posicional
                io.BytesIO(documento_bytes),  # body como segundo argumento posicional (IO[bytes])
                content_type="application/pdf"  # content_type explícito
            )

            result: AnalyzeResult = poller.result()
            
            # Extrair texto por página
            texto_completo = []
            num_paginas = 0
            
            if result.pages:
                num_paginas = len(result.pages)
                
                for page in result.pages:
                    page_num = page.page_number
                    
                    # Extrair texto das linhas
                    if hasattr(page, 'lines') and page.lines:
                        linhas = [linha.content for linha in page.lines]
                        texto_pagina = "\n".join(linhas)
                        texto_completo.append(f"--- Página {page_num} ---\n{texto_pagina}")
            
            texto_final = "\n\n".join(texto_completo)
            
            return {
                "texto": texto_final,
                "metodo": "ocr",
                "num_paginas": num_paginas,
                "sucesso": True,
                "erro": None
            }
            
        except Exception as e:
            logger.error(f"Erro no OCR: {e}")
            return {
                "texto": "",
                "metodo": "ocr",
                "num_paginas": 0,
                "sucesso": False,
                "erro": str(e)
            }
    
    def extrair_metadados(self, arquivo_path: str) -> Dict[str, Any]:
        """Extrai metadados básicos do PDF.
        
        Args:
            arquivo_path: Caminho para o arquivo PDF
            
        Returns:
            Dict com metadados
        """
        arquivo_path = Path(arquivo_path)
        
        metadados = {
            "nome_arquivo": arquivo_path.name,
            "tamanho_bytes": 0,
            "num_paginas": 0,
            "titulo": None,
            "autor": None,
            "criador": None,
            "data_criacao": None
        }
        
        if not arquivo_path.exists():
            return metadados
        
        try:
            metadados["tamanho_bytes"] = arquivo_path.stat().st_size
            
            with pdfplumber.open(arquivo_path) as pdf:
                metadados["num_paginas"] = len(pdf.pages)
                
                # Metadados do PDF
                if pdf.metadata:
                    metadados["titulo"] = pdf.metadata.get("Title")
                    metadados["autor"] = pdf.metadata.get("Author")
                    metadados["criador"] = pdf.metadata.get("Creator")
                    metadados["data_criacao"] = pdf.metadata.get("CreationDate")
        
        except Exception as e:
            logger.error(f"Erro ao extrair metadados: {e}")
        
        return metadados
