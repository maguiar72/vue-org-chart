#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importa a Agenda Funcional do CJF para o organograma.

Entrada (a primeira que existir em dados/):
  dados/agenda_funcional.json  -> saída de scripts/capturar_agenda.js (ou lista JSON simples)
  dados/agenda_funcional.csv   -> exportação em CSV (separador ; ou ,)
  dados/agenda_funcional.xlsx  -> exportação em Excel (requer: pip install openpyxl)

Colunas reconhecidas (maiúsculas/minúsculas e acentos são ignorados; sinônimos aceitos):
  nome        : nome, servidor, pessoa, nome completo
  matricula   : matricula, id, siape, login, usuario
  cargo       : cargo, funcao, função, cargo/função, descricao_cargo
  ramal       : ramal, telefone, fone, tel
  email       : email, e-mail, correio
  unidade     : sigla, unidade, lotacao, lotação, setor, sigla_unidade, unidade_sigla
  unidade_nome: nome_unidade, unidade_descricao, descricao_unidade, lotacao_descricao
  foto        : foto, imagem, photo, url_foto, foto_url (URL, data URI base64 ou nome de arquivo em dados/fotos/)
  titular     : titular, chefe, gestor, responsavel (sim/nao, true/false, S/N, 1/0)

Saída:
  dados/pessoas.json            -> consumido por scripts/gerar_dados_cjf.py
  public/photos/<id>.jpg        -> fotos normalizadas (200x200, JPEG)
  dados/nao_localizados.csv     -> pessoas cuja unidade não foi encontrada no organograma

Uso:
  python3 scripts/importar_agenda.py [--sem-fotos] [--arquivo CAMINHO]
