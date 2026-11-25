#!/usr/bin/env python3
"""Entry point para execução do Agente de Análise de Contratos."""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    """Executa o agente Streamlit."""
    parser = argparse.ArgumentParser(description="Executa o Agente de Análise de Contratos")
    parser.add_argument("--port", type=int, default=8501, help="Porta do servidor (default: 8501)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host do servidor (default: 0.0.0.0)")
    parser.add_argument("--dev", action="store_true", help="Modo desenvolvimento com auto-reload")

    args = parser.parse_args()

    # Verificar se agent.py existe
    agent_file = Path(__file__).parent / "agent.py"
    if not agent_file.exists():
        print(f"❌ Erro: Arquivo não encontrado: {agent_file}")
        sys.exit(1)

    print("🚀 Iniciando Agente de Análise de Contratos...")
    print(f"   Servidor: http://{args.host}:{args.port}")
    print()

    # Construir comando Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(agent_file),
        f"--server.port={args.port}",
        f"--server.address={args.host}",
        "--theme.primaryColor=#1E3A8A",
    ]

    if args.dev:
        cmd.append("--server.runOnSave=true")

    # Executar
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n✅ Agente encerrado pelo usuário")
        sys.exit(0)


if __name__ == "__main__":
    main()
