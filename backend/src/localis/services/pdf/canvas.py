from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas as pdfcanvas

from localis.services.pdf.styles import Palette

W, H = A4


class ReportCanvas(pdfcanvas.Canvas):
    def __init__(
        self,
        *args,
        company: str = "",
        date_str: str = "",
        provider: str = "",
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.company = company
        self.date_str = date_str
        self.provider = provider
        self._saved: list[dict] = []

    def showPage(self) -> None:
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved)
        for i, state in enumerate(self._saved):
            self.__dict__.update(state)
            self._draw_header()
            self._draw_footer(i + 1, total)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_header(self) -> None:
        y = H - 18 * mm
        self._draw_mascot(x=15 * mm, y=y, size=9 * mm)

        self.setFont("Helvetica-Bold", 11)
        self.setFillColor(Palette.FG)
        self.drawString(27 * mm, y + 1 * mm, "Localis")
        self.setFont("Helvetica", 8.5)
        self.setFillColor(Palette.MUTED)
        self.drawString(45 * mm, y + 1 * mm, "AI")

        if self.provider:
            self._draw_pill(
                x=W - 2 * cm,
                y=y + 0.3 * mm,
                label=self.provider.upper(),
                fill=Palette.PRIMARY_SOFT,
                stroke=Palette.PRIMARY,
                text_color=Palette.PRIMARY,
                align_right=True,
            )

        self.setStrokeColor(Palette.BORDER)
        self.setLineWidth(0.25)
        self.line(15 * mm, y - 3 * mm, W - 15 * mm, y - 3 * mm)

    def _draw_mascot(self, x: float, y: float, size: float) -> None:
        cx, cy, r = x + size / 2, y + size / 2, size / 2

        self.setFillColor(Palette.PRIMARY_DEEP)
        self.circle(cx, cy, r, fill=1, stroke=0)
        self.setFillColor(Palette.PRIMARY)
        self.circle(cx - r * 0.1, cy + r * 0.1, r * 0.85, fill=1, stroke=0)

        eye_r = r * 0.18
        eye_y = cy + r * 0.12
        self.setFillColor(Palette.WHITE)
        self.circle(cx - r * 0.32, eye_y, eye_r, fill=1, stroke=0)
        self.circle(cx + r * 0.32, eye_y, eye_r, fill=1, stroke=0)

        pup_r = r * 0.08
        self.setFillColor(Palette.BG)
        self.circle(cx - r * 0.32, eye_y, pup_r, fill=1, stroke=0)
        self.circle(cx + r * 0.32, eye_y, pup_r, fill=1, stroke=0)

        self.setStrokeColor(Palette.WHITE)
        self.setLineWidth(1.3)
        self.setLineCap(1)
        self.arc(
            cx - r * 0.42,
            cy - r * 0.55,
            cx + r * 0.42,
            cy - r * 0.05,
            startAng=200,
            extent=140,
        )

    def _draw_pill(
        self,
        x: float,
        y: float,
        label: str,
        fill,
        stroke,
        text_color,
        align_right: bool = False,
    ) -> None:
        padding = 3 * mm
        self.setFont("Helvetica-Bold", 7.5)
        width = self.stringWidth(label, "Helvetica-Bold", 7.5) + padding * 2
        height = 5 * mm
        x0 = x - width if align_right else x
        self.setFillColor(fill)
        self.setStrokeColor(stroke)
        self.setLineWidth(0.4)
        self.roundRect(x0, y, width, height, radius=2.2 * mm, fill=1, stroke=1)
        self.setFillColor(text_color)
        self.drawString(x0 + padding, y + 1.6 * mm, label)

    def _draw_footer(self, pg: int, total: int) -> None:
        self.setFillColor(Palette.CARD)
        self.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
        self.setStrokeColor(Palette.BORDER)
        self.setLineWidth(0.25)
        self.line(0, 10 * mm, W, 10 * mm)

        self.setFont("Helvetica", 7)
        self.setFillColor(Palette.MUTED)
        self.drawString(15 * mm, 3.8 * mm, f"Localis AI · {self.company}")
        self.drawCentredString(W / 2, 3.8 * mm, "Généré par IA · vérifiez avant décision")
        self.drawRightString(W - 15 * mm, 3.8 * mm, f"{pg} / {total}")
