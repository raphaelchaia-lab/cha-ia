#!/usr/bin/env python3
"""Cha.IA - gera documentos sobre o papel timbrado do titular.

O timbrado é um arquivo .docx do próprio titular (cabeçalho, rodapé, margens e
fontes já definidos). O script abre esse arquivo, apaga o corpo e escreve o
conteúdo novo, preservando cabeçalho, rodapé e configuração de página.

Uso:
  python3 cha_docs.py peca ENTRADA.md SAIDA.docx --modelo TIMBRADO.docx
  python3 cha_docs.py pdf  ENTRADA.md SAIDA.pdf  --modelo TIMBRADO.docx --titulo "RELATÓRIO RESERVADO" [--paisagem]

Sem --modelo (ou com arquivo inexistente), gera em A4 simples, sem timbrado.
O modo pdf monta um DOCX sobre o mesmo timbrado e converte com LibreOffice
(soffice), com uma tarja de uso interno no topo.

Marcação aceita no .md:
  # Texto         -> título centralizado em negrito
  ## 1. DOS FATOS -> título de seção (negrito, caixa alta)
  ### 1.1 Texto   -> subtítulo (negrito)
  > texto         -> citação longa (recuo 4 cm, corpo 10, espaço simples)
  - item          -> item de lista
  ^ texto         -> linha centralizada (fecho, local e data, assinatura)
  ---pagebreak--- -> quebra de página
  **negrito**  *itálico*  [[PENDENTE: ...]] (realce amarelo)
  Tabelas Markdown (| a | b |) -> tabela
"""
import argparse, re, subprocess, tempfile, shutil
from pathlib import Path

INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|\[\[[^\]]+\]\])")


def blocos(texto):
    out, para, tab = [], [], []
    def fecha():
        if para:
            out.append(("p", " ".join(s.strip() for s in para))); para.clear()
        if tab:
            out.append(("table", list(tab))); tab.clear()
    for raw in texto.splitlines():
        s = raw.strip()
        if not s:
            fecha(); continue
        if s.startswith("|"):
            if para: out.append(("p", " ".join(para))); para.clear()
            if not re.fullmatch(r"\|?[\s:\-|]+\|?", s):
                tab.append([c.strip() for c in s.strip("|").split("|")])
            continue
        if tab: fecha()
        if s == "---pagebreak---": fecha(); out.append(("pb", "")); continue
        m = re.match(r"(#{1,3})\s+(.*)", s)
        if m: fecha(); out.append(("h%d" % len(m.group(1)), m.group(2))); continue
        if s.startswith(">"): fecha(); out.append(("quote", s.lstrip("> ").strip())); continue
        if re.match(r"[-•]\s+", s): fecha(); out.append(("li", re.sub(r"^[-•]\s+", "", s))); continue
        if s.startswith("^"): fecha(); out.append(("center", s[1:].strip())); continue
        para.append(s)
    fecha()
    res = []
    for t, c in out:
        if t == "quote" and res and res[-1][0] == "quote":
            res[-1] = ("quote", res[-1][1] + " " + c)
        else:
            res.append((t, c))
    return res


def abrir_modelo(modelo, paisagem=False):
    from docx import Document
    from docx.shared import Cm
    from docx.enum.section import WD_ORIENT
    if modelo and Path(modelo).exists():
        doc = Document(str(modelo))
        body = doc.element.body
        for el in list(body):
            if not el.tag.endswith("}sectPr"):
                body.remove(el)
    else:
        doc = Document()
        sec = doc.sections[0]
        sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
        sec.top_margin, sec.bottom_margin = Cm(3.0), Cm(2.0)
        sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.0)
        st = doc.styles["Normal"]; st.font.name = "Arial"
        from docx.shared import Pt
        st.font.size = Pt(12)
    if paisagem:
        for sec in doc.sections:
            if sec.orientation != WD_ORIENT.LANDSCAPE:
                sec.orientation = WD_ORIENT.LANDSCAPE
                sec.page_width, sec.page_height = sec.page_height, sec.page_width
    return doc