"""
import argparse
import base64
import csv
import io
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")
FOTOS_DIR = os.path.join(RAIZ, "public", "photos")
FOTO_EXT = ".jpg"   # deve coincidir com config.photoUrl.suffix em gerar_dados_cjf.py
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import gerar_dados_cjf as ger  # noqa: E402

SINONIMOS = {
    "nome": ["nome", "servidor", "pessoa", "nome completo", "nome_completo", "name"],
    "matricula": ["matricula", "id", "siape", "login", "usuario", "codigo"],
    "cargo": ["cargo", "funcao", "cargo/funcao", "cargo funcao", "descricao_cargo", "descricao cargo", "function", "functionname"],
    "ramal": ["ramal", "telefone", "fone", "tel", "phone"],
    "email": ["email", "e-mail", "correio", "mail"],
    "unidade": ["unidade_sigla", "sigla_unidade", "sigla unidade", "sigla", "unidade", "setor", "lotacao", "department", "departamento"],
    "lotacao_caminho": ["lotacao", "caminho", "hierarquia", "lotacao_completa"],
    "unidade_nome": ["nome_unidade", "nome unidade", "unidade_descricao", "descricao_unidade", "descricao unidade", "lotacao_descricao", "descricao_lotacao",
                     "nome_lotacao", "descricao", "unidade.descricao", "unidade.nome", "lotacao.descricao", "lotacao.nome", "setor.descricao", "setor.nome"],
    "foto": ["arquivo_foto", "foto", "imagem", "photo", "url_foto", "foto_url", "avatar", "picture", "foto_arquivo"],
    "nome_social": ["nomesocial", "nome_social", "nome social"],
    "afastamento": ["afastamento", "afastado_ate", "afastado ate", "retorno"],
    "titular": ["titular", "chefe", "gestor", "responsavel", "chefia", "manager"],
}
PALAVRAS_TITULAR = ("diretor", "secretari", "coordenador", "chefe", "supervisor", "assessor-chefe", "titular")
# Siglas usadas na agenda que diferem das do organograma
APELIDOS_SIGLA = {"CG": "CGJF", "IPE": "IPÊ LAB", "IPE LAB": "IPÊ LAB", "PR": "PRESIDENCIA", "CGJF": "CGJF", "TNU": "TNU", "CEJ": "CEJ"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def mapear_colunas(colunas):
    """Para cada campo, escolhe a coluna cujo nome bate com o sinônimo de maior prioridade."""
    mapa, usadas = {}, set()
    normalizadas = {col: norm(col).replace("_", " ") for col in colunas}
    for campo, alts in SINONIMOS.items():
        for alt in alts:
            alt_n = alt.replace("_", " ")
            col = next((c for c, n in normalizadas.items() if n == alt_n and c not in usadas), None)
            if col is not None:
                mapa[campo] = col
                usadas.add(col)
                break
    return mapa


def valor(reg, mapa, campo):
    col = mapa.get(campo)
    if col is None:
        return ""
    v = reg.get(col, "")
    return "" if v is None else str(v).strip()


# ---------------------------------------------------------------------------
# Leitura da entrada
# ---------------------------------------------------------------------------
def achatar(obj, prefixo=""):
    """Achata dicionários aninhados: {"unidade": {"sigla": "STI"}} -> {"unidade.sigla": "STI"}"""
    out = {}
    for k, v in (obj or {}).items():
        chave = f"{prefixo}{k}"
        if isinstance(v, dict):
            out.update(achatar(v, chave + "."))
        else:
            out[chave] = v
    # cria também apelidos pela última parte da chave ("unidade.sigla" -> "sigla")
    for k in list(out.keys()):
        if "." in k:
            out.setdefault(k.split(".")[-1], out[k])
    return out


def registros_de_json(j, fotos):
    regs = []
    if isinstance(j, dict) and "respostas" in j:            # saída do capturar_agenda.js
        fotos.update(j.get("fotos") or {})
        for r in j["respostas"]:
            js = r.get("json")
            arr = js if isinstance(js, list) else None
            if arr is None and isinstance(js, dict):
                for k in ("data", "items", "content", "result", "registros", "pessoas", "servidores"):
                    if isinstance(js.get(k), list):
                        arr = js[k]
                        break
            if arr:
                regs.extend(achatar(x) for x in arr if isinstance(x, dict))
        for linha in j.get("dom") or []:
            if "colunas" in linha:
                regs.append({"_dom": linha["colunas"], "foto": linha.get("foto", "")})
    elif isinstance(j, list):
        regs = [achatar(x) for x in j if isinstance(x, dict)]
    elif isinstance(j, dict):
        for k in ("data", "items", "content", "result", "registros", "pessoas", "servidores"):
            if isinstance(j.get(k), list):
                regs = [achatar(x) for x in j[k] if isinstance(x, dict)]
                break
    # remove duplicados (mesmo nome + unidade)
    vistos, unicos = set(), []
    for r in regs:
        chave = json.dumps(r, sort_keys=True, ensure_ascii=False)[:500]
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(r)
    return unicos


def ler_entrada(caminho):
    fotos = {}
    if caminho.endswith(".json"):
        with open(caminho, encoding="utf-8") as f:
            return registros_de_json(json.load(f), fotos), fotos
    if caminho.endswith(".csv"):
        with open(caminho, encoding="utf-8-sig", newline="") as f:
            amostra = f.read(4096)
            f.seek(0)
            sep = ";" if amostra.count(";") > amostra.count(",") else ","
            return list(csv.DictReader(f, delimiter=sep)), fotos
    if caminho.endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            sys.exit("Instale o openpyxl para ler .xlsx:  pip install openpyxl")
        ws = openpyxl.load_workbook(caminho, read_only=True).active
        linhas = list(ws.iter_rows(values_only=True))
        cab = [str(c or "") for c in linhas[0]]
        return [dict(zip(cab, l)) for l in linhas[1:] if any(l)], fotos
    sys.exit("Formato não suportado: " + caminho)


# ---------------------------------------------------------------------------
# Índice de unidades do organograma
# ---------------------------------------------------------------------------
def indexar_unidades():
    por_sigla, por_nome = {}, {}

    def walk(no):
        sigla, nome, _staff, filhos = no
        por_sigla[norm(sigla.rstrip("*"))] = sigla
        por_nome[norm(nome)] = sigla
        for f in filhos:
            walk(f)

    walk(ger.ARVORE)
    return por_sigla, por_nome


def localizar_unidade(sigla_txt, nome_txt, por_sigla, por_nome, caminho_txt=""):
    s = norm(sigla_txt).rstrip("*").strip()
    if s.upper() in APELIDOS_SIGLA:
        return APELIDOS_SIGLA[s.upper()]
    if s in por_sigla:
        return por_sigla[s]
    # último trecho do caminho de lotação: "... > SETRAN (SEÇÃO DE TRANSPORTE)"
    if caminho_txt and ">" in caminho_txt:
        ultimo = caminho_txt.split(">")[-1].strip()
        m = re.match(r"^(.+?)\s*\((.+)\)\s*$", ultimo)
        if m:
            sig_c, nome_c = m.group(1).strip(), m.group(2).strip()
            if norm(sig_c).upper() in APELIDOS_SIGLA:
                return APELIDOS_SIGLA[norm(sig_c).upper()]
            if norm(sig_c) in por_sigla:
                return por_sigla[norm(sig_c)]
            if norm(nome_c) in por_nome:
                return por_nome[norm(nome_c)]
            nome_txt = nome_txt or nome_c
    # "GAB-STI", "GAB STI", "GAB/STI"
    s2 = re.sub(r"[\s/]+", "-", s)
    if s2 in por_sigla:
        return por_sigla[s2]
    for txt in (nome_txt, sigla_txt):
        n = norm(txt)
        if n in por_nome:
            return por_nome[n]
    # nome parcial (ex.: "Secretaria de Tecnologia da Informação - STI")
    for txt in (nome_txt, sigla_txt):
        n = norm(txt)
        if len(n) > 8:
            for nome, sig in por_nome.items():
                if nome in n or n in nome:
                    return sig
    return None


# ---------------------------------------------------------------------------
# Fotos
# ---------------------------------------------------------------------------
def salvar_foto(origem, pid, fotos_capturadas, sem_fotos):
    if sem_fotos or not origem:
        return ""
    dados = None
    src = fotos_capturadas.get(origem, origem)
    try:
        if src.startswith("data:"):
            dados = base64.b64decode(src.split(",", 1)[1])
        elif src.lower().startswith("http"):
            import requests
            r = requests.get(src, timeout=15, verify=False)
            if r.ok:
                dados = r.content
        else:
            for cand in (os.path.join(DADOS, src), os.path.join(DADOS, "fotos", src),
                         os.path.join(DADOS, "fotos", os.path.basename(src)), src):
                if os.path.isfile(cand):
                    dados = open(cand, "rb").read()
                    break
    except Exception as e:  # rede interna indisponível, arquivo corrompido etc.
        print("  aviso: foto de %s não obtida (%s)" % (pid, e))
    if not dados:
        return ""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(dados)).convert("RGB")
        lado = min(im.size)
        im = im.crop(((im.width - lado) // 2, (im.height - lado) // 2, (im.width + lado) // 2, (im.height + lado) // 2))
        im = im.resize((200, 200), Image.LANCZOS)
        os.makedirs(FOTOS_DIR, exist_ok=True)
        im.save(os.path.join(FOTOS_DIR, pid + FOTO_EXT), "JPEG", quality=82, optimize=True)
        return pid
    except Exception as e:
        print("  aviso: foto de %s inválida (%s)" % (pid, e))
        return ""


# ---------------------------------------------------------------------------
def eh_verdadeiro(v):
    return norm(v) in ("sim", "s", "true", "1", "x", "yes", "y")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo", help="caminho do arquivo exportado (padrão: dados/agenda_funcional.*)")
    ap.add_argument("--sem-fotos", action="store_true", help="não processa fotos")
    args = ap.parse_args()

    caminho = args.arquivo
    if not caminho:
        for ext in ("json", "csv", "xlsx"):
            c = os.path.join(DADOS, "agenda_funcional." + ext)
            if os.path.exists(c):
                caminho = c
                break
    if not caminho or not os.path.exists(caminho):
        sys.exit("Arquivo de entrada não encontrado. Coloque a exportação em dados/agenda_funcional.(json|csv|xlsx).")

    registros, fotos_capturadas = ler_entrada(caminho)
    if not registros:
        sys.exit("Nenhum registro encontrado em " + caminho)
    print("Registros lidos: %d de %s" % (len(registros), os.path.relpath(caminho, RAIZ)))

    colunas = sorted({k for r in registros for k in r.keys()})
    mapa = mapear_colunas(colunas)
    print("Colunas mapeadas:", {k: v for k, v in mapa.items()})
    if "nome" not in mapa:
        sys.exit("Não identifiquei a coluna de NOME. Colunas disponíveis: %s" % colunas)

    por_sigla, por_nome = indexar_unidades()
    pessoas, nao_localizados, ids = {}, [], set()

    for reg in registros:
        nome = valor(reg, mapa, "nome_social") or valor(reg, mapa, "nome")
        if not nome:
            continue
        matricula = valor(reg, mapa, "matricula")
        pid = re.sub(r"[^A-Za-z0-9]+", "", matricula) or ger.slug(nome)
        base, n = pid, 1
        while pid in ids and pessoas[pid]["name"] != nome:
            n += 1
            pid = "%s_%d" % (base, n)
        ids.add(pid)

        cargo = valor(reg, mapa, "cargo")
        unidade = localizar_unidade(valor(reg, mapa, "unidade"), valor(reg, mapa, "unidade_nome"), por_sigla, por_nome,
                                    valor(reg, mapa, "lotacao_caminho"))
        if not unidade:
            nao_localizados.append({"nome": nome, "unidade": valor(reg, mapa, "unidade"), "unidade_nome": valor(reg, mapa, "unidade_nome"), "cargo": cargo})

        titular_txt = valor(reg, mapa, "titular")
        titular = eh_verdadeiro(titular_txt) if titular_txt else any(p in norm(cargo) for p in PALAVRAS_TITULAR)

        p = pessoas.setdefault(pid, {
            "id": pid,
            "name": nome,
            "photo": "",
            "functionName": cargo,
            "fields": {"E-mail": valor(reg, mapa, "email"), "Ramal": valor(reg, mapa, "ramal"), "Matrícula": matricula,
                       "Afastamento": ("até " + valor(reg, mapa, "afastamento")) if valor(reg, mapa, "afastamento") else ""},
            "lotacoes": [],
            "gerencia": "",
        })
        if unidade and not any(l["sigla"] == unidade for l in p["lotacoes"]):
            p["lotacoes"].append({"sigla": unidade, "role": cargo})
        if unidade and titular and not p["gerencia"]:
            p["gerencia"] = unidade
        if not p["photo"]:
            p["photo"] = salvar_foto(valor(reg, mapa, "foto"), pid, fotos_capturadas, args.sem_fotos)

    # garante um único titular por unidade (o primeiro encontrado)
    titulares = {}
    for p in pessoas.values():
        if p["gerencia"]:
            if p["gerencia"] in titulares:
                p["gerencia"] = ""
            else:
                titulares[p["gerencia"]] = p["id"]

    os.makedirs(DADOS, exist_ok=True)
    saida = os.path.join(DADOS, "pessoas.json")
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(sorted(pessoas.values(), key=lambda x: norm(x["name"])), f, ensure_ascii=False, indent=1)

    if nao_localizados:
        with open(os.path.join(DADOS, "nao_localizados.csv"), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["nome", "unidade", "unidade_nome", "cargo"], delimiter=";")
            w.writeheader()
            w.writerows(nao_localizados)

    com_foto = sum(1 for p in pessoas.values() if p["photo"])
    print("Pessoas: %d | com unidade: %d | titulares: %d | com foto: %d | não localizadas: %d"
          % (len(pessoas), sum(1 for p in pessoas.values() if p["lotacoes"]), len(titulares), com_foto, len(nao_localizados)))
    print("Gerado:", os.path.relpath(saida, RAIZ))
    if nao_localizados:
        print("Verifique dados/nao_localizados.csv e ajuste as siglas (ou a árvore em gerar_dados_cjf.py).")
    print("Próximo passo: python3 scripts/gerar_dados_cjf.py && npm run build")


if __name__ == "__main__":
    main()
