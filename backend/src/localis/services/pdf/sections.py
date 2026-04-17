from __future__ import annotations

from collections.abc import Iterable

from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from localis.domain.schemas import (
    ActionPlan,
    AnalysisReport,
    Diagnostic,
    DiagnosticItem,
    KPI,
    Risk,
    ShortTermAction,
)
from localis.services.pdf.styles import Palette, safe


def _hex(color) -> str:
    return color.hexval().replace("0x", "#")


def _accent_bar(color=Palette.PRIMARY, thickness: float = 1.2) -> HRFlowable:
    return HRFlowable(width="15%", thickness=thickness, color=color, lineCap="round", hAlign="LEFT")


def build_cover(report: AnalysisReport, styles: dict) -> list[Flowable]:
    company = report.entreprise
    items: list[Flowable] = [
        Spacer(1, 4 * mm),
        Paragraph("RAPPORT DE DIAGNOSTIC STRATÉGIQUE", styles["pill"]),
        Spacer(1, 2 * mm),
        Paragraph(safe(company.nom), styles["h1"]),
    ]
    if company.categorie:
        items.append(Paragraph(safe(company.categorie), styles["dim"]))
    items.append(Spacer(1, 6 * mm))

    rows = [
        ("Adresse", company.adresse or "—"),
        ("Téléphone", company.telephone or "—"),
        ("Site web", company.site_web or "—"),
        ("Note moyenne", f"{company.note_moyenne:.1f} / 5" if company.note_moyenne is not None else "—"),
        ("Nombre d'avis", str(company.nombre_avis) if company.nombre_avis is not None else "—"),
    ]
    data = [
        [Paragraph(f"<b>{safe(label)}</b>", styles["item_title"]), Paragraph(safe(value), styles["item_body"])]
        for label, value in rows
    ]
    table = Table(data, colWidths=[40 * mm, None])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), Palette.CARD),
                ("BOX", (0, 0), (-1, -1), 0.4, Palette.BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, Palette.BORDER),
            ]
        )
    )
    items.append(table)
    items.append(Spacer(1, 6 * mm))
    return items


def build_swot(diagnostic: Diagnostic, styles: dict) -> list[Flowable]:
    forces = _swot_quadrant("Forces", diagnostic.points_forts, Palette.GREEN, Palette.GREEN_SOFT, styles)
    faibl = _swot_quadrant("Faiblesses", diagnostic.points_faibles, Palette.RED, Palette.RED_SOFT, styles)
    oppor = _swot_quadrant("Opportunités", diagnostic.opportunites, Palette.BLUE, Palette.BLUE_SOFT, styles)
    menac = _swot_quadrant("Menaces", diagnostic.menaces, Palette.AMBER, Palette.AMBER_SOFT, styles)

    grid = Table([[forces, faibl], [oppor, menac]], colWidths=[None, None])
    grid.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return [
        Paragraph("Analyse SWOT", styles["h2"]),
        _accent_bar(),
        Spacer(1, 3 * mm),
        KeepTogether(grid),
        Spacer(1, 6 * mm),
    ]


def _swot_quadrant(
    title: str,
    entries: Iterable[DiagnosticItem],
    header_color,
    header_soft,
    styles: dict,
) -> Table:
    header_row = Paragraph(
        f'<font color="{_hex(header_color)}"><b>{safe(title.upper())}</b></font>',
        styles["quad_title"],
    )
    body: list[list] = [[header_row]]

    entries_list = list(entries)
    if not entries_list:
        body.append([Paragraph("<i>Aucun élément</i>", styles["muted"])])
    else:
        for entry in entries_list:
            body.append([Paragraph(f"<b>{safe(entry.titre)}</b>", styles["item_title"])])
            body.append([Paragraph(safe(entry.description), styles["item_body"])])

    quadrant = Table(body, colWidths=[None])
    quadrant.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), Palette.CARD),
                ("BACKGROUND", (0, 0), (-1, 0), header_soft),
                ("LINEABOVE", (0, 0), (-1, 0), 1.5, header_color),
                ("BOX", (0, 0), (-1, -1), 0.4, Palette.BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 1), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, 0), 0.3, Palette.BORDER),
            ]
        )
    )
    return quadrant


def build_action_plan(plan: ActionPlan, styles: dict) -> list[Flowable]:
    items: list[Flowable] = [
        Paragraph("Plan d'action", styles["h2"]),
        _accent_bar(),
        Spacer(1, 3 * mm),
    ]

    if plan.resume_executif:
        items.append(_callout(plan.resume_executif, styles))
        items.append(Spacer(1, 4 * mm))

    items.extend(_horizon_block("COURT TERME", "0 – 3 mois", plan.court_terme, Palette.RED, styles))
    items.extend(_horizon_block("MOYEN TERME", "3 – 6 mois", plan.moyen_terme, Palette.AMBER, styles))
    items.extend(_horizon_block("LONG TERME", "6 – 12 mois", plan.long_terme, Palette.GREEN, styles))

    if plan.kpis:
        items.append(Spacer(1, 4 * mm))
        items.append(Paragraph("Indicateurs à suivre", styles["h3"]))
        items.append(_kpi_table(plan.kpis, styles))

    if plan.risques:
        items.append(Spacer(1, 4 * mm))
        items.append(Paragraph("Risques identifiés", styles["h3"]))
        for risk in plan.risques:
            items.append(_risk_card(risk, styles))

    return items


