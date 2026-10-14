"""Write small PDFs for table-layout tests: text at positions, ruling lines, boxes (no dependencies).

Coordinates are pdfplumber's: x from the left, `top` from the top of the page, in points. Text uses the
standard Helvetica fonts (no embedding), so only Latin-1 characters can be drawn.

    page = Page()
    page.grid([72, 200, 300], [100, 120, 140])        # every rule of a 2 x 2 grid
    page.text(76, 104, "Load", bold=True)
    page.text(204, 124, "1,25")
    write_pdf(tmp_path / "t.pdf", [page])
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ASCENT = 0.718  # Helvetica cap height / size: pdfplumber's `top` = height - baseline - ASCENT * size


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


@dataclass
class Page:
    width: float = 612
    height: float = 792
    ops: list[str] = field(default_factory=list)

    def text(self, x: float, top: float, s: str, size: float = 10, bold: bool = False, rotate: int = 0) -> None:
        """Text whose glyph tops sit at `top`. rotate=90: reads bottom to top, starting at (x, top) and
        running up the page (pdfplumber then reports x0 = x - ASCENT * size, bottom = top)."""
        font = "F2" if bold else "F1"
        if rotate == 90:
            y = self.height - top
            tm = f"0 1 -1 0 {x:.2f} {y:.2f} Tm"
        elif rotate == -90:
            y = self.height - top
            tm = f"0 -1 1 0 {x:.2f} {y:.2f} Tm"
        else:
            tm = f"1 0 0 1 {x:.2f} {self.height - top - ASCENT * size:.2f} Tm"
        self.ops.append(f"BT /{font} {size:g} Tf {tm} ({_esc(s)}) Tj ET")

    def hline(self, top: float, x0: float, x1: float, width: float = 0.5) -> None:
        y = self.height - top
        self.ops.append(f"{width:g} w {x0:.2f} {y:.2f} m {x1:.2f} {y:.2f} l S")

    def vline(self, x: float, top: float, bottom: float, width: float = 0.5) -> None:
        self.ops.append(f"{width:g} w {x:.2f} {self.height - top:.2f} m {x:.2f} {self.height - bottom:.2f} l S")

    def bar(self, x0: float, top: float, x1: float, bottom: float) -> None:
        """A thin filled rectangle (how some PDFs draw rules)."""
        self.ops.append(f"{x0:.2f} {self.height - bottom:.2f} {x1 - x0:.2f} {bottom - top:.2f} re f")

    def fill(self, x0: float, top: float, x1: float, bottom: float, gray: float = 0.8) -> None:
        """A filled grey rectangle (shaded cell, legend swatch); the fill colour is reset to black after."""
        self.ops.append(f"{gray:g} g {x0:.2f} {self.height - bottom:.2f} {x1 - x0:.2f} {bottom - top:.2f} re f 0 g")

    def grid(self, xs: list[float], ys: list[float]) -> None:
        """All horizontal and vertical rules of a regular grid (no merged cells)."""
        for y in ys:
            self.hline(y, xs[0], xs[-1])
        for x in xs:
            self.vline(x, ys[0], ys[-1])

    def box(self, x0: float, top: float, x1: float, bottom: float) -> None:
        self.hline(top, x0, x1)
        self.hline(bottom, x0, x1)
        self.vline(x0, top, bottom)
        self.vline(x1, top, bottom)


def write_pdf(path: Path, pages: list[Page]) -> Path:
    objs: list[bytes] = []

    def add(body: str | bytes) -> int:
        objs.append(body.encode("latin-1") if isinstance(body, str) else body)
        return len(objs)

    add("<< /Type /Catalog /Pages 2 0 R >>")
    add("")  # pages, filled below
    f1 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    f2 = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    kids = []
    for p in pages:
        stream = "\n".join(p.ops).encode("latin-1")
        content = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        kids.append(add(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {p.width:g} {p.height:g}] "
                        f"/Resources << /Font << /F1 {f1} 0 R /F2 {f2} 0 R >> >> /Contents {content} 0 R >>"))
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {len(kids)} >>".encode()

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    Path(path).write_bytes(bytes(out))
    return Path(path)
