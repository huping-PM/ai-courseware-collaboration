"""Local text extraction. Scanned documents require a separate OCR tool."""
import argparse
from pathlib import Path
import sys


def extract(path):
    suffix = path.suffix.lower()
    if suffix in ['.txt', '.md']: return path.read_text(encoding='utf-8-sig'), []
    if suffix == '.docx':
        from docx import Document
        from docx.oxml.ns import qn
        from docx.text.paragraph import Paragraph
        from docx.table import Table
        doc = Document(path); lines = []
        for child in doc.element.body:
            if child.tag == qn('w:p'): lines.append(Paragraph(child, doc).text)
            elif child.tag == qn('w:tbl'):
                for row in Table(child, doc).rows: lines.append(' | '.join(cell.text for cell in row.cells))
        return '\n\n'.join(lines), ['Images, equations, textboxes, headers and revision semantics require manual verification.']
    if suffix == '.pdf':
        import pdfplumber
        parts = []; warnings = []
        with pdfplumber.open(path) as pdf:
            for n, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ''
                if not text.strip(): warnings.append(f'Page {n}: no text extracted; OCR/manual inspection required.')
                parts.append(f'## Page {n}\n\n{text}')
        if len(warnings) == len(parts): raise ValueError('No PDF text found; use OCR, do not invent content')
        return '\n\n'.join(parts), warnings + ['Reading order and tables need comparison with the source.']
    raise ValueError('Supported input: UTF-8 .txt/.md, .docx, text-based .pdf')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', required=True); ap.add_argument('--output', required=True)
    a = ap.parse_args(); source = Path(a.input).resolve(); out = Path(a.output).resolve()
    if out.exists(): raise ValueError('Refusing to overwrite output')
    text, warnings = extract(source)
    if not text.strip(): raise ValueError('Empty source; no content generated')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f'<!-- Source: {source.name}; extraction only, not approved -->\n\n' + text, encoding='utf-8')
    for warning in warnings: print('REVIEW:', warning)
    print(str(out))

if __name__ == '__main__': main()
