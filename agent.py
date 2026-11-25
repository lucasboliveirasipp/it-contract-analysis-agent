from __future__ import annotations
import io
import sys
import os
import logging
import time
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

# --- configuração de caminho (path) ---
# Garantir que o diretório do agente seja o PRIMEIRO em sys.path
# (antes do streamlit e do app pai). Assim "utils", "config", "skills", etc.
# resolvem para este projeto e não para outro agente.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir in sys.path:
    sys.path.remove(current_dir)
sys.path.insert(0, current_dir)

# Limpar módulos cacheados de outros agentes para evitar conflito.
# Em um hub multi-agente, outro agente pode ter carregado
# "utils", "config", "skills" etc. antes. O Python cacheia em sys.modules
# e não re-importa mesmo com sys.path diferente.
_project_modules = ["agente_analise_contratos_utils", "config", "agente_analise_contratos_skills", "agente_analise_contratos_prompts", "agente_analise_contratos_schemas"]
for _mod_name in list(sys.modules.keys()):
    for _prefix in _project_modules:
        if _mod_name == _prefix or _mod_name.startswith(f"{_prefix}."):
            del sys.modules[_mod_name]
            break

# bibliotecas externas
import streamlit as st

# Importações do projeto
from agente_analise_contratos_skills.extrair_texto import extrair_texto_simples
from agente_analise_contratos_skills.classificar_contrato import classificar_contrato_estruturado
from agente_analise_contratos_skills.extrair_clausulas import extrair_clausulas_estruturado
from db_connector import MONGO
from feedback import log_interaction, render_feedback_widget

# configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_NAME = "agente_analise_contratos"

# --- importação do estilo visual ---
try:
    from agente_analise_contratos_style.streamlit_style import (
        init_page_config,
        apply_app_style,
        build_institutional_header,
        build_footer
    )
except ImportError as e:
    st.error(f"ERRO CRÍTICO: não foi possível importar 'streamlit_style'. detalhe: {e}")
    st.stop()

# --- funções de dados ---
@st.cache_data(ttl=60)
def get_local_file_catalog():
    """Lista arquivos dinamicamente baseando-se no diretório atual do projeto."""
    try:
        target_folders = {
            "agente_analise_contratos_assets/base de dados de exemplo": "Sistema",
            "agente_analise_contratos_ingestao_documentos": "Upload Usuário"
        }
        docs = []

        for folder, origem in target_folders.items():
            folder_path = os.path.join(current_dir, folder)

            if os.path.exists(folder_path):
                files = [f for f in os.listdir(folder_path) if f.endswith(('.pdf', '.docx'))]
                for f in files:
                    file_path = os.path.join(folder_path, f)
                    stats = os.stat(file_path)

                    upload_time = datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M')
                    size_mb = stats.st_size / (1024 * 1024)

                    docs.append({
                        "Nome do Documento": f,
                        "Data de Upload": upload_time,
                        "Tamanho (MB)": size_mb,
                        "Origem": origem
                    })

        if docs:
            df = pd.DataFrame(docs)
            df = df.drop_duplicates(subset=["Nome do Documento"])
            df = df.sort_values(by="Data de Upload", ascending=False)
            return df
        return pd.DataFrame()

    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}")
        return pd.DataFrame()


def delete_document_process(filename: str):
    """Remove arquivo local."""
    msgs = []

    target_folder = os.path.join(current_dir, "agente_analise_contratos_ingestao_documentos")
    filepath = os.path.join(target_folder, filename)

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            msgs.append(f"✅ Arquivo local removido.")
        else:
            msgs.append(f"⚠️ Arquivo não encontrado na pasta.")
    except Exception as e:
        msgs.append(f"❌ Erro ao remover: {e}")

    return msgs


