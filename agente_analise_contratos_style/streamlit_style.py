"""
Tema visual do Agente de Análise de Contratos para Streamlit
============================================================

Este módulo contém apenas funções de design (CSS, header, footer, configuração de página).
Sem lógica de processamento - apenas identidade visual padronizada.

Uso:
    from agente_analise_contratos_style.streamlit_style import (
        init_page_config,
        apply_app_style,
        build_institutional_header,
        build_footer
    )

    init_page_config("Título da Página")
    apply_app_style()
    build_institutional_header("Título", "Subtítulo")
    # ... seu código ...
    build_footer("Linha 1", "Linha 2")
"""

import base64
import os
from datetime import datetime

import streamlit as st

# Paleta do tema
PRIMARY_COLOR = "#1E3A8A"    # azul índigo
SECONDARY_COLOR = "#0F766E"  # verde-azulado
PRIMARY_RGB = "30, 58, 138"

_PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ICON_PATH = os.path.join(_PARENT_DIR, "agente_analise_contratos_icons", "header_logo.svg")


def init_page_config(page_title: str) -> None:
    """
    Configura a página Streamlit com favicon e layout wide.
    Deve ser chamada ANTES de qualquer outro comando Streamlit.

    Args:
        page_title: Título da página exibido na aba do navegador
    """
    st.set_page_config(
        page_title=page_title,
        page_icon="📑",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def apply_app_style() -> None:
    """
    Aplica o CSS do tema para páginas Streamlit.
    Apenas design (cores, tipografia, espaçamento, componentes).
    """
    st.markdown(
        f"""
        <style>
        /* Configuração geral do container */
        .block-container {{
            padding-top: 1rem;
            max-width: 1200px;
        }}

        /* Estilo para papel de relatório */
        .report-paper {{
            background-color: white;
            border-radius: 12px;
            padding: 30px 45px;
            color: #2D3748;
            font-family: 'Segoe UI', sans-serif;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-top: 10px;
        }}

        /* Título do documento */
        .doc-title {{
            font-size: 24px;
            font-weight: 700;
            color: {PRIMARY_COLOR};
            margin-bottom: 20px;
            border-bottom: 2px solid #EDF2F7;
            padding-bottom: 10px;
        }}

        /* Títulos de seção */
        .section-title {{
            display: block;
            font-size: 18px;
            font-weight: 700;
            color: {PRIMARY_COLOR};
            margin-top: 30px;
            margin-bottom: 12px;
            border-left: 4px solid {PRIMARY_COLOR};
            padding-left: 12px;
        }}

        /* Header com degradê do tema */
        .institutional-header {{
            background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%);
            color: white;
            padding: 25px 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .logo-container {{
            display: flex;
            align-items: center;
        }}

        .logo-container img {{
            height: 50px;
            width: auto;
        }}

        .header-content {{
            flex: 1;
        }}

        .header-title {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }}

        .header-subtitle {{
            margin: 5px 0 0 0;
            font-size: 14px;
            opacity: 0.95;
        }}

        /* Botões primários */
        .stButton > button {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
            border-radius: 12px !important;
            border: none !important;
            font-weight: 600 !important;
            transition: background-color 0.3s ease;
            padding: 0.5rem 1.5rem;
        }}
        .stButton > button:hover {{
            background-color: {SECONDARY_COLOR} !important;
            color: white !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba({PRIMARY_RGB}, 0.3);
        }}

        /* Botões de download */
        .stDownloadButton > button {{
            background-color: {PRIMARY_COLOR} !important;
            color: white !important;
            border-radius: 12px !important;
            border: none !important;
            font-weight: 600 !important;
        }}
        .stDownloadButton > button:hover {{
            background-color: {SECONDARY_COLOR} !important;
        }}

        /* Estilo para tabelas */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            border-radius: 12px;
            overflow: hidden;
        }}
        th {{
            background-color: #F7FAFC;
            padding: 12px;
            border: 1px solid #EDF2F7;
            text-align: left;
            font-weight: 600;
            color: #2D3748;
        }}
        td {{
            padding: 10px;
            border: 1px solid #EDF2F7;
        }}

        /* Cards informativos */
        .info-card {{
            background-color: #F7FAFC;
            border-left: 4px solid {PRIMARY_COLOR};
            padding: 15px 20px;
            border-radius: 8px;
            margin: 15px 0;
        }}

        /* Loading spinner customizado */
        .stSpinner > div {{
            border-color: {PRIMARY_COLOR} transparent transparent transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_base64_file(path: str) -> str | None:
    """Converte um arquivo para base64 se existir."""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def build_institutional_header(title: str, subtitle: str, show_logo: bool = True) -> None:
    """
    Renderiza o header: ícone + título do agente + subtítulo.

    Args:
        title: Nome do agente (ex: "Análise de Contratos")
        subtitle: Subtítulo descritivo
        show_logo: Se True, exibe o ícone acima do título
    """
    b64_icon = _get_base64_file(_ICON_PATH) if show_logo else None

    st.markdown(
        f"""
        <style>
        .header-container {{
            background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%);
            color: white;
            padding: 40px 30px 35px 30px;
            border-radius: 16px;
            margin-bottom: 28px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 6px 20px rgba({PRIMARY_RGB}, 0.25);
        }}
        .header-icon {{
            width: 96px;
            height: auto;
            margin-bottom: 16px;
        }}
        .header-title {{
            margin: 0;
            font-size: 2.4rem;
            font-weight: 700;
            color: white !important;
            line-height: 1.15;
            letter-spacing: -0.3px;
        }}
        .header-subtitle {{
            margin-top: 12px;
            font-size: 15px;
            opacity: 0.90;
            font-weight: 400;
            letter-spacing: 0.3px;
            line-height: 1.5;
            max-width: 600px;
            color: white;
        }}
        @media (max-width: 768px) {{
            .header-container {{ padding: 28px 16px 24px 16px; }}
            .header-icon {{ width: 72px; }}
            .header-title {{ font-size: 1.8rem; }}
            .header-subtitle {{ font-size: 13px; margin-top: 8px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    header_html = '<div class="header-container">'

    if b64_icon:
        header_html += f'<img src="data:image/svg+xml;base64,{b64_icon}" class="header-icon" alt="Ícone">'

    header_html += f'<h1 class="header-title">{title}</h1>'
    header_html += f'<p class="header-subtitle">{subtitle}</p>'
    header_html += '</div>'

    st.markdown(header_html, unsafe_allow_html=True)


def build_footer(line_1: str = "Agente de Análise de Contratos v1.0", line_2: str = "Sistema inteligente com IA para análise de contratos de TI (ITAM/SAM)") -> None:
    """
    Renderiza rodapé (apenas design).

    Args:
        line_1: Primeira linha do rodapé
        line_2: Segunda linha do rodapé
    """
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #718096; font-size: 12px; padding: 20px;">
            <p>{line_1}</p>
            <p>{line_2}</p>
            <p style="opacity: 0.75; margin-top: 10px;">{datetime.now().year}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
