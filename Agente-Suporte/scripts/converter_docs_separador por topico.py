#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor de documentos brutos do Digifarma -> Markdown para RAG.

O que ELE FAZ (automático):
  - Remove o bloco de ÍNDICE redundante do topo (tudo antes de "CONTEUDO").
  - Converte a numeração hierárquica (1, 1.1, 1.1.3.2 ...) em títulos e listas.
  - Agrupa passos de procedimento em listas NUMERADAS (1. 2. 3.).
  - Absorve linhas "órfãs" (sem numeração) como continuação do item anterior.
  - Promove linhas curtas terminadas em ":" a SUBTÍTULOS em negrito.
  - Limpa resíduos de numeração quebrada no meio do texto (ex.: "arquivo.28.1.3.2").
  - Detecta FAQ (Pergunta/Resposta), Regras para IA (⚠️) e Observações (📌).
  - Insere um placeholder de "Contexto:" em cada seção de 1º nível para você preencher.

O que ELE NÃO FAZ (precisa de revisão manual depois):
  - Escrever as frases "Contexto:" reais (ele só deixa o placeholder).
  - Reorganizar tabelas confusas (ex.: preços por estado).
  - Corrigir erros de digitação ou consolidar regras espalhadas.
  - Garantir que TODO subtítulo sugerido faça sentido (confira os **negrito**).

USO (três formas de importar o .txt):
  1) Dois cliques no arquivo OU "python3 converter_docs.py"
     -> abre uma janela para você escolher o .txt (e pergunta o título).
  2) python3 converter_docs.py entrada.txt --titulo "NOTAS FISCAIS"
     -> passando o arquivo direto pela linha de comando.
  3) Se a janela não abrir, o script pede para você colar o caminho do arquivo.

  A saída padrão é <nome_do_arquivo>_convertido.md (ou use -o saida.md).