# --- CSS ---
def _inject_component_styles():
    st.markdown("""
    <style>
        .status-banner {
            background-color: #FFFFFF;
            color: #2D3748;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 24px;
            border: 1px solid #EDF2F7;
            display: flex; align-items: center; justify-content: space-between;
            font-family: 'Segoe UI', sans-serif !important;
        }
        .status-text {
            color: #1E3A8A;
            font-weight: 700; letter-spacing: 0.5px;
            text-transform: uppercase; font-size: 0.9rem;
        }
        .status-pill {
            background-color: #1E3A8A;
            color: white !important;
            padding: 6px 16px; border-radius: 6px;
            font-weight: 600; font-size: 0.85rem;
        }
        .manual-card h3 {
            color: #1E3A8A !important;
            font-family: 'Segoe UI', sans-serif !important;
            font-weight: 700 !important;
            font-size: 1.25rem !important;
            margin-bottom: 12px !important;
        }
        .manual-card p, .manual-card li, .manual-card span {
            color: #2D3748 !important;
            font-family: 'Segoe UI', sans-serif !important;
            line-height: 1.6;
        }
        .file-item {
            display: flex; align-items: center; gap: 10px;
            padding: 8px 0; border-bottom: 1px solid #EDF2F7;
            color: #2D3748;
            font-family: 'Segoe UI', sans-serif !important;
        }
        .contract-card {
            background-color: #FFFFFF;
            border: 1px solid #EDF2F7;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .contract-card-header {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 12px; padding-bottom: 12px;
            border-bottom: 1px solid #EDF2F7;
        }
        .badge-success {
            background-color: #38A169; color: white;
            padding: 4px 12px; border-radius: 6px;
            font-weight: 600; font-size: 0.8rem;
        }
        .badge-error {
            background-color: #E53E3E; color: white;
            padding: 4px 12px; border-radius: 6px;
            font-weight: 600; font-size: 0.8rem;
        }
    </style>
    """, unsafe_allow_html=True)


# --- Pipeline de processamento ---
def processar_contrato_unico(uploaded_file, log=None) -> Dict:
    """Pipeline para um único arquivo com log detalhado de cada etapa."""
    if log is None:
        log = lambda msg: None

    result = {
        "filename": uploaded_file.name,
        "status": "error",
        "error_msg": None,
        "texto_extraido": "",
        "metodo_extracao": "",
        "num_paginas": 0,
        "num_caracteres": 0,
        "classificacao": None,
        "clausulas": None,
    }

    upload_path = os.path.join(current_dir, "agente_analise_contratos_ingestao_documentos")
    os.makedirs(upload_path, exist_ok=True)

    try:
        # 1. Salvar arquivo
        log(f"💾 Salvando arquivo **{uploaded_file.name}**...")
        save_path = os.path.join(upload_path, uploaded_file.name)
        with open(save_path, "wb") as w:
            w.write(uploaded_file.getbuffer())
        size_mb = uploaded_file.size / (1024 * 1024)
        log(f"&nbsp;&nbsp;&nbsp;&nbsp;Arquivo salvo ({size_mb:.2f} MB)")

        # 2. Extrair texto
        log("📖 Extraindo texto do PDF com pdfplumber...")
        t0 = time.time()
        extracao = extrair_texto_simples(save_path)
        texto = extracao.get("texto", "")
        result["texto_extraido"] = texto
        result["metodo_extracao"] = extracao.get("metodo", "DESCONHECIDO")
        result["num_paginas"] = extracao.get("num_paginas", 0)
        result["num_caracteres"] = len(texto)
        elapsed = time.time() - t0
        log(
            f"&nbsp;&nbsp;&nbsp;&nbsp;Extração concluída em {elapsed:.1f}s — "
            f"**{result['num_paginas']} páginas**, "
            f"**{result['num_caracteres']:,} caracteres**"
        )

        if not texto or len(texto) < 50:
            result["error_msg"] = "Texto extraído insuficiente para análise."
            log("⚠️ Texto insuficiente para análise. Pulando etapas seguintes.")
            return result

        # 3. Classificar contrato
        log("🔍 Classificando tipo de contrato via IA...")
        t0 = time.time()
        try:
            classificacao = classificar_contrato_estruturado(texto)
            result["classificacao"] = classificacao
            elapsed = time.time() - t0
            tipo = classificacao.get("tipo_contrato", "—")
            confianca = classificacao.get("confianca")
            confianca_txt = f"{float(confianca)*100:.0f}%" if confianca else "—"
            log(
                f"&nbsp;&nbsp;&nbsp;&nbsp;Classificado como **{tipo.upper()}** "
                f"(confiança: {confianca_txt}) em {elapsed:.1f}s"
            )
        except Exception as e:
            logger.error(f"Erro ao classificar {uploaded_file.name}: {e}")
            log(f"&nbsp;&nbsp;&nbsp;&nbsp;❌ Erro na classificação: {e}")

        # 4. Extrair cláusulas
        log("📋 Extraindo cláusulas contratuais via IA...")
        t0 = time.time()
        try:
            clausulas = extrair_clausulas_estruturado(texto)
            result["clausulas"] = clausulas
            elapsed = time.time() - t0
            n_secoes = sum(1 for v in clausulas.values() if isinstance(v, dict))
            log(f"&nbsp;&nbsp;&nbsp;&nbsp;**{n_secoes} seções** extraídas em {elapsed:.1f}s")
        except Exception as e:
            logger.error(f"Erro ao extrair cláusulas de {uploaded_file.name}: {e}")
            log(f"&nbsp;&nbsp;&nbsp;&nbsp;❌ Erro na extração de cláusulas: {e}")

        result["status"] = "success"
        log(f"✅ **{uploaded_file.name}** processado com sucesso!")

    except Exception as e:
        result["error_msg"] = str(e)
        logger.error(f"Erro no pipeline para {uploaded_file.name}: {e}")
        log(f"❌ Erro fatal: {e}")

    return result


