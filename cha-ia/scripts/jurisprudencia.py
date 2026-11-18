#!/usr/bin/env python3
"""Cha.IA - busca de jurisprudência direto nos portais oficiais (leitura literal).

Devolve as fichas com o texto da ementa como publicado pelo tribunal, para a
verificação literal. Só funciona com os domínios liberados nas configurações de
capacidades do Claude (lista de domínios permitidos).

Uso:
  python3 jurisprudencia.py teste
  python3 jurisprudencia.py stj  "termos da pesquisa" [--max 5] [--inicio 1] [--inteiro-teor DIR] [--json SAIDA.json]
  python3 jurisprudencia.py tjms "termos da pesquisa" [--max 5] [--pagina 1] [--inteiro-teor DIR] [--json SAIDA.json]
  python3 jurisprudencia.py stf  "termos da pesquisa"

Sintaxe de pesquisa:
  STJ (SCON): operadores e, ou, nao, adj, prox, "frase exata"; ex.: "provedor e porta adj logica"
  TJMS (e-SAJ): palavras-chave; aspas para frase exata.

Status por portal (testado em 18/11/2026):
  STJ  - busca e inteiro teor (PDF) funcionando por acesso direto.
  STF  - o portal bloqueia acesso automatizado (firewall F5, erro 403): usar navegador ou PDF.
  TJMS - implementado no padrão e-SAJ; validar com o comando "teste" na primeira conversa.
"""
import argparse, datetime, html, json, re, shutil, subprocess, sys
from pathlib import Path
from urllib.parse import urlencode
import urllib.request, http.cookiejar

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
HOJE = datetime.date.today().strftime("%d/%m/%Y")


