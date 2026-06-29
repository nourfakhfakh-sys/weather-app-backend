 
import json
import csv
import io
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def to_json(records: list[dict]) -> bytes:
    return json.dumps(records, indent=2, ensure_ascii=False).encode("utf-8")


def to_csv(records: list[dict]) -> bytes:
    if not records:
        return b""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(records[0].keys()))
    writer.writeheader()
    for r in records:
        row = r.copy()
        row["temperature_data"] = json.dumps(row.get("temperature_data", []))
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def to_xml(records: list[dict]) -> bytes:
    root = Element("weather_records")
    for r in records:
        record_el = SubElement(root, "record", id=str(r.get("id")))
        for key, value in r.items():
            if key == "id":
                continue
            child = SubElement(record_el, key)
            child.text = json.dumps(value) if isinstance(value, (list, dict)) else str(value)
    rough = tostring(root, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ").encode("utf-8")


def to_markdown(records: list[dict]) -> bytes:
    lines = ["# Export des données météo", ""]
    for r in records:
        lines.append(f"## Enregistrement #{r.get('id')} — {r.get('resolved_name')}, {r.get('country')}")
        lines.append(f"- Période: {r.get('start_date')} → {r.get('end_date')}")
        lines.append(f"- Coordonnées: ({r.get('latitude')}, {r.get('longitude')})")
        lines.append("")
        lines.append("| Date | Temp Max (°C) | Temp Min (°C) | Précipitation (mm) |")
        lines.append("|------|---------------|---------------|---------------------|")
        for day in r.get("temperature_data", []):
            lines.append(
                f"| {day.get('date')} | {day.get('temp_max_c')} | {day.get('temp_min_c')} | {day.get('precipitation_mm')} |"
            )
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def to_pdf(records: list[dict]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Export des données météo")
    y -= 30
    c.setFont("Helvetica", 10)

    for r in records:
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, f"#{r.get('id')} - {r.get('resolved_name')}, {r.get('country')}")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(40, y, f"Période: {r.get('start_date')} -> {r.get('end_date')}")
        y -= 15
        for day in r.get("temperature_data", []):
            line = f"  {day.get('date')}: max {day.get('temp_max_c')}C / min {day.get('temp_min_c')}C / pluie {day.get('precipitation_mm')}mm"
            c.drawString(40, y, line)
            y -= 12
            if y < 80:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 9)
        y -= 10

    c.save()
    return buffer.getvalue()


EXPORTERS = {
    "json": (to_json, "application/json", "weather_export.json"),
    "csv": (to_csv, "text/csv", "weather_export.csv"),
    "xml": (to_xml, "application/xml", "weather_export.xml"),
    "markdown": (to_markdown, "text/markdown", "weather_export.md"),
    "pdf": (to_pdf, "application/pdf", "weather_export.pdf"),
}
