#!/usr/bin/env python3
"""Build the four-page English technical report as a publication-ready PDF."""

from pathlib import Path
from textwrap import wrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Image, Paragraph, Table, TableStyle
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "smart-helmet-aiot-technical-report.pdf"
ARCH = ROOT / "docs" / "architecture.png"
VISION = ROOT / "experiments" / "plots" / "vision" / "frame-sampling-comparison.png"
DELIVERY = ROOT / "experiments" / "plots" / "network" / "delivery_rate_vs_packet_loss.png"
RECONNECT = ROOT / "experiments" / "plots" / "network" / "reconnect_time_vs_outage.png"

PAGE_W, PAGE_H = A4
MARGIN = 17 * mm
TEXT_W = PAGE_W - 2 * MARGIN
INK = colors.HexColor("#1f2328")
MUTED = colors.HexColor("#59636e")
ACCENT = colors.HexColor("#0969da")
BORDER = colors.HexColor("#d0d7de")
PAPER = colors.HexColor("#ffffff")
SOFT = colors.HexColor("#f6f8fa")


def register_fonts():
    regular = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("ReportSans", str(regular)))
        pdfmetrics.registerFont(TTFont("ReportSansBold", str(bold)))
        return "ReportSans", "ReportSansBold"
    return "Helvetica", "Helvetica-Bold"


FONT, BOLD = register_fonts()


def para_style(size=9.2, leading=12.2, color=INK, bold=False, space_after=4):
    return ParagraphStyle(
        name=f"p-{size}-{bold}-{color}",
        fontName=BOLD if bold else FONT,
        fontSize=size,
        leading=leading,
        textColor=color,
        alignment=TA_LEFT,
        spaceAfter=space_after,
    )


BODY = para_style()
SMALL = para_style(7.5, 9.4, MUTED)
CAPTION = para_style(7.2, 9, MUTED)


def header(canvas: Canvas, page_no: int, section: str):
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 7.5)
    canvas.drawString(MARGIN, PAGE_H - 11 * mm, "SMART HELMET AIOT")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 11 * mm, section.upper())
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.55)
    canvas.line(MARGIN, PAGE_H - 14 * mm, PAGE_W - MARGIN, PAGE_H - 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W - MARGIN, 9 * mm, str(page_no))


def title(canvas: Canvas, text: str, y: float, size=19):
    canvas.setFillColor(INK)
    canvas.setFont(BOLD, size)
    canvas.drawString(MARGIN, y, text)
    return y - (size + 8)


def section_title(canvas: Canvas, text: str, y: float, size=12, x=MARGIN):
    canvas.setFillColor(ACCENT)
    canvas.setFont(BOLD, size)
    canvas.drawString(x, y, text)
    return y - 5 * mm


def draw_para(canvas: Canvas, text: str, x: float, y: float, width: float, style=BODY):
    p = Paragraph(text, style)
    _, h = p.wrap(width, PAGE_H)
    p.drawOn(canvas, x, y - h)
    return y - h - style.spaceAfter


def draw_bullets(canvas: Canvas, items, x: float, y: float, width: float, style=BODY):
    for item in items:
        y = draw_para(canvas, f"<font color='#0969da'>•</font> {item}", x, y, width, style)
    return y


def draw_image(canvas: Canvas, path: Path, x: float, y_top: float, width: float, height: float):
    if not path.exists():
        raise FileNotFoundError(path)
    img = Image(str(path), width=width, height=height, kind="proportional")
    iw, ih = img.wrap(width, height)
    img.drawOn(canvas, x + (width - iw) / 2, y_top - ih)
    return y_top - ih


