# -*- coding: utf-8 -*-
"""
Geração de embeddings (Ollama) e upload para o Supabase (pgvector).

⚠️ SANITIZADO PARA PORTFÓLIO:
As credenciais foram removidas e substituídas por variáveis de ambiente.
Nunca deixe URLs, chaves de API ou tokens escritos diretamente no código.
"""

import os
import json
import time
import requests
from supabase import create_client, Client

# =========================
# 1. CONFIGURAÇÕES (via variáveis de ambiente)
# =========================

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/embed")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-embedding:4b")

SUPABASE_URL = os.environ["SUPABASE_URL"]          # obrigatório - definir no .env
SUPABASE_KEY = os.environ["SUPABASE_KEY"]          # obrigatório - definir no .env
SUPABASE_TABLE = os.environ.get("SUPABASE_TABLE", "documents")

JSON_PATH = os.environ.get("JSON_PATH", "base_conhecimento_agrupada.json")
LIMITE_ITENS = None       # None para enviar todos; um número para testar
BATCH_SLEEP = 0.2         # pausa entre chamadas para não sobrecarregar o Ollama


def gerar_embedding(texto: str) -> list:
    """Chama o Ollama e retorna o vetor de embedding."""
    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "input": texto},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["embeddings"][0]


def montar_metadata(item: dict) -> dict:
    """Monta o objeto de metadata que vai junto com cada chunk."""
    return {
        "id": item.get("id"),
        "id_pai": item.get("id_pai"),
        "indice": item.get("indice"),
        "titulo": item.get("titulo"),
        "id_topico": item.get("id_topico"),
    }


def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        itens = json.load(f)

    if LIMITE_ITENS:
        itens = itens[:LIMITE_ITENS]

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    sucesso = 0
    falhas = []

    for i, item in enumerate(itens, start=1):
        texto = item.get("texto_embedding") or item.get("conteudo", "")
        if not texto.strip():
            print(f"[{i}/{len(itens)}] SKIP (texto vazio) - id={item.get('id')}")
            continue

        try:
            vetor = gerar_embedding(texto)

            row = {
                "content": texto,
                "metadata": montar_metadata(item),
                "embedding": vetor,
            }

            supabase.table(SUPABASE_TABLE).insert(row).execute()

            sucesso += 1
            print(f"[{i}/{len(itens)}] OK - id={item.get('id')} | dim={len(vetor)}")

        except Exception as e:
            falhas.append((item.get("id"), str(e)))
            print(f"[{i}/{len(itens)}] ERRO - id={item.get('id')}: {e}")

        time.sleep(BATCH_SLEEP)

    print("\n===== RESUMO =====")
    print(f"Sucesso: {sucesso}")
    print(f"Falhas: {len(falhas)}")
    for fid, err in falhas:
        print(f"  - id={fid}: {err}")


if __name__ == "__main__":
    main()