def escrever(doc, md, corpo_tabela=9.5):
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    def runs(par, texto, size=None, bold=None):
        for parte in INLINE.split(texto):
            if not parte: continue
            if parte.startswith("**"):
                r = par.add_run(parte[2:-2]); r.bold = True
            elif parte.startswith("[["):
                r = par.add_run(parte); r.font.highlight_color = WD_COLOR_INDEX.YELLOW; r.bold = True
            elif parte.startswith("*"):
                r = par.add_run(parte[1:-1]); r.italic = True
            else:
                r = par.add_run(parte)
            if size: r.font.size = Pt(size)
            if bold: r.bold = True

    for tipo, c in blocos(md):
        if tipo == "pb":
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE); continue
        if tipo == "table":
            ncol = max(len(l) for l in c)
            t = doc.add_table(rows=0, cols=ncol); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, linha in enumerate(c):
                cells = t.add_row().cells
                for j in range(ncol):
                    p = cells[j].paragraphs[0]; p.paragraph_format.line_spacing = 1.0
                    p.paragraph_format.first_line_indent = Cm(0)
                    runs(p, linha[j] if j < len(linha) else "", size=corpo_tabela, bold=(i == 0))
                    if i == 0:
                        tcPr = cells[j]._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
                        sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), "EEEEEE"); tcPr.append(sh)
            doc.add_paragraph(); continue
        p = doc.add_paragraph(); f = p.paragraph_format
        f.line_spacing = 1.5; f.space_after = Pt(6)
        if tipo == "h1":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER; f.space_after = Pt(18); runs(p, c, bold=True)
        elif tipo == "h2":
            f.space_before = Pt(12); f.keep_with_next = True; runs(p, c.upper(), bold=True)
        elif tipo == "h3":
            f.space_before = Pt(6); f.keep_with_next = True; runs(p, c, bold=True)
        elif tipo == "quote":
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; f.left_indent = Cm(4); f.line_spacing = 1.0
            f.space_before = Pt(6); f.space_after = Pt(12); runs(p, c, size=10)
        elif tipo == "li":
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; f.left_indent = Cm(1.25); f.first_line_indent = Cm(-0.5)
            runs(p, "– " + c)
        elif tipo == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER; runs(p, c)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; f.first_line_indent = Cm(2.0); runs(p, c)


def gerar_docx(md, saida, modelo):
    doc = abrir_modelo(modelo)
    escrever(doc, md)
    doc.save(saida)


def gerar_pdf(md, saida, modelo, titulo, paisagem=False):
    tarja = f"**{titulo.upper()} · USO INTERNO DO ADVOGADO · NÃO PROTOCOLAR**\n\n"
    doc = abrir_modelo(modelo, paisagem)
    escrever(doc, tarja + md, corpo_tabela=8)
    tmp = Path(tempfile.mkdtemp())
    docx = tmp / (Path(saida).stem + ".docx")
    doc.save(docx)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise SystemExit("LibreOffice (soffice) não encontrado: o DOCX foi gerado em %s" % docx)
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(docx)],
                   check=True, capture_output=True)
    shutil.move(str(tmp / (docx.stem + ".pdf")), saida)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["peca", "pdf"])
    ap.add_argument("entrada"); ap.add_argument("saida")
    ap.add_argument("--modelo", default="", help="DOCX com o papel timbrado do titular")
    ap.add_argument("--titulo", default="RELATÓRIO RESERVADO")
    ap.add_argument("--paisagem", action="store_true")
    a = ap.parse_args()
    texto = Path(a.entrada).read_text(encoding="utf-8")
    if a.modo == "peca":
        gerar_docx(texto, a.saida, a.modelo)
    else:
        gerar_pdf(texto, a.saida, a.modelo, a.titulo, a.paisagem)
    print("ok:", a.saida)
