from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle


class Palette:
    BG = HexColor("#0B0A14")
    CARD = HexColor("#141321")
    CARD_ALT = HexColor("#1C1A2E")
    BORDER = HexColor("#2A263D")

    FG = HexColor("#F4F2FA")
    FG_DIM = HexColor("#C7C2D8")
    MUTED = HexColor("#8A85A0")

    PRIMARY = HexColor("#A78BFA")
    PRIMARY_DEEP = HexColor("#7C3AED")
    PRIMARY_SOFT = HexColor("#2A1F52")

    GREEN = HexColor("#34D399")
    GREEN_SOFT = HexColor("#0F3D2E")
    RED = HexColor("#F87171")
    RED_SOFT = HexColor("#3E1A1A")
    BLUE = HexColor("#60A5FA")
    BLUE_SOFT = HexColor("#1A2A47")
    AMBER = HexColor("#FBBF24")
    AMBER_SOFT = HexColor("#3A2A0A")

    WHITE = HexColor("#FFFFFF")


def make_styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle(
        "base",
        fontName="Helvetica",
        fontSize=10,
        textColor=Palette.FG,
        leading=14,
    )
    return {
        "body": ParagraphStyle("body", parent=base),
        "dim": ParagraphStyle("dim", parent=base, textColor=Palette.FG_DIM, fontSize=9, leading=13),
        "muted": ParagraphStyle("muted", parent=base, textColor=Palette.MUTED, fontSize=8, leading=11),
        "h1": ParagraphStyle(
            "h1",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=Palette.FG,
            spaceAfter=6,
            leading=32,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=15,
            textColor=Palette.FG,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=Palette.PRIMARY,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "quad_title": ParagraphStyle(
            "quad_title",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=Palette.WHITE,
        ),
        "item_title": ParagraphStyle(
            "item_title",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=9.5,
            textColor=Palette.FG,
            leading=12,
        ),
        "item_body": ParagraphStyle(
            "item_body",
            parent=base,
            fontSize=8.5,
            textColor=Palette.FG_DIM,
            alignment=TA_JUSTIFY,
            leading=11.5,
        ),
        "centered": ParagraphStyle("centered", parent=base, alignment=TA_CENTER),
        "left": ParagraphStyle("left", parent=base, alignment=TA_LEFT),
        "pill": ParagraphStyle(
            "pill",
            parent=base,
            fontName="Helvetica-Bold",
            fontSize=7.5,
            textColor=Palette.PRIMARY,
        ),
    }


def safe(text: str | None, max_len: int = 600) -> str:
    if not text:
        return ""
    result = str(text)[:max_len]
    return result.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