# --- Helpers de renderização ---
def _deep_find(data: Dict, *keys: str) -> str:
    """Busca um valor em qualquer nível do dict, incluindo seções numeradas."""
    if not data:
        return "—"
    for k in keys:
        # Buscar na raiz
        val = data.get(k)
        if val is not None and str(val).strip() and not isinstance(val, dict):
            return str(val)
    # Buscar dentro de todas as sub-seções
    for section_key, section_val in data.items():
        if isinstance(section_val, dict):
            for k in keys:
                val = section_val.get(k)
                if val is not None and str(val).strip() and not isinstance(val, dict):
                    return str(val)
    return "—"


def _format_currency(value) -> str:
    """Formata valor monetário para padrão brasileiro."""
    if value is None:
        return "—"
    try:
        v = float(value) if not isinstance(value, str) else float(str(value).replace(".", "").replace(",", "."))
        if v > 0:
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        if value:
            return str(value)
    return "—"


# Mapa de labels bonitos para as chaves do JSON
_LABELS = {
    "numero_contrato": "Número do Contrato",
    "tipo_contrato": "Tipo",
    "objeto_contrato": "Objeto",
    "data_assinatura": "Data de Assinatura",
    "cnpj": "CNPJ",
    "razao_social": "Razão Social",
    "nome_fantasia": "Nome Fantasia",
    "contato_nome": "Contato",
    "contato_email": "E-mail",
    "contato_telefone": "Telefone",
    "endereco": "Endereço",
    "tipo_licenca": "Tipo de Licença",
    "quantidade_licencas": "Quantidade de Licenças",
    "restricoes_uso": "Restrições de Uso",
    "sublicenciamento_permitido": "Sublicenciamento Permitido",
    "direitos_propriedade_intelectual": "Direitos de Propriedade Intelectual",
    "escopo_uso": "Escopo de Uso",
    "limitacoes_tecnicas": "Limitações Técnicas",
    "data_inicio": "Data de Início",
    "data_termino": "Data de Término",
    "prazo_meses": "Prazo (meses)",
    "renovacao_automatica": "Renovação Automática",
    "condicoes_renovacao": "Condições de Renovação",
    "prazo_aviso_previo": "Prazo de Aviso Prévio (dias)",
    "clausulas_rescisao": "Cláusulas de Rescisão",
    "penalidades_rescisao": "Penalidades de Rescisão",
    "valor_total": "Valor Total",
    "valor_mensal": "Valor Mensal",
    "valor_anual": "Valor Anual",
    "moeda": "Moeda",
    "forma_pagamento": "Forma de Pagamento",
    "indice_reajuste": "Índice de Reajuste",
    "periodicidade_reajuste": "Periodicidade do Reajuste",
    "percentual_reajuste": "Percentual de Reajuste",
    "multas": "Multas",
    "penalidades": "Penalidades",
    "custos_adicionais": "Custos Adicionais",
    "niveis_suporte": "Níveis de Suporte",
    "tempo_resposta_sla": "Tempo de Resposta / SLA",
    "canais_atendimento": "Canais de Atendimento",
    "horario_atendimento": "Horário de Atendimento",
    "disponibilidade_garantida": "Disponibilidade Garantida",
    "manutencao_inclusa": "Manutenção Inclusa",
    "atualizacoes_inclusas": "Atualizações Inclusas",
    "penalidades_descumprimento_sla": "Penalidades por Descumprimento de SLA",
    "clausulas_lgpd": "Cláusulas LGPD",
    "tratamento_dados_pessoais": "Tratamento de Dados Pessoais",
    "responsavel_tratamento": "Responsável pelo Tratamento",
    "encarregado_dpo": "Encarregado / DPO",
    "transferencia_internacional": "Transferência Internacional",
    "paises_transferencia": "Países de Transferência",
    "direito_auditoria": "Direito de Auditoria",
    "medidas_seguranca": "Medidas de Segurança",
    "prazo_retencao_dados": "Prazo de Retenção de Dados",
    "confidencialidade": "Confidencialidade",
    "propriedade_intelectual": "Propriedade Intelectual",
    "foro_jurisdicao": "Foro / Jurisdição",
    "lei_aplicavel": "Lei Aplicável",
    "garantias": "Garantias",
    "indenizacoes": "Indenizações",
    "limitacao_responsabilidade": "Limitação de Responsabilidade",
    "forca_maior": "Força Maior",
    "observacoes": "Observações",
}