class Sessao:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def get(self, url, params=None, data=None, ref=None, timeout=60, enc=None):
        if params:
            url = url + ("&" if "?" in url else "?") + urlencode(params, encoding=enc or "utf-8")
        body = urlencode(data, encoding=enc or "utf-8").encode() if data is not None else None
        req = urllib.request.Request(url, data=body, headers={
            "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*",
            "Accept-Language": "pt-BR,pt;q=0.9", **({"Referer": ref} if ref else {})})
        with self.op.open(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(), r.geturl()


def limpa(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    return s.strip()


def pdf_texto(caminho):
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", str(caminho), "-"], capture_output=True, text=True)
        return out.stdout
    return ""


# ------------------------------------------------------------------ STJ
STJ = "https://scon.stj.jus.br/SCON/"

def stj(termos, maximo=5, inicio=1, inteiro_teor=None):
    s = Sessao()
    s.get(STJ)
    campos = {"preConsultaPP": "", "pesquisaAmigavel": " " + termos, "acao": "pesquisar",
              "novaConsulta": "true", "i": str(inicio), "b": "ACOR", "livre": termos,
              "filtroPorOrgao": "", "filtroPorMinistro": "", "filtroPorNota": "", "data": "",
              "operador": "e", "thesaurus": "JURIDICO", "p": "true", "tp": "T", "processo": "",
              "classe": "", "uf": "", "relator": "", "dtpb": "", "dtpb1": "", "dtpb2": "",
              "dtde": "", "dtde1": "", "dtde2": "", "orgao": "", "ementa": "", "nota": "", "ref": ""}
    st, ct, raw, url = s.get(STJ + "pesquisar.jsp", params=campos, ref=STJ)
    t = raw.decode("iso-8859-1", "ignore")
    total = re.search(r"Documento\s+\d+\s+de\s+(\d+)", t)
    docs = t.split('class="documento"')[1:]
    fichas = []
    for blk in docs[:maximo]:
        f = {"tribunal": "STJ", "caminho": "acesso direto (scon.stj.jus.br)", "consulta_em": HOJE,
             "url_pesquisa": STJ, "termos": termos}
        for m in re.finditer(r'class="docTitulo">(.*?)</div>\s*<div class="docTexto">(.*?)</div>', blk, re.S):
            f[limpa(m.group(1))] = limpa(m.group(2))
        ta = re.search(r'<textarea[^>]*class="textareaSemformatacao"[^>]*>(.*?)</textarea>', blk, re.S)
        if ta:
            em = html.unescape(ta.group(1)).strip()
            ref = re.search(r"\n(\([^()\n]*(?:\([^()]*\)[^()\n]*)*\))\s*$", em)
            f["ementa"] = em[:ref.start()].strip() if ref else em
            f["referencia_oficial"] = ref.group(1) if ref else ""
        else:
            f["ementa"] = f.get("Ementa", "")
        it = re.search(r"inteiro_teor\('([^']+)'\)", blk)
        f["url_inteiro_teor"] = ("https://scon.stj.jus.br" + it.group(1)) if it else ""
        fichas.append(f)
    if inteiro_teor:
        Path(inteiro_teor).mkdir(parents=True, exist_ok=True)
        for n, f in enumerate(fichas, 1):
            if not f["url_inteiro_teor"]:
                continue
            try:
                _, ct, pdf, _ = s.get(f["url_inteiro_teor"], ref=STJ)
                if "pdf" in ct.lower():
                    p = Path(inteiro_teor) / f"STJ_{n:02d}.pdf"
                    p.write_bytes(pdf)
                    f["arquivo_inteiro_teor"] = str(p)
                    f["inteiro_teor_texto"] = pdf_texto(p)[:200000]
            except Exception as e:
                f["erro_inteiro_teor"] = str(e)
    return {"tribunal": "STJ", "termos": termos, "total": int(total.group(1)) if total else len(docs),
            "fichas": fichas}


# ------------------------------------------------------------------ TJMS (e-SAJ)
TJMS = "https://esaj.tjms.jus.br/cjsg/"

def tjms(termos, maximo=5, pagina=1, inteiro_teor=None):
    s = Sessao()
    s.get(TJMS + "consultaCompleta.do")
    dados = {"conversationId": "", "dados.buscaInteiroTeor": termos, "dados.pesquisarComSinonimos": "S",
             "dados.buscaEmenta": "", "dados.nuProcOrigem": "", "dados.nuRegistro": "",
             "agenteSelectedEntitiesList": "", "contadoragente": "0", "contadorMaioragente": "0",
             "codigoCr": "", "codigoTr": "", "nmAgente": "", "juizProlatorSelectedEntitiesList": "",
             "contadorjuizProlator": "0", "contadorMaiorjuizProlator": "0", "codigoJuizCr": "",
             "codigoJuizTr": "", "nmJuiz": "", "classesTreeSelection.values": "",
             "classesTreeSelection.text": "", "assuntosTreeSelection.values": "",
             "assuntosTreeSelection.text": "", "comarcaSelectedEntitiesList": "", "contadorcomarca": "0",
             "contadorMaiorcomarca": "0", "cdComarca": "", "nmComarca": "",
             "secaoRecursalSelectedEntitiesList": "", "contadorsecaoRecursal": "0",
             "contadorMaiorsecaoRecursal": "0", "cdSecao": "", "nmSecao": "",
             "dados.dtJulgamentoInicio": "", "dados.dtJulgamentoFim": "", "dados.dtPublicacaoInicio": "",
             "dados.dtPublicacaoFim": "", "dados.origensSelecionadas": "T", "tipoDecisaoSelecionados": "A",
             "dados.ordenarPor": "dtPublicacao"}
    st, ct, raw, url = s.get(TJMS + "resultadoCompleta.do", data=dados, ref=TJMS + "consultaCompleta.do")
    if pagina > 1:
        st, ct, raw, url = s.get(TJMS + "trocaDePagina.do", params={"tipoDeDecisao": "A", "pagina": str(pagina)},
                                 ref=TJMS + "resultadoCompleta.do")
    t = raw.decode("utf-8", "ignore")
    total = re.search(r"Resultados\s+\d+\s+a\s+\d+\s+de\s+(\d+)", limpa(t))
    blocos = re.split(r'<tr[^>]*class="fundocinza1"', t)[1:]
    rot = ["Classe/Assunto", "Relator(a)", "Comarca", "Órgão julgador", "Data do julgamento",
           "Data de publicação", "Data de registro", "Ementa", "Outros números"]
    fichas = []
    for blk in blocos[:maximo]:
        f = {"tribunal": "TJMS", "caminho": "acesso direto (esaj.tjms.jus.br)", "consulta_em": HOJE,
             "url_pesquisa": TJMS + "consultaCompleta.do", "termos": termos}
        num = re.search(r'class="[^"]*downloadEmenta[^"]*"[^>]*>(.*?)</a>', blk, re.S)
        f["Processo"] = limpa(num.group(1)) if num else ""
        cd = re.search(r'cdacordao="(\d+)"[^>]*cdforo="(\d+)"', blk, re.I)
        f["url_inteiro_teor"] = (f"{TJMS}getArquivo.do?cdAcordao={cd.group(1)}&cdForo={cd.group(2)}"
                                 if cd else "")
        # a ementa completa fica no bloco oculto; usa o maior texto disponível
        ocultas = re.findall(r'<div[^>]*style="display:\s*none;?"[^>]*>(.*?)</div>', blk, re.S)
        texto = limpa(blk)
        for i, r in enumerate(rot):
            m = re.search(re.escape(r) + r"\s*:\s*(.*?)(?=(?:" + "|".join(re.escape(x) for x in rot) + r")\s*:|$)",
                          texto, re.S)
            if m:
                f[r] = m.group(1).strip()
        if ocultas:
            em = max((limpa(o) for o in ocultas), key=len)
            em = re.sub(r"^Ementa\s*:\s*", "", em)
            if len(em) > len(f.get("Ementa", "")):
                f["Ementa"] = em
        f["ementa"] = f.get("Ementa", "")
        fichas.append(f)
    if inteiro_teor:
        Path(inteiro_teor).mkdir(parents=True, exist_ok=True)
        for n, f in enumerate(fichas, 1):
            if not f["url_inteiro_teor"]:
                continue
            try:
                _, ct, pdf, _ = s.get(f["url_inteiro_teor"], ref=TJMS + "resultadoCompleta.do")
                if "pdf" in ct.lower():
                    p = Path(inteiro_teor) / f"TJMS_{n:02d}.pdf"
                    p.write_bytes(pdf)
                    f["arquivo_inteiro_teor"] = str(p)
                    f["inteiro_teor_texto"] = pdf_texto(p)[:200000]
            except Exception as e:
                f["erro_inteiro_teor"] = str(e)
    return {"tribunal": "TJMS", "termos": termos,
            "total": int(total.group(1)) if total else len(blocos), "fichas": fichas,
            "aviso": "" if blocos else "Nenhum resultado lido: conferir a página no navegador (o leiaute do e-SAJ pode ter mudado)."}


# ------------------------------------------------------------------ STF
def stf(termos):
    s = Sessao()
    try:
        st, ct, raw, url = s.get("https://jurisprudencia.stf.jus.br/pages/search")
        bloqueado = b"was rejected" in raw
    except Exception as e:
        return {"tribunal": "STF", "erro": str(e), "orientacao": "Usar navegador ou PDF do acórdão."}
    return {"tribunal": "STF", "termos": termos, "bloqueado": True,
            "orientacao": ("O portal do STF bloqueia consultas automatizadas (firewall), "
                           "mesmo com o domínio liberado. Conferir a ementa pelo navegador "
                           "(jurisprudencia.stf.jus.br) ou pelo PDF do acórdão anexado."),
            "pagina_inicial_acessivel": not bloqueado}


# ------------------------------------------------------------------ teste
def teste():
    res = {}
    for nome, fn in (("STJ", lambda: stj("marco adj civil", 1)),
                     ("TJMS", lambda: tjms("marco civil da internet", 1))):
        try:
            r = fn()
            ok = bool(r["fichas"]) and bool(r["fichas"][0].get("ementa"))
            res[nome] = "ok: ementa literal lida" if ok else "acesso ok, mas nenhuma ementa extraída"
        except Exception as e:
            res[nome] = f"falhou: {type(e).__name__}: {e}"
    r = stf("teste")
    res["STF"] = "bloqueado pelo portal: usar navegador ou PDF" if r.get("bloqueado") else str(r)
    return res


def ficha_md(f, n):
    def g(*ks):
        for k in ks:
            if f.get(k):
                return f[k]
        return "não confirmado"
    proc = " · ".join(x.strip() for x in g("Processo").splitlines() if x.strip())
    linhas = [f"**{n}. {proc}**",
              f"- Tribunal e órgão julgador: {f['tribunal']} – {g('Órgão Julgador', 'Órgão julgador')}",
              f"- Relator(a): {g('Relator', 'Relator(a)')}",
              f"- Data de julgamento: {g('Data do Julgamento', 'Data do julgamento')}",
              f"- Data de publicação: {g('Data da Publicação/Fonte', 'Data de publicação')}",
              "- Ementa:", "", "> " + g("ementa").replace("\n", "\n> "), ""]
    if f.get("referencia_oficial"):
        linhas.append(f"- Referência oficial: {f['referencia_oficial']}")
    linhas += [f"- Inteiro teor: {f.get('url_inteiro_teor') or 'não localizado'}",
               f"- Fonte: {f['url_pesquisa']} (pesquisa: «{f.get('termos', '')}»; consulta em {f['consulta_em']})",
               f"- Caminho de verificação: {f['caminho']}", ""]
    return "\n".join(linhas)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("tribunal", choices=["stj", "tjms", "stf", "teste"])
    ap.add_argument("termos", nargs="?", default="")
    ap.add_argument("--max", type=int, default=5)
    ap.add_argument("--inicio", type=int, default=1)
    ap.add_argument("--pagina", type=int, default=1)
    ap.add_argument("--inteiro-teor", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    if a.tribunal == "teste":
        print(json.dumps(teste(), ensure_ascii=False, indent=2)); sys.exit()
    if a.tribunal == "stf":
        print(json.dumps(stf(a.termos), ensure_ascii=False, indent=2)); sys.exit()
    fn = stj if a.tribunal == "stj" else tjms
    kw = {"inicio": a.inicio} if a.tribunal == "stj" else {"pagina": a.pagina}
    r = fn(a.termos, a.max, inteiro_teor=a.inteiro_teor or None, **kw)
    if a.json:
        Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{r['tribunal']}: {r['total']} resultado(s) para «{r['termos']}»; exibindo {len(r['fichas'])}.\n")
    if r.get("aviso"):
        print(r["aviso"] + "\n")
    for n, f in enumerate(r["fichas"], 1):
        print(ficha_md(f, n))