def draw_table(canvas: Canvas, data, x: float, y_top: float, col_widths, font_size=7.4, row_height=None):
    table = Table(data, colWidths=col_widths, rowHeights=row_height)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SOFT),
                ("TEXTCOLOR", (0, 0), (-1, 0), INK),
                ("FONTNAME", (0, 0), (-1, 0), BOLD),
                ("FONTNAME", (0, 1), (-1, -1), FONT),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("LEADING", (0, 0), (-1, -1), font_size + 2),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PAPER, colors.HexColor("#fbfcfd")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    tw, th = table.wrap(sum(col_widths), PAGE_H)
    table.drawOn(canvas, x, y_top - th)
    return y_top - th


def page_one(canvas: Canvas):
    header(canvas, 1, "Overview")
    y = PAGE_H - 28 * mm
    canvas.setFillColor(ACCENT)
    canvas.setFont(BOLD, 8)
    canvas.drawString(MARGIN, y, "TECHNICAL REPORT  |  VERSION 1.0.0  |  SEPTEMBER 2026")
    y -= 10 * mm
    canvas.setFillColor(INK)
    canvas.setFont(BOLD, 25)
    canvas.drawString(MARGIN, y, "Smart Helmet AIoT")
    y -= 10 * mm
    canvas.setFont(FONT, 15)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, y, "A Reproducible Edge-to-Cloud Safety Monitoring System")
    y -= 12 * mm
    y = section_title(canvas, "Abstract", y)
    abstract = (
        "This report presents a reproducible research prototype for studying an edge-to-cloud monitoring pipeline derived from a physical smart-helmet project. "
        "The system combines MQTT telemetry, Spring Boot and MySQL persistence, a Vue dashboard, fixed-video person detection, and repeatable network experiments. "
        "Its scope is deliberately limited to latency, throughput, sampled-frame detection continuity, and delivery reliability. "
        "On a 20-second reference video, frame stride 5 reached 34.56 pipeline FPS with 99.17% sampled-frame continuity. "
        "Across nine broker-outage trials, every client recovered after broker availability."
    )
    y = draw_para(canvas, abstract, MARGIN, y, TEXT_W)
    y -= 2 * mm
    y = section_title(canvas, "Research question", y)
    question = (
        "<b>How do frame-sampling frequency and network conditions affect the latency, throughput, reliability, "
        "and detection continuity of a resource-constrained edge-to-cloud monitoring pipeline?</b>"
    )
    y = draw_para(canvas, question, MARGIN, y, TEXT_W, para_style(10.2, 13.3, INK))
    y -= 3 * mm
    arch_h = 78 * mm
    y = draw_image(canvas, ARCH, MARGIN, y, TEXT_W, arch_h)
    draw_para(
        canvas,
        "Figure 1. Public reproducibility architecture. Telemetry and fixed-video results converge in the backend and dashboard.",
        MARGIN,
        y - 2 * mm,
        TEXT_W,
        CAPTION,
    )