"""

import re
import sys
import argparse


# ----------------------------------------------------------------------
# Etapa 1 — remover o índice do topo
# ----------------------------------------------------------------------
def remover_indice(texto: str) -> str:
    """
    Os documentos brutos têm um ÍNDICE no topo e depois a palavra
    CONTEUDO (ou CONTEÚDO) seguida do conteúdo real. Cortamos tudo
    antes do marcador CONTEUDO. Se não houver marcador, devolve o texto.
    """
    m = re.search(r'^\s*CONTE[UÚ]DO\s*$', texto, flags=re.MULTILINE | re.IGNORECASE)
    if m:
        return texto[m.end():].lstrip('\n')
    # Sem marcador explícito: tenta achar a primeira linha "1 - TITULO"
    # que apareça pela SEGUNDA vez (a 1ª é no índice).
    ocorrencias = [mm.start() for mm in re.finditer(r'^\s*1\s*-\s*\S', texto, flags=re.MULTILINE)]
    if len(ocorrencias) >= 2:
        return texto[ocorrencias[1]:].lstrip('\n')
    return texto


# ----------------------------------------------------------------------
# Etapa 2 — classificar cada linha pela numeração
# ----------------------------------------------------------------------
# Captura prefixos como: "1 -", "1.1-", "1.1.3.2-", "6.9.6.4.1-"
RE_NUMERADO = re.compile(r'^\s*(\d+(?:\.\d+)*)\s*[-–.]?\s*(.*)$')


def nivel_da_numeracao(num: str) -> int:
    """Conta quantos níveis tem o prefixo: '1' -> 1, '1.1' -> 2, '1.1.3' -> 3."""
    return num.count('.') + 1


def eh_regra_ia(conteudo: str) -> bool:
    return bool(re.match(r'(?i)^\s*regra(s)?\s+para\s+ia\b', conteudo))


def eh_pergunta(conteudo: str) -> bool:
    return bool(re.match(r'(?i)^\s*pergunta\s*[:\-]', conteudo)) or conteudo.strip().endswith('?')


def eh_resposta(conteudo: str) -> bool:
    return bool(re.match(r'(?i)^\s*resposta\s*[:\-]', conteudo))


def eh_titulo_faq(conteudo: str) -> bool:
    return bool(re.search(r'(?i)\b(perguntas?\s+esperadas?|base\s+faq|faq)\b', conteudo))


def eh_observacao(conteudo: str) -> bool:
    return bool(re.match(r'(?i)^\s*(observa[çc][aã]o|aten[çc][aã]o|importante|nota)\b', conteudo))


# --- Melhoria 3: limpar resíduos de numeração quebrada no MEIO do texto ---
# Ex.: "geração de arquivo.28.1.3.2" -> "geração de arquivo."
#      "no F7.6.9.6.4" -> "no F7."
RE_LIXO_NUM = re.compile(r'(?<=\S)\.\d+(?:\.\d+){1,}\b')


def limpar_residuo_numeracao(texto: str) -> str:
    # remove sequências tipo .28.1.3.2 grudadas no fim de uma palavra/frase
    texto = RE_LIXO_NUM.sub('.', texto)
    # colapsa pontos duplicados que possam sobrar
    texto = re.sub(r'\.{2,}', '.', texto)
    return texto.strip()


# --- Melhoria 4: detectar linha que deve virar SUBTÍTULO em negrito ---
# Heurística: linha curta, termina em ":" e NÃO parece um passo/frase comum.
def eh_subtitulo_bloco(conteudo: str) -> bool:
    c = conteudo.strip()
    if not c.endswith(':'):
        return False
    miolo = c[:-1].strip()
    # curto (poucas palavras) e sem pontuação interna de frase
    palavras = miolo.split()
    if len(palavras) > 7:
        return False
    if any(p in miolo for p in ('.', ';', '?')):
        return False
    return True


def converter(texto: str, titulo_doc: str = "") -> str:
    texto = remover_indice(texto)
    linhas = texto.split('\n')

    saida = []
    if titulo_doc:
        saida.append(f"# BASE DE CONHECIMENTO — {titulo_doc.upper()} (DIGIFARMA)")
        saida.append("")
        saida.append("> Documento convertido automaticamente para markdown. "
                     "REVISAR: preencher as frases 'Contexto:' de cada seção, "
                     "conferir tabelas/regras e os subtítulos sugeridos.")
        saida.append("")

    primeira_secao_vista = False
    # estado para listas numeradas (Melhoria 2): contador do bloco de passos atual
    contador_passo = 0

    def fechar_lista():
        nonlocal contador_passo
        contador_passo = 0

    i = 0
    n = len(linhas)
    while i < n:
        bruta = linhas[i].rstrip()
        i += 1

        if not bruta.strip():
            if saida and saida[-1] != "":
                saida.append("")
            fechar_lista()
            continue

        m = RE_NUMERADO.match(bruta)

        # ----------------------------------------------------------
        # Melhoria 1: linha SEM numeração
        # ----------------------------------------------------------
        if not m:
            conteudo = limpar_residuo_numeracao(bruta.strip())

            # vira subtítulo em negrito? (Melhoria 4)
            if eh_subtitulo_bloco(conteudo):
                if saida and saida[-1] != "":
                    saida.append("")
                saida.append(f"**{conteudo}**")
                fechar_lista()  # subtítulo inicia um novo bloco de passos
                continue

            # se estamos dentro de um bloco de lista, ABSORVE como continuação
            ultimo = saida[-1] if saida else ""
            dentro_de_lista = ultimo.lstrip().startswith(('-', '1.', '2.', '3.', '4.',
                                                          '5.', '6.', '7.', '8.', '9.')) \
                or bool(re.match(r'^\s*\d+\.', ultimo))
            if dentro_de_lista and ultimo.strip():
                # anexa o texto órfão ao item anterior (continuação da frase)
                saida[-1] = ultimo.rstrip() + " " + conteudo
                continue

            # caso contrário, parágrafo normal
            saida.append(conteudo)
            continue

        num, conteudo = m.group(1), m.group(2).strip()
        conteudo = limpar_residuo_numeracao(conteudo)
        nivel = nivel_da_numeracao(num)

        # --- Nível 1: título de seção principal (##) + placeholder de contexto
        # Cada seção (assunto) é ENVOLVIDA por --- : abre com --- antes do título
        # e a seção seguinte abre o próprio ---, de modo que o conteúdo de cada
        # assunto fica isolado entre separadores. O fechamento final é feito no fim.
        if nivel == 1:
            if saida and saida[-1] != "":
                saida.append("")
            saida.append("---")
            saida.append("")
            saida.append(f"## {num} — {conteudo}")
            saida.append("")
            saida.append(f"*Contexto: [PREENCHER — do que trata a seção {num} ({conteudo})].*")
            saida.append("")
            primeira_secao_vista = True
            fechar_lista()
            continue

        # --- Nível 2: subtítulo (###)
        if nivel == 2:
            if saida and saida[-1] != "":
                saida.append("")
            saida.append(f"### {num} — {conteudo}")
            saida.append("")
            fechar_lista()
            continue

        # --- Regras para IA: destaca com ⚠️
        if eh_regra_ia(conteudo):
            texto_regra = re.sub(r'(?i)^\s*regra(s)?\s+para\s+ia\s*[:\-]?\s*', '', conteudo)
            if saida and saida[-1] != "":
                saida.append("")
            saida.append(f"⚠️ Regra para IA: {texto_regra.strip()}")
            fechar_lista()
            continue

        # --- Observações: destaca com 📌
        if eh_observacao(conteudo):
            if saida and saida[-1] != "":
                saida.append("")
            saida.append(f"📌 {conteudo}")
            fechar_lista()
            continue

        # --- FAQ
        if eh_titulo_faq(conteudo):
            saida.append(f"**FAQ — {conteudo}**")
            saida.append("")
            fechar_lista()
            continue
        if eh_pergunta(conteudo):
            q = re.sub(r'(?i)^\s*pergunta\s*[:\-]\s*', '', conteudo)
            saida.append(f"**P: {q.strip()}**")
            fechar_lista()
            continue
        if eh_resposta(conteudo):
            r = re.sub(r'(?i)^\s*resposta\s*[:\-]\s*', '', conteudo)
            saida.append(f"R: {r.strip()}")
            saida.append("")
            fechar_lista()
            continue

        # ----------------------------------------------------------
        # Melhoria 2 + 4: subtítulo de bloco OU passo numerado
        # ----------------------------------------------------------
        # se o conteúdo é curto e termina em ":", é um subtítulo de bloco
        if eh_subtitulo_bloco(conteudo):
            if saida and saida[-1] != "":
                saida.append("")
            saida.append(f"**{conteudo}**")
            fechar_lista()
            continue

        # senão, é um passo -> lista NUMERADA dentro do bloco atual
        contador_passo += 1
        saida.append(f"{contador_passo}. {conteudo}")

    # limpeza final: no máximo 1 linha vazia seguida
    resultado = []
    for ln in saida:
        if ln == "" and resultado and resultado[-1] == "":
            continue
        resultado.append(ln)

    # fecha a última seção com --- (se houve ao menos uma seção)
    if primeira_secao_vista:
        while resultado and resultado[-1] == "":
            resultado.pop()
        resultado.append("")
        resultado.append("---")

    return "\n".join(resultado).strip() + "\n"


# ----------------------------------------------------------------------
# Importação do TXT — três formas de escolher o arquivo
# ----------------------------------------------------------------------
def escolher_arquivo_dialogo():
    """Abre uma janela do sistema para o usuário escolher o .txt.
    Retorna o caminho ou None se o tkinter não estiver disponível."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        raiz = tk.Tk()
        raiz.withdraw()  # esconde a janela principal
        raiz.attributes("-topmost", True)
        caminho = filedialog.askopenfilename(
            title="Selecione o documento bruto (.txt)",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        raiz.destroy()
        return caminho or None
    except Exception:
        return None


def ler_txt(caminho: str) -> str:
    """Lê o txt tentando UTF-8 e, se falhar, latin-1 (acentos do Windows)."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(caminho, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # último recurso: ignora bytes problemáticos
    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def obter_entrada(args):
    """Decide de onde vem o arquivo: argumento da linha de comando,
    janela de seleção, ou caminho digitado manualmente."""
    # 1) veio pela linha de comando
    if args.entrada:
        return args.entrada

    # 2) tenta abrir a janela de seleção
    print("Abrindo janela para você escolher o arquivo .txt...")
    caminho = escolher_arquivo_dialogo()
    if caminho:
        return caminho

    # 3) sem janela disponível: pede o caminho digitado
    print("(Não foi possível abrir a janela de seleção.)")
    caminho = input("Cole ou digite o caminho do arquivo .txt: ").strip().strip('"').strip("'")
    return caminho or None


# ----------------------------------------------------------------------
# CLI / interativo
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Converte documento bruto Digifarma para markdown.")
    ap.add_argument("entrada", nargs="?", default=None,
                    help="arquivo .txt de entrada (opcional; se omitido, abre janela de seleção)")
    ap.add_argument("-o", "--saida", help="arquivo .md de saída")
    ap.add_argument("--titulo", default="", help="título do documento (ex.: 'NOTAS FISCAIS')")
    args = ap.parse_args()

    entrada = obter_entrada(args)
    if not entrada:
        print("Nenhum arquivo selecionado. Encerrando.")
        sys.exit(1)

    import os
    if not os.path.isfile(entrada):
        print(f"Arquivo não encontrado: {entrada}")
        sys.exit(1)

    texto = ler_txt(entrada)

    # título: usa o passado por argumento ou pergunta (se rodando interativo)
    titulo = args.titulo
    if not titulo and args.entrada is None:
        titulo = input("Título do documento (ex.: NOTAS FISCAIS) — Enter para pular: ").strip()

    md = converter(texto, titulo)

    saida = args.saida or re.sub(r'\.[^.]+$', '', entrada) + "_convertido.md"
    with open(saida, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\nOK. Markdown gerado em: {saida}")
    print(f"  Linhas de saída: {md.count(chr(10))}")
    print(f"  Placeholders 'Contexto:' para preencher: {md.count('[PREENCHER')}")
    print(f"  Regras para IA marcadas: {md.count('⚠️ Regra para IA')}")


if __name__ == "__main__":
    main()
