"""Schemas Pydantic para validação de dados de contratos de TI.

Estruturas de dados baseadas nas necessidades de ITAM/SAM para análise
completa de contratos de software, hardware, serviços e mão de obra.
"""

from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


# ============================================
# ENUMS
# ============================================

class TipoContrato(str, Enum):
    """Tipos de contrato suportados."""
    SOFTWARE = "software"
    HARDWARE = "hardware"
    SERVICOS = "servicos"
    MAO_DE_OBRA = "mao_de_obra"
    HIBRIDO = "hibrido"
    OUTRO = "outro"


class TipoLicenca(str, Enum):
    """Tipos de licença de software."""
    PERPETUA = "perpetua"
    ASSINATURA = "assinatura"
    POR_USUARIO = "por_usuario"
    POR_DISPOSITIVO = "por_dispositivo"
    POR_SERVIDOR = "por_servidor"
    CONCURRENT = "concurrent"
    SITE_LICENSE = "site_license"
    OUTRO = "outro"


class FormaPagamento(str, Enum):
    """Formas de pagamento."""
    MENSAL = "mensal"
    TRIMESTRAL = "trimestral"
    SEMESTRAL = "semestral"
    ANUAL = "anual"
    UNICO = "unico"
    CUSTOMIZADO = "customizado"


class IndiceReajuste(str, Enum):
    """Índices de reajuste de valores."""
    IGPM = "igpm"
    IPCA = "ipca"
    INPC = "inpc"
    IGP_DI = "igp_di"
    PERCENTUAL_FIXO = "percentual_fixo"
    NAO_APLICAVEL = "nao_aplicavel"
    OUTRO = "outro"


# ============================================
# MODELOS BASE
# ============================================

class Fornecedor(BaseModel):
    """Dados do fornecedor/prestador de serviço."""
    cnpj: Optional[str] = Field(None, description="CNPJ do fornecedor")
    razao_social: str = Field(..., description="Razão social do fornecedor")
    nome_fantasia: Optional[str] = Field(None, description="Nome fantasia")
    contato_nome: Optional[str] = Field(None, description="Nome do contato principal")
    contato_email: Optional[str] = Field(None, description="Email do contato")
    contato_telefone: Optional[str] = Field(None, description="Telefone do contato")
    endereco: Optional[str] = Field(None, description="Endereço completo")


class Licenciamento(BaseModel):
    """Informações de licenciamento de software."""
    tipo_licenca: Optional[TipoLicenca] = Field(None, description="Tipo de licença")
    quantidade_licencas: Optional[int] = Field(None, description="Quantidade de licenças contratadas", ge=0)
    restricoes_uso: Optional[str] = Field(None, description="Restrições de uso")
    sublicenciamento_permitido: Optional[bool] = Field(None, description="Permite sublicenciamento")
    direitos_propriedade_intelectual: Optional[str] = Field(None, description="Direitos de PI")
    escopo_uso: Optional[str] = Field(None, description="Escopo de uso autorizado")
    limitacoes_tecnicas: Optional[str] = Field(None, description="Limitações técnicas")