def page_two(canvas: Canvas):
    header(canvas, 2, "System design and implementation")
    y = PAGE_H - 25 * mm
    y = title(canvas, "System design and implementation", y)
    col_gap = 9 * mm
    col_w = (TEXT_W - col_gap) / 2
    left_x = MARGIN
    right_x = MARGIN + col_w + col_gap
    left_y = y
    right_y = y
    left_y = section_title(canvas, "Telemetry loop", left_y)
    left_y = draw_para(
        canvas,
        "A simulator or the archived ESP8266 bridge publishes telemetry through MQTT QoS 1. Mosquitto forwards messages to Spring Boot; Flyway-managed MySQL tables persist them; REST endpoints expose the latest state to the Vue dashboard.",
        left_x,
        left_y,
        col_w,
    )
    left_y -= 3 * mm
    left_y = section_title(canvas, "Vision loop", left_y)
    left_y = draw_para(
        canvas,
        "A downloader restores a public-domain 20-second video and checks its SHA-256 digest. YOLO11n produces JSONL, CSV, annotated video, and benchmark summaries. A publication script posts the summary to the backend, which stores it and serves the latest result to the dashboard.",
        left_x,
        left_y,
        col_w,
    )
    left_y -= 3 * mm
    left_y = section_title(canvas, "Physical prototype provenance", left_y)
    left_y = draw_para(
        canvas,
        "The helmet used an ESP32-CAM for imaging and an ESP8266 as a UART-to-network bridge. Sensor values originated from an STM32 subsystem developed by another contributor. Hardware images and authored firmware are retained as provenance; public tests use simulators.",
        left_x,
        left_y,
        col_w,
    )

    right_y = section_title(canvas, "Implementation map", right_y, x=right_x)
    implementation = [
        ["Layer", "Implementation"],
        ["Messaging", "Eclipse Mosquitto, MQTT QoS 1"],
        ["Backend", "Java, Spring Boot, Flyway"],
        ["Storage", "MySQL"],
        ["Dashboard", "Vue, Vite"],
        ["Vision", "Python, OpenCV, YOLO11n"],
        ["Packaging", "Docker Compose"],
        ["Verification", "JUnit, pytest, smoke tests"],
    ]
    right_y = draw_table(canvas, implementation, right_x, right_y, [30 * mm, col_w - 30 * mm], 7.5)
    right_y -= 7 * mm
    right_y = section_title(canvas, "Independent contributions", right_y, x=right_x)
    right_y = draw_bullets(
        canvas,
        [
            "Public edge-to-cloud architecture and Docker workflow",
            "ESP8266 parsing and cloud integration, plus ESP32-CAM integration",
            "Telemetry ingestion, persistence, REST APIs, and dashboard",
            "Fixed-input vision benchmark and backend publication",
            "Frame-sampling and network-reliability experiments",
            "Scope, provenance, limitations, and repeatability documentation",
        ],
        right_x,
        right_y,
        col_w,
        para_style(8.4, 11.1),
    )
    y2 = min(left_y, right_y) - 7 * mm
    y2 = section_title(canvas, "Reproducibility boundary", y2)
    draw_para(
        canvas,
        "The public workflow validates software behavior without requiring the helmet. It does not represent medical validation, a certified safety product, radio-layer packet loss, or detector accuracy. This boundary keeps every reported claim tied to versioned code and observable measurements.",
        MARGIN,
        y2,
        TEXT_W,
    )


def page_three(canvas: Canvas):
    header(canvas, 3, "Vision experiment")
    y = PAGE_H - 25 * mm
    y = title(canvas, "Frame sampling: latency, throughput, continuity", y)
    y = draw_para(
        canvas,
        "The fixed input contains 600 frames at 1280 x 720 and 30 FPS. YOLO11n runs on CPU at image size 640 with confidence threshold 0.25. Continuity is the percentage of sampled frames containing at least one person detection; it is not an accuracy metric.",
        MARGIN,
        y,
        TEXT_W,
    )
    y -= 3 * mm
    image_h = 91 * mm
    y = draw_image(canvas, VISION, MARGIN, y, TEXT_W, image_h)
    y = draw_para(canvas, "Figure 2. Measured frame-sampling trade-offs on the fixed reference clip.", MARGIN, y - 2 * mm, TEXT_W, CAPTION)
    y -= 4 * mm
    data = [
        ["Stride", "Sampling", "Mean latency", "p95 latency", "Pipeline", "Continuity"],
        ["1", "30 FPS", "124.00 ms", "317.43 ms", "7.59 FPS", "99.50%"],
        ["2", "15 FPS", "109.75 ms", "116.37 ms", "16.08 FPS", "99.33%"],
        ["5", "6 FPS", "108.47 ms", "114.88 ms", "34.56 FPS", "99.17%"],
        ["10", "3 FPS", "110.14 ms", "114.68 ms", "55.35 FPS", "98.33%"],
    ]
    widths = [18 * mm, 24 * mm, 31 * mm, 29 * mm, 27 * mm, 27 * mm]
    y = draw_table(canvas, data, MARGIN, y, widths, 7.2)
    y -= 6 * mm
    y = section_title(canvas, "Interpretation", y)
    draw_para(
        canvas,
        "Stride 1 did not keep pace with the 30 FPS source on the evaluated CPU path. Stride 5 processed the sampled workload at 34.56 pipeline FPS while retaining 99.17% continuity. Stride 10 increased throughput further, but continuity fell to 98.33%. Frame sampling is therefore a useful load-control mechanism for this clip, but continuity must be measured rather than assumed.",
        MARGIN,
        y,
        TEXT_W,
    )


