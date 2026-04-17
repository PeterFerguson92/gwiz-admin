from __future__ import annotations

import base64
from urllib.parse import urlencode

from django.conf import settings
from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing


def build_check_in_url(token: object) -> str:
    base = (getattr(settings, "PUBLIC_SITE_URL", "/") or "/").strip()
    query = urlencode({"token": str(token)})

    if base == "/":
        return f"/staff/check-in?{query}"

    return f"{base.rstrip('/')}/staff/check-in?{query}"


def build_check_in_qr_drawing(token: object, *, size: int = 128) -> Drawing:
    widget = qr.QrCodeWidget(build_check_in_url(token))
    x0, y0, x1, y1 = widget.getBounds()
    width = x1 - x0
    height = y1 - y0
    scale = min(size / width, size / height)

    drawing = Drawing(
        size,
        size,
        transform=[scale, 0, 0, scale, -x0 * scale, -y0 * scale],
    )
    drawing.add(widget)
    return drawing


def build_check_in_qr_data_url(token: object, *, size: int = 128) -> str:
    svg = renderSVG.drawToString(build_check_in_qr_drawing(token, size=size))
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def build_check_in_qr_context(token: object, *, size: int = 128) -> dict[str, object]:
    return {
        "check_in_url": build_check_in_url(token),
        "check_in_qr_data_url": build_check_in_qr_data_url(token, size=size),
        "check_in_qr_drawing": build_check_in_qr_drawing(token, size=size),
    }


def draw_check_in_qr(
    canvas_obj, token: object, *, x: int, y: int, size: int = 128
) -> None:
    renderPDF.draw(build_check_in_qr_drawing(token, size=size), canvas_obj, x, y)