def _callout(text: str, styles: dict) -> Flowable:
    body = Paragraph(f"<b>Résumé exécutif</b><br/>{safe(text, 700)}", styles["item_body"])
    callout = Table([[body]], colWidths=[None])
    callout.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), Palette.PRIMARY_SOFT),
                ("LINEBEFORE", (0, 0), (0, -1), 2, Palette.PRIMARY),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return callout


def _horizon_block(
    title: str,
    subtitle: str,
    actions: list[ShortTermAction],
    dot_color,
    styles: dict,
) -> list[Flowable]:
    header_text = (
        f'<font color="{_hex(dot_color)}">●</font> '
        f'<b>{safe(title)}</b>  '
        f'<font color="{_hex(Palette.MUTED)}">— {safe(subtitle)}</font>'
    )
    header = Table([[Paragraph(header_text, styles["item_title"])]], colWidths=[None])
    header.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    out: list[Flowable] = [header]
    if not actions:
        out.append(Paragraph("<i>Aucune action</i>", styles["muted"]))
        return out

    for action in actions:
        first_line = f"<b>{safe(action.action)}</b>  {_priority_label(action.priorite)}{_delay_label(action)}"
        card = Table(
            [
                [Paragraph(first_line, styles["item_title"])],
                [Paragraph(safe(action.description, 400), styles["item_body"])],
            ],
            colWidths=[None],
        )
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), Palette.CARD),
                    ("BOX", (0, 0), (-1, -1), 0.3, Palette.BORDER),
                    ("LINEBEFORE", (0, 0), (0, -1), 2, dot_color),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        out.append(card)
        out.append(Spacer(1, 2 * mm))

    return out


_PRIORITY_COLORS = {
    "P0": Palette.RED,
    "P1": Palette.AMBER,
    "P2": Palette.BLUE,
    "P3": Palette.MUTED,
}


def _priority_label(priorite: str | None) -> str:
    if not priorite:
        return ""
    color = _hex(_PRIORITY_COLORS.get(priorite, Palette.MUTED))
    return f' <font color="{color}" size="7.5">[ {safe(priorite)} ]</font>'


def _delay_label(action: ShortTermAction) -> str:
    muted = _hex(Palette.MUTED)
    if action.delai_jours:
        return f' <font color="{muted}" size="8">· {action.delai_jours} j</font>'
    if action.delai_mois:
        return f' <font color="{muted}" size="8">· {action.delai_mois} mois</font>'
    return ""


def _kpi_table(kpis: list[KPI], styles: dict) -> Table:
    rows = [["Métrique", "Baseline", "Cible", "Fréquence"]]
    for kpi in kpis:
        rows.append(
            [
                Paragraph(f"<b>{safe(kpi.metrique)}</b>", styles["item_title"]),
                Paragraph(safe(str(kpi.baseline or "—")), styles["item_body"]),
                Paragraph(safe(str(kpi.cible or "—")), styles["item_body"]),
                Paragraph(safe(kpi.frequence_mesure or "—"), styles["item_body"]),
            ]
        )
    table = Table(rows, hAlign="LEFT", colWidths=[None, 30 * mm, 30 * mm, 30 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), Palette.PRIMARY_SOFT),
                ("TEXTCOLOR", (0, 0), (-1, 0), Palette.PRIMARY),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, Palette.PRIMARY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [Palette.CARD, Palette.CARD_ALT]),
                ("BOX", (0, 0), (-1, -1), 0.3, Palette.BORDER),
                ("LINEBELOW", (0, 1), (-1, -2), 0.25, Palette.BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


_RISK_COLORS = {
    "élevé": Palette.RED,
    "très élevé": Palette.RED,
    "modéré": Palette.AMBER,
    "faible": Palette.GREEN,
    "très faible": Palette.GREEN,
}


def _risk_card(risk: Risk, styles: dict) -> Flowable:
    prob_color = _RISK_COLORS.get(str(risk.probabilite or "").lower(), Palette.MUTED)
    header_text = (
        f"<b>{safe(risk.risque)}</b>  "
        f'<font color="{_hex(prob_color)}" size="7.5">probabilité : {safe(risk.probabilite or "—")}</font>  '
        f'<font color="{_hex(Palette.MUTED)}" size="7.5">impact : {safe(str(risk.impact) if risk.impact else "—")}</font>'
    )
    body_text = (
        f'<font color="{_hex(Palette.FG_DIM)}">Mitigation : </font>'
        f"{safe(risk.mitigation or '—')}"
    )
    card = Table(
        [
            [Paragraph(header_text, styles["item_title"])],
            [Paragraph(body_text, styles["item_body"])],
        ],
        colWidths=[None],
    )
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), Palette.CARD),
                ("BOX", (0, 0), (-1, -1), 0.3, Palette.BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 2, prob_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return KeepTogether([card, Spacer(1, 2 * mm)])


def build_footer_metadata(report: AnalysisReport, styles: dict) -> list[Flowable]:
    meta = report.metadonnees
    footer = (
        f'<font color="{_hex(Palette.MUTED)}">'
        f"Généré par {safe(meta.provider or '?')} / {safe(meta.modele or '?')} · "
        f"ID {safe(meta.id_analyse)} · {meta.temps_reponse_ms or 0} ms · "
        f"{meta.date_analyse.strftime('%d/%m/%Y à %H:%M')}</font>"
    )
    return [
        Spacer(1, 6 * mm),
        _accent_bar(color=Palette.BORDER, thickness=0.3),
        Paragraph(footer, styles["muted"]),
    ]