def _format_value(key: str, value) -> str:
    """Formata o valor de acordo com o tipo."""
    if value is None:
        return None  # será omitido
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if "valor" in key and isinstance(value, (int, float)):
        return _format_currency(value)
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _section_header_html(titulo: str) -> str:
    """Gera HTML de título de seção com box do tema (fundo azul, texto branco)."""
    return (
        f'<div style="background: linear-gradient(135deg, #1E3A8A 0%, #0F766E 100%); '
        f'color: white; padding: 10px 18px; border-radius: 8px; margin: 24px 0 14px 0; '
        f'font-size: 1.05rem; font-weight: 700; letter-spacing: 0.3px;">'
        f'{titulo}</div>'
    )


def _render_clausulas_html(clausulas: Dict, classif: Dict) -> str:
    """Converte o dict de cláusulas em HTML estruturado com headers do tema."""
    html = ""

    # Classificação primeiro
    if classif:
        html += _section_header_html("🔍 Classificação")
        tipo = classif.get("tipo_contrato", "—")
        confianca = classif.get("confianca")
        confianca_txt = f"{float(confianca)*100:.0f}%" if confianca else "—"
        html += f'<p><b>Tipo de Contrato:</b> {tipo.upper().replace("_", " ")}</p>'
        html += f'<p><b>Confiança da IA:</b> {confianca_txt}</p>'
        if classif.get("justificativa"):
            html += f'<blockquote style="border-left:3px solid #1E3A8A; padding-left:12px; color:#4A5568; margin:10px 0;">{classif["justificativa"]}</blockquote>'
        palavras = classif.get("palavras_chave")
        if palavras:
            tags = palavras if isinstance(palavras, list) else [str(palavras)]
            tags_html = " &middot; ".join(f'<code>{t}</code>' for t in tags)
            html += f'<p><b>Palavras-chave:</b> {tags_html}</p>'

    # Seções de cláusulas
    for section_key, section_val in clausulas.items():
        if section_key == "observacoes":
            continue
        if not isinstance(section_val, dict):
            continue

        titulo = section_key
        if titulo[0].isdigit() and ". " in titulo:
            titulo = titulo.split(". ", 1)[1]

        html += _section_header_html(titulo)

        for k, v in section_val.items():
            formatted = _format_value(k, v)
            if formatted is None:
                continue
            label = _LABELS.get(k, k.replace("_", " ").title())
            html += f'<p><b>{label}:</b> {formatted}</p>'

    # Observações no final
    obs = clausulas.get("observacoes")
    if obs:
        html += _section_header_html("📝 Observações")
        html += f'<blockquote style="border-left:3px solid #1E3A8A; padding-left:12px; color:#4A5568;">{obs}</blockquote>'

    return html