def page_four(canvas: Canvas):
    header(canvas, 4, "Network reliability and conclusions")
    y = PAGE_H - 25 * mm
    y = title(canvas, "Network reliability and conclusions", y)
    col_gap = 8 * mm
    col_w = (TEXT_W - col_gap) / 2
    y_images = y
    left_bottom = draw_image(canvas, DELIVERY, MARGIN, y_images, col_w, 55 * mm)
    right_bottom = draw_image(canvas, RECONNECT, MARGIN + col_w + col_gap, y_images, col_w, 55 * mm)
    y = min(left_bottom, right_bottom) - 3 * mm
    draw_para(canvas, "Figure 3. Attempted-message delivery under seeded loss.", MARGIN, y, col_w, CAPTION)
    y = draw_para(canvas, "Figure 4. Recovery after broker availability.", MARGIN + col_w + col_gap, y, col_w, CAPTION)
    y -= 4 * mm
    results = [
        ["Experiment", "Conditions", "Observed result"],
        ["Added delay", "0-200 ms, 3 x 20 messages", "2.74-207.91 ms mean latency"],
        ["Seeded loss", "0%-40%, 3 x 100 attempts", "100.00%-62.00% delivery"],
        ["Broker outage", "1, 3, 5 s, 3 repeats", "9/9 recovered; 0.78 s subscription mean"],
    ]
    y = draw_table(canvas, results, MARGIN, y, [29 * mm, 56 * mm, TEXT_W - 85 * mm], 7.3)
    y -= 6 * mm
    left_y = section_title(canvas, "Limitations", y)
    left_y = draw_bullets(
        canvas,
        [
            "Offline fixed-video inference, not a live ESP32-CAM stream",
            "No annotated ground truth; continuity is not precision or recall",
            "Single-host Docker trials with application-level loss",
            "Simulators replace physical devices in automated tests",
            "No long-duration field deployment or safety certification",
        ],
        MARGIN,
        left_y,
        col_w,
        para_style(7.7, 9.5),
    )
    right_y = section_title(canvas, "Conclusion", y, x=MARGIN + col_w + col_gap)
    right_y = draw_para(
        canvas,
        "This release demonstrates a complete, inspectable path from telemetry and fixed-video inputs to persistent backend records and a user-facing dashboard. Its strongest evidence is not code volume, but reproducibility: fixed inputs, raw results, regenerable plots, tests, explicit provenance, and bounded claims.",
        MARGIN + col_w + col_gap,
        right_y,
        col_w,
        para_style(8.2, 10.4),
    )
    right_y -= 3 * mm
    right_y = section_title(canvas, "Next evaluation", right_y, x=MARGIN + col_w + col_gap)
    draw_para(
        canvas,
        "Longer repeated runs, confidence intervals, Linux tc netem validation, controlled physical-device trials, and adaptive sampling evaluated only against latency, throughput, continuity, and reliability.",
        MARGIN + col_w + col_gap,
        right_y,
        col_w,
        para_style(8.2, 10.4),
    )


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(OUTPUT), pagesize=A4, pageCompression=1)
    canvas.setTitle("Smart Helmet AIoT: A Reproducible Edge-to-Cloud Safety Monitoring System")
    canvas.setAuthor("Kettkk")
    canvas.setSubject("Technical report for the Smart Helmet AIoT research prototype")
    for renderer in (page_one, page_two, page_three, page_four):
        renderer(canvas)
        canvas.showPage()
    canvas.save()
    print(OUTPUT)


if __name__ == "__main__":
    build()