class Vigencia(BaseModel):
    """Informações de vigência do contrato."""
    data_inicio: Optional[date] = Field(None, description="Data de início da vigência")
    data_termino: Optional[date] = Field(None, description="Data de término da vigência")
    prazo_meses: Optional[int] = Field(None, description="Prazo em meses", ge=0)
    renovacao_automatica: Optional[bool] = Field(None, description="Possui renovação automática")
    condicoes_renovacao: Optional[str] = Field(None, description="Condições para renovação")
    prazo_aviso_previo: Optional[int] = Field(None, description="Prazo de aviso prévio em dias", ge=0)
    clausulas_rescisao: Optional[str] = Field(None, description="Cláusulas de rescisão")
    penalidades_rescisao: Optional[str] = Field(None, description="Penalidades por rescisão antecipada")

    @field_validator('data_inicio', 'data_termino', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Converte strings de data para objetos date."""
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                try:
                    return datetime.strptime(v, "%d/%m/%Y").date()
                except ValueError:
                    return None
        return v


class Custos(BaseModel):
    """Informações de custos e valores do contrato."""
    valor_total: Optional[float] = Field(None, description="Valor total do contrato", ge=0)
    valor_mensal: Optional[float] = Field(None, description="Valor mensal", ge=0)
    valor_anual: Optional[float] = Field(None, description="Valor anual", ge=0)
    moeda: str = Field("BRL", description="Moeda (padrão BRL)")
    forma_pagamento: Optional[FormaPagamento] = Field(None, description="Forma de pagamento")
    indice_reajuste: Optional[IndiceReajuste] = Field(None, description="Índice de reajuste")
    periodicidade_reajuste: Optional[str] = Field(None, description="Periodicidade do reajuste")
    percentual_reajuste: Optional[float] = Field(None, description="Percentual de reajuste", ge=0)
    multas: Optional[str] = Field(None, description="Multas contratuais")
    penalidades: Optional[str] = Field(None, description="Penalidades")
    custos_adicionais: Optional[str] = Field(None, description="Custos adicionais")


class SuporteSLA(BaseModel):
    """Informações de suporte e SLA."""
    niveis_suporte: Optional[str] = Field(None, description="Níveis de suporte oferecidos")
    tempo_resposta_sla: Optional[str] = Field(None, description="Tempos de resposta SLA")
    canais_atendimento: Optional[List[str]] = Field(None, description="Canais de atendimento")
    horario_atendimento: Optional[str] = Field(None, description="Horário de atendimento")
    disponibilidade_garantida: Optional[str] = Field(None, description="Disponibilidade garantida (%)")
    manutencao_inclusa: Optional[bool] = Field(None, description="Manutenção inclusa")
    atualizacoes_inclusas: Optional[bool] = Field(None, description="Atualizações inclusas")
    penalidades_descumprimento_sla: Optional[str] = Field(None, description="Penalidades por descumprimento SLA")


class ComplianceLGPD(BaseModel):
    """Informações de compliance e LGPD."""
    clausulas_lgpd: Optional[str] = Field(None, description="Cláusulas LGPD")
    tratamento_dados_pessoais: Optional[str] = Field(None, description="Como trata dados pessoais")
    responsavel_tratamento: Optional[str] = Field(None, description="Responsável pelo tratamento")
    encarregado_dpo: Optional[str] = Field(None, description="Encarregado/DPO")
    transferencia_internacional: Optional[bool] = Field(None, description="Permite transferência internacional")
    paises_transferencia: Optional[List[str]] = Field(None, description="Países para transferência")
    direito_auditoria: Optional[bool] = Field(None, description="Direito de auditoria")
    medidas_seguranca: Optional[str] = Field(None, description="Medidas de segurança")
    prazo_retencao_dados: Optional[str] = Field(None, description="Prazo de retenção de dados")


class ObrigacoesLegais(BaseModel):
    """Obrigações legais e cláusulas jurídicas."""
    confidencialidade: Optional[str] = Field(None, description="Cláusula de confidencialidade")
    propriedade_intelectual: Optional[str] = Field(None, description="Propriedade intelectual")
    foro_jurisdicao: Optional[str] = Field(None, description="Foro/jurisdição")
    lei_aplicavel: Optional[str] = Field(None, description="Lei aplicável")
    garantias: Optional[str] = Field(None, description="Garantias")
    indenizacoes: Optional[str] = Field(None, description="Cláusulas de indenização")
    limitacao_responsabilidade: Optional[str] = Field(None, description="Limitação de responsabilidade")
    forca_maior: Optional[str] = Field(None, description="Cláusula de força maior")


# ============================================
# MODELO COMPLETO
# ============================================

class ContratoCompleto(BaseModel):
    """Modelo completo de contrato com todas as informações estruturadas."""
    
    # Metadados
    id_documento: Optional[str] = Field(None, description="ID único do documento")
    nome_arquivo: Optional[str] = Field(None, description="Nome do arquivo original")
    data_processamento: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Data de processamento"
    )
    
    # Dados Gerais
    numero_contrato: Optional[str] = Field(None, description="Número do contrato")
    tipo_contrato: Optional[TipoContrato] = Field(None, description="Tipo do contrato")
    objeto_contrato: Optional[str] = Field(None, description="Objeto/descrição do contrato")
    data_assinatura: Optional[date] = Field(None, description="Data de assinatura")
    
    # Entidades relacionadas
    fornecedor: Optional[Fornecedor] = Field(None, description="Dados do fornecedor")
    contratante: Optional[str] = Field(None, description="Dados do contratante")
    
    # Informações específicas
    licenciamento: Optional[Licenciamento] = Field(None, description="Informações de licenciamento")
    vigencia: Optional[Vigencia] = Field(None, description="Informações de vigência")
    custos: Optional[Custos] = Field(None, description="Informações de custos")
    suporte_sla: Optional[SuporteSLA] = Field(None, description="Informações de suporte e SLA")
    compliance_lgpd: Optional[ComplianceLGPD] = Field(None, description="Informações de compliance")
    obrigacoes_legais: Optional[ObrigacoesLegais] = Field(None, description="Obrigações legais")
    
    # Texto completo e chunks
    texto_completo: Optional[str] = Field(None, description="Texto completo do contrato")
    chunks: Optional[List[str]] = Field(None, description="Chunks para indexação")
    
    # Classificação e análise
    confianca_extracao: Optional[float] = Field(None, description="Confiança da extração (0-1)", ge=0, le=1)
    observacoes: Optional[str] = Field(None, description="Observações da análise")
    alertas: Optional[List[str]] = Field(None, description="Alertas identificados")
    
    class Config:
        """Configuração do modelo Pydantic."""
        json_schema_extra = {
            "example": {
                "numero_contrato": "CT-2025-0001",
                "tipo_contrato": "software",
                "objeto_contrato": "Licença de uso de software ITAM",
                "fornecedor": {
                    "razao_social": "TECHNOVA SOLUCOES EM TI LTDA",
                    "cnpj": "12.345.678/0001-99"
                },
                "vigencia": {
                    "data_inicio": "2024-01-01",
                    "data_termino": "2025-01-01",
                    "prazo_meses": 12
                },
                "custos": {
                    "valor_anual": 120000.00,
                    "moeda": "BRL",
                    "forma_pagamento": "mensal"
                }
            }
        }


# ============================================
# MODELOS AUXILIARES
# ============================================

class ClassificacaoContrato(BaseModel):
    """Resultado da classificação de contrato."""
    tipo_contrato: TipoContrato = Field(..., description="Tipo identificado")
    confianca: float = Field(..., description="Confiança da classificação (0-1)", ge=0, le=1)
    justificativa: str = Field(..., description="Justificativa da classificação")
    palavras_chave: List[str] = Field(default_factory=list, description="Palavras-chave identificadas")

    @field_validator("tipo_contrato", mode="before")
    @classmethod
    def normalizar_tipo_contrato(cls, v: object) -> object:
        """Aceita string do LLM (ex: 'Software', 'MAO_DE_OBRA') e normaliza para o enum."""
        if isinstance(v, TipoContrato):
            return v
        if isinstance(v, str):
            s = v.strip().lower().replace(" ", "_")
            for member in TipoContrato:
                if member.value == s:
                    return member
            # Tentar por nome do enum (ex: "software" -> SOFTWARE)
            try:
                return TipoContrato(s)
            except ValueError:
                pass
        return v


class ResultadoBusca(BaseModel):
    """Resultado de busca no índice."""
    id_documento: str = Field(..., description="ID do documento")
    numero_contrato: Optional[str] = Field(None, description="Número do contrato")
    fornecedor: Optional[str] = Field(None, description="Nome do fornecedor")
    tipo_contrato: Optional[str] = Field(None, description="Tipo do contrato")
    score: float = Field(..., description="Score de relevância", ge=0)
    conteudo_relevante: str = Field(..., description="Conteúdo relevante encontrado")
    highlights: Optional[List[str]] = Field(None, description="Destaques do texto")


class ComparacaoContratos(BaseModel):
    """Resultado de comparação entre contratos."""
    contratos_comparados: List[str] = Field(..., description="IDs dos contratos comparados")
    criterio: str = Field(..., description="Critério de comparação")
    diferencas: List[str] = Field(default_factory=list, description="Diferenças identificadas")
    semelhancas: List[str] = Field(default_factory=list, description="Semelhanças identificadas")
    recomendacoes: Optional[List[str]] = Field(None, description="Recomendações")
    resumo: str = Field(..., description="Resumo da comparação")