# --- Export Excel ---
def _gerar_excel_contrato(result: Dict) -> bytes:
    """Gera Excel espelhando o relatório exibido na tela: uma planilha única
    com seções separadas por headers, campo e valor lado a lado."""
    rows: List[Dict[str, str]] = []

    classif = result.get("classificacao") or {}
    clausulas = result.get("clausulas") or {}

    # --- Classificação ---
    if classif:
        rows.append({"Seção": "CLASSIFICAÇÃO", "Campo": "", "Valor": ""})
        rows.append({"Seção": "", "Campo": "Tipo de Contrato", "Valor": str(classif.get("tipo_contrato", "—")).upper()})
        confianca = classif.get("confianca")
        rows.append({"Seção": "", "Campo": "Confiança da IA", "Valor": f"{float(confianca)*100:.0f}%" if confianca else "—"})
        if classif.get("justificativa"):
            rows.append({"Seção": "", "Campo": "Justificativa", "Valor": classif["justificativa"]})
        palavras = classif.get("palavras_chave")
        if palavras:
            rows.append({"Seção": "", "Campo": "Palavras-chave", "Valor": ", ".join(palavras) if isinstance(palavras, list) else str(palavras)})
        rows.append({"Seção": "", "Campo": "", "Valor": ""})  # linha em branco

    # --- Seções de cláusulas ---
    for section_key, section_val in clausulas.items():
        if section_key == "observacoes":
            continue
        if not isinstance(section_val, dict):
            continue

        titulo = section_key
        if titulo[0].isdigit() and ". " in titulo:
            titulo = titulo.split(". ", 1)[1]

        rows.append({"Seção": titulo.upper(), "Campo": "", "Valor": ""})

        for k, v in section_val.items():
            formatted = _format_value(k, v)
            if formatted is None:
                continue
            label = _LABELS.get(k, k.replace("_", " ").title())
            rows.append({"Seção": "", "Campo": label, "Valor": formatted})

        rows.append({"Seção": "", "Campo": "", "Valor": ""})  # linha em branco

    # --- Observações ---
    obs = clausulas.get("observacoes")
    if obs:
        rows.append({"Seção": "OBSERVAÇÕES", "Campo": "", "Valor": ""})
        rows.append({"Seção": "", "Campo": "Observações", "Valor": str(obs)})
        rows.append({"Seção": "", "Campo": "", "Valor": ""})

    # --- Info técnica ---
    rows.append({"Seção": "INFO TÉCNICA", "Campo": "", "Valor": ""})
    rows.append({"Seção": "", "Campo": "Arquivo", "Valor": result["filename"]})
    rows.append({"Seção": "", "Campo": "Método de Extração", "Valor": str(result.get("metodo_extracao", "—")).upper()})
    rows.append({"Seção": "", "Campo": "Páginas", "Valor": str(result.get("num_paginas", 0))})
    rows.append({"Seção": "", "Campo": "Caracteres", "Valor": f"{result.get('num_caracteres', 0):,}"})
    rows.append({"Seção": "", "Campo": "Data da Análise", "Valor": datetime.now().strftime("%d/%m/%Y %H:%M:%S")})

    df = pd.DataFrame(rows)

    # Gerar Excel com formatação
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Análise do Contrato")

        # Formatar headers de seção em negrito + fundo azul do tema
        from openpyxl.styles import Font, PatternFill, Alignment
        ws = writer.sheets["Análise do Contrato"]

        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        section_font = Font(bold=True, size=11)

        # Ajustar largura das colunas
        ws.column_dimensions["A"].width = 22
        ws.column_dimensions["B"].width = 35
        ws.column_dimensions["C"].width = 80

        for row_idx, row_data in enumerate(rows, start=2):  # +2: header Excel + 1-indexed
            if row_data["Seção"]:  # É header de seção
                for col in range(1, 4):
                    cell = ws.cell(row=row_idx, column=col)
                    cell.fill = header_fill
                    cell.font = header_font
            else:
                # Campo em negrito
                ws.cell(row=row_idx, column=2).font = section_font
                # Valor com wrap text
                ws.cell(row=row_idx, column=3).alignment = Alignment(wrap_text=True)

    buffer.seek(0)
    return buffer.getvalue()


