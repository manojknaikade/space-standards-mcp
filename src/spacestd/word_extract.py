"""Word (.docx/.doc) path for ECSS documents that have no PDF yet (e.g. ECSS-E-ST-32-08C).

Clause numbers and requirement letters are Word auto-numbering, so python-docx
cannot see them. Pipeline (docs/PARSING_NOTES.md):

1. accept all tracked changes in the XML (drop w:del / w:moveFrom, unwrap
   w:ins / w:moveTo, drop *Change property records, merge paragraphs whose
   paragraph mark was deleted);
2. let LibreOffice render the numbering into plain text (.doc is converted first);
3. the ECSS parser recomputes letters per clause (Word runs them on: r., aa., ...).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
DROP = ("del", "moveFrom", "moveFromRangeStart", "moveFromRangeEnd", "moveToRangeStart", "moveToRangeEnd")
UNWRAP = ("ins", "moveTo")
PARTS = ("word/document.xml", "word/footnotes.xml", "word/endnotes.xml")


def accept_changes_xml(xml: bytes) -> bytes:
    root = etree.fromstring(xml)
    # paragraphs whose paragraph mark was deleted are merged with the next paragraph
    for p in list(root.iter(f"{{{W}}}p")):
        mark = p.find("w:pPr/w:rPr/w:del", NS)
        if mark is None:
            continue
        nxt = p.getnext()
        if nxt is not None and nxt.tag == f"{{{W}}}p":
            for child in list(p):
                if child.tag != f"{{{W}}}pPr":
                    nxt.insert(1 if nxt.find("w:pPr", NS) is not None else 0, child)
            p.getparent().remove(p)
        else:
            mark.getparent().remove(mark)
    for el in list(root.iter()):
        if not isinstance(el.tag, str):
            continue
        local = etree.QName(el).localname
        parent = el.getparent()
        if parent is None:
            continue
        if local in DROP or (local.endswith("Change") and el.tag.startswith(f"{{{W}}}")):
            parent.remove(el)
    for local in UNWRAP:
        for el in list(root.iter(f"{{{W}}}{local}")):
            parent = el.getparent()
            if parent is None:
                continue
            idx = parent.index(el)
            for child in list(el):
                parent.insert(idx, child)
                idx += 1
            parent.remove(el)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def accept_changes(src: Path, dst: Path) -> None:
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in PARTS:
                data = accept_changes_xml(data)
            zout.writestr(item, data)


def _soffice() -> str:
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        raise RuntimeError("LibreOffice (soffice) is needed to read ECSS Word files; install it or use the PDF")
    return exe


def _convert(src: Path, fmt: str, outdir: Path) -> Path:
    subprocess.run(
        [_soffice(), "--headless", f"-env:UserInstallation=file://{outdir}/lo-profile", "--convert-to", fmt,
         "--outdir", str(outdir), str(src)],
        check=True, capture_output=True, timeout=300,
    )
    ext = fmt.split(":")[0]
    return outdir / f"{src.stem}.{ext}"


def word_to_text_lines(path: Path) -> list[str]:
    """Return the rendered paragraphs (numbering included) of a .docx/.doc with changes accepted."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        src = path
        if path.suffix.lower() == ".doc":
            src = _convert(path, "docx", tmpdir)
        accepted = tmpdir / f"{path.stem}.accepted.docx"
        accept_changes(src, accepted)
        txt = _convert(accepted, "txt:Text (encoded):UTF8", tmpdir)
        return txt.read_text(encoding="utf-8-sig").splitlines()