# --- Renderização de cards ---
def render_contract_card(result: Dict):
    """Card visual — tudo visível, Markdown estruturado."""
    filename = result["filename"]
    is_success = result["status"] == "success"
    badge_cls = "badge-success" if is_success else "badge-error"
    badge_txt = "Processado" if is_success else "Erro"
    badge_icon = "✅" if is_success else "❌"

    # --- Header ---
    st.markdown(f"""
    <div class="contract-card">
        <div class="contract-card-header">
            <span style="font-weight:700; font-size:1.1rem; color:#2D3748;">📄 {filename}</span>
            <span class="{badge_cls}">{badge_icon} {badge_txt}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not is_success:
        st.error(f"Erro: {result.get('error_msg', 'Erro desconhecido')}")
        return

    clausulas = result.get("clausulas") or {}
    classif = result.get("classificacao") or {}

    # =============================================
    # RELATÓRIO COMPLETO
    # =============================================
    report_html = _render_clausulas_html(clausulas, classif)
    if report_html:
        st.markdown(report_html, unsafe_allow_html=True)

    # --- Info técnica (discreta) ---
    st.caption(f"Extração: {result.get('metodo_extracao', '—').upper()} | {result['num_paginas']} páginas | {result['num_caracteres']:,} caracteres")

    # --- Botão de download Excel ---
    nome_base = os.path.splitext(result["filename"])[0]
    st.download_button(
        label="📥 Exportar para Excel",
        data=_gerar_excel_contrato(result),
        file_name=f"{nome_base}_analise.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"dl_excel_{result['filename']}",
    )

    st.markdown("---")


# --- Páginas ---
def render_page_processar():
    """Página principal: upload e processamento de contratos."""
    build_institutional_header(
        title="📄 Análise de Contratos",
        subtitle="Plataforma inteligente para leitura automática de contratos de TI"
    )

    # Sobre este Agente — aparece quando não há resultados
    if not st.session_state.get("processing_results"):
        st.markdown("""
        <div class="manual-card" style="margin-bottom: 20px;">
            <h3>📚 Sobre este Agente</h3>
            <p style="margin-bottom: 12px;">
                Sou seu assistente especializado em <b>Análise de Contratos de TI</b>. Minha missão é transformar
                contratos complexos de tecnologia em dados estruturados e acionáveis, garantindo <b>governança</b>,
                <b>rastreabilidade</b> e suporte a <b>auditorias</b> para as áreas de ITAM/SAM (gestão de ativos e licenças de software).
            </p>
            <ul style="padding-left: 20px; margin-bottom: 12px;">
                <li style="margin-bottom:8px;"><b>Classificação Inteligente:</b> identifico automaticamente o tipo de contrato — software, hardware, serviços, mão de obra ou híbrido — com nível de confiança e justificativa detalhada.</li>
                <li style="margin-bottom:8px;"><b>Extração de Cláusulas Críticas:</b> leio o contrato e extraio vigência, custos, licenciamento, SLA, penalidades, condições de rescisão e multas de forma estruturada.</li>
                <li style="margin-bottom:8px;"><b>Compliance e LGPD:</b> identifico cláusulas de proteção de dados, responsáveis pelo tratamento, direitos de auditoria e medidas de segurança exigidas.</li>
                <li style="margin-bottom:8px;"><b>Dados do Fornecedor:</b> capturo razão social, CNPJ, endereço, contatos e obrigações contratuais para associação a ativos e centros de custo.</li>
                <li><b>Obrigações Legais:</b> extraio confidencialidade, propriedade intelectual, foro, garantias, indenizações e limitações de responsabilidade.</li>
            </ul>
            <p style="margin-bottom: 8px;"><b>💡 Como utilizar:</b></p>
            <ol style="padding-left: 20px; margin-bottom: 15px; font-size: 0.95em;">
                <li style="margin-bottom:6px;">Faça o upload de um ou mais contratos em PDF utilizando o campo abaixo</li>
                <li style="margin-bottom:6px;">Clique em <b>"Processar Contratos"</b> e aguarde a análise</li>
                <li>O relatório completo será exibido diretamente nesta página com todas as informações extraídas</li>
            </ol>
            <p style="font-size: 0.9em; color: #718096; border-top: 1px solid #EDF2F7; padding-top: 10px;">
                ✨ <i><b>Dica:</b> envie contratos em PDF com texto nativo (não escaneado) para melhor resultado.
                Você pode enviar até <b>10 arquivos</b> por lote, com limite de <b>50MB</b> no total.</i>
            </p>
        </div>
        """, unsafe_allow_html=True)

    LIMITE_ARQUIVOS = 10
    LIMITE_TAMANHO_MB = 50

    uploaded_files = st.file_uploader(
        f"Upload PDF/DOCX (Máx {LIMITE_ARQUIVOS} arquivos, {LIMITE_TAMANHO_MB}MB total)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state['uploader_key']}"
    )

    if uploaded_files:
        if len(uploaded_files) > LIMITE_ARQUIVOS:
            st.error(f"⚠️ Limite excedido: Máx {LIMITE_ARQUIVOS} arquivos.")
        else:
            tamanho_total = sum(f.size for f in uploaded_files) / (1024 * 1024)

            if tamanho_total > LIMITE_TAMANHO_MB:
                st.error(f"⚠️ Volume total ({tamanho_total:.1f}MB) excede o limite de {LIMITE_TAMANHO_MB}MB.")
            else:
                st.info(f"📎 {len(uploaded_files)} arquivo(s) selecionado(s) — {tamanho_total:.1f}MB")

                if st.button("Processar Contratos", type="primary"):
                    results = []
                    total = len(uploaded_files)
                    with st.status(f"Processando {total} contrato(s)...", expanded=True) as status:
                        for i, f in enumerate(uploaded_files):
                            if total > 1:
                                st.write(f"---\n**Arquivo {i+1} de {total}**")
                            result = processar_contrato_unico(
                                f,
                                log=lambda msg: st.markdown(msg, unsafe_allow_html=True)
                            )
                            results.append(result)

                        sucesso = sum(1 for r in results if r["status"] == "success")
                        if sucesso == total:
                            status.update(label=f"Concluído — {sucesso} contrato(s) processado(s) com sucesso", state="complete")
                        else:
                            status.update(label=f"Concluído — {sucesso} de {total} com sucesso", state="complete")

                    st.session_state["processing_results"] = results
                    st.cache_data.clear()
                    st.session_state["uploader_key"] += 1
                    st.rerun()

    # Exibir resultados do último processamento
    if st.session_state.get("processing_results"):
        results = st.session_state["processing_results"]
        sucesso = sum(1 for r in results if r["status"] == "success")
        if sucesso == 1 and len(results) == 1:
            st.markdown("### ✅ Contrato carregado com sucesso")
        elif sucesso > 0:
            st.markdown(f"### ✅ {sucesso} contrato(s) carregado(s) com sucesso")
        else:
            st.markdown("### ⚠️ Nenhum contrato processado com sucesso")

        for result in results:
            render_contract_card(result)

        # Feedback — registra a interação e exibe widget
        if sucesso > 0:
            # Gerar resumo textual para log
            filenames = ", ".join(r["filename"] for r in results)
            response_summary = f"Processados {sucesso}/{len(results)} contratos: {filenames}"

            # Registrar interação (só uma vez via session_state)
            if "last_response_id" not in st.session_state:
                response_id = log_interaction(
                    mongo_db=MONGO,
                    agent_name=AGENT_NAME,
                    thread_id=st.session_state["thread_id"],
                    user_question=f"Upload de {len(results)} contrato(s): {filenames}",
                    chatbot_response=response_summary,
                )
                st.session_state["last_response_id"] = response_id

            render_feedback_widget(
                mongo_db=MONGO,
                agent_name=AGENT_NAME,
                thread_id=st.session_state["thread_id"],
                response_id=st.session_state["last_response_id"],
            )

        # Botão reiniciar
        st.markdown("")
        if st.button("🔄 Nova Análise", type="secondary", use_container_width=True):
            st.session_state["processing_results"] = []
            st.session_state.pop("last_response_id", None)
            st.session_state["uploader_key"] += 1
            import uuid
            st.session_state["thread_id"] = str(uuid.uuid4())
            st.rerun()

    build_footer()


def render_page_catalogo():
    """Página de catálogo: storage, tabelas de arquivos, exclusão."""
    build_institutional_header(
        title="Catálogo de Documentos",
        subtitle="Gerencie os arquivos locais da plataforma",
        show_logo=False
    )

    # Listagem de Arquivos
    st.markdown("### 📄 Catálogo de Documentos")

    with st.spinner("Atualizando catálogo..."):
        df = get_local_file_catalog()

    if df is not None and not df.empty:
        df_sistema = df[df["Origem"] == "Sistema"].copy()
        df_usuario = df[df["Origem"] == "Upload Usuário"].copy()

        if not df_sistema.empty:
            st.markdown("**🔒 Arquivos do Sistema (Protegidos)**", help=
                        "Estes arquivos representam a base de conhecimento oficial do projeto. Eles são gerenciados pela equipe técnica e são fixos para garantir que o agente siga as regras da empresa.")
            st.dataframe(
                df_sistema.drop(columns=["Origem"]),
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Nome do Documento": st.column_config.TextColumn("Nome", width="large"),
                    "Tamanho (MB)": st.column_config.NumberColumn("Tamanho", format="%.2f MB"),
                    "Data de Upload": st.column_config.TextColumn("Data", width="medium"),
                }
            )
            st.markdown("<br>", unsafe_allow_html=True)

        if not df_usuario.empty:
            st.markdown("**👤 Uploads (Gerenciável)**", help=
                        "Estes são arquivos que foram inseridos pela interface para testes ou análises pontuais. Eles consomem seu limite de armazenamento e você tem total liberdade para excluí-los.")
            st.dataframe(
                df_usuario.drop(columns=["Origem"]),
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Nome do Documento": st.column_config.TextColumn("Nome", width="large"),
                    "Tamanho (MB)": st.column_config.NumberColumn("Tamanho", format="%.2f MB"),
                    "Data de Upload": st.column_config.TextColumn("Data", width="medium"),
                }
            )

            # Área de Exclusão
            st.markdown("---")
            st.markdown("### 🗑️ Área de Exclusão")
            st.markdown("Utilize para remover arquivos antigos ou de teste.")

            with st.container(border=True):
                st.warning("⚠️ Atenção: a exclusão remove o arquivo da base de conhecimento permanentemente.")

                lista_arquivos = df_usuario["Nome do Documento"].tolist()

                arquivos_selecionados = st.multiselect(
                    "Selecione os arquivos que deseja remover:",
                    options=lista_arquivos,
                    placeholder="Clique ou digite para buscar..."
                )

                if arquivos_selecionados:
                    st.markdown(f"**Selecionados para exclusão:** {len(arquivos_selecionados)} arquivo(s).")

                    if st.button("Confirmar Exclusão", type="primary"):
                        progress_bar = st.progress(0, text="Iniciando...")

                        for i, filename in enumerate(arquivos_selecionados):
                            logs = delete_document_process(filename)

                            for log in logs:
                                st.toast(log)

                            progress_bar.progress((i + 1) / len(arquivos_selecionados), text=f"Removendo {filename}...")

                        time.sleep(1)
                        st.cache_data.clear()
                        st.success("Arquivos removidos com sucesso!")
                        st.rerun()

        elif df_usuario.empty:
            st.info("Você ainda não fez upload de nenhum arquivo.")

    else:
        st.warning("⚠️ Nenhum documento encontrado.")

    build_footer()


def render_page_sobre():
    """Página sobre: status e capacidades."""
    build_institutional_header(
        title="Sobre a Plataforma",
        subtitle="Plataforma de leitura automática de contratos de TI",
        show_logo=False
    )

    st.markdown("""
    <div class="status-banner">
        <div class="status-text">PLATAFORMA DE CONTRATOS</div>
        <div class="status-pill">Status: Online 🟢</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="manual-card">
        <h3>✅ Capacidades</h3>
        <ul style="padding-left: 20px;">
            <li style="margin-bottom:10px;"><b>Extração de Texto:</b> extrai texto nativo de contratos PDF para análise estruturada.</li>
            <li style="margin-bottom:10px;"><b>Classificação:</b> classifica automaticamente contratos por tipo (software, hardware, serviços) e identifica fornecedores.</li>
            <li style="margin-bottom:10px;"><b>Cláusulas:</b> extrai e analisa cláusulas contratuais relevantes (LGPD, SLA, penalidades, vigência).</li>
            <li><b>Relatório PDF:</b> gera relatório estruturado em PDF com todas as análises extraídas do contrato.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="manual-card">
        <h3>🚫 Limitações</h3>
        <ul style="padding-left: 20px;">
            <li style="margin-bottom:8px;">As análises baseiam-se estritamente nos documentos processados na ferramenta.</li>
            <li style="margin-bottom:8px;"><b>Não inventa dados:</b> se a informação não existir no documento, será informado.</li>
            <li style="margin-bottom:8px;"><b>Confidencialidade:</b> as análises geradas são para uso interno.</li>
            <li><b>Capacidade da PoC:</b> limite de 10 arquivos por lote e máximo de 50MB no total.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    build_footer()


# --- App principal ---
def build_page(is_authenticated: bool = True, *args, **kwargs) -> None:
    apply_app_style()
    _inject_component_styles()

    if not is_authenticated:
        st.error("🔒 Acesso negado. Por favor, realize o login.")
        return

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "processar"
    if "processing_results" not in st.session_state:
        st.session_state["processing_results"] = []
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0
    if "thread_id" not in st.session_state:
        import uuid
        st.session_state["thread_id"] = str(uuid.uuid4())

    with st.sidebar:
        st.markdown("### Navegação")

        if st.button("📄 Processar Contratos", type="primary" if st.session_state["current_page"] == "processar" else "secondary", use_container_width=True):
            st.session_state["current_page"] = "processar"
            st.rerun()

        if st.button("📂 Catálogo", type="primary" if st.session_state["current_page"] == "catalogo" else "secondary", use_container_width=True):
            st.session_state["current_page"] = "catalogo"
            st.rerun()

        if st.button("ℹ️ Sobre", type="primary" if st.session_state["current_page"] == "sobre" else "secondary", use_container_width=True):
            st.session_state["current_page"] = "sobre"
            st.rerun()

    # Roteamento de páginas
    page = st.session_state["current_page"]
    if page == "processar":
        render_page_processar()
    elif page == "catalogo":
        render_page_catalogo()
    elif page == "sobre":
        render_page_sobre()


if __name__ == "__main__":
    build_page()
