"""Erzeugt `docs/demo.gif`: den Beweismoment als zwei-Frame-Animation.

Frame A: kein injizierter Fehler  -> Namensinvarianz bestanden, Art. 10 belegt
Frame B: Namensmerkmal injiziert  -> Namensinvarianz rot, Art. 10 faellt auf offen

Kein Projekt-Dependency: Playwright und Pillow werden nur hier gebraucht und
absichtlich nicht in `pyproject.toml` aufgenommen (Pillow kommt ohnehin ueber
Streamlit mit). Aufruf:

    python -m streamlit run app.py --server.port 8502 --server.headless true &
    python scripts/capture_demo.py docs/

Warum zwei Ausschnitte pro Zustand montiert werden: Relation (Schritt 3) und
Konformitaetscheckliste (Schritt 4) liegen in der Seite weit auseinander. Ein
Vollbild-Screenshot waere als GIF unlesbar (256 Farben, dunkles Theme mit
Verlaeufen bandet stark), deshalb wird eng geschnitten und montiert.
"""

import os
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

# Das global installierte Playwright erwartet unter Umstaenden einen
# Chromium-Build, der lokal nicht liegt. Ueber DEMO_CHROME laesst sich ein
# vorhandener Build vorgeben, statt 150 MB nachzuladen.
CHROME = os.environ.get("DEMO_CHROME")
URL = os.environ.get("DEMO_URL", "http://localhost:8502/")
BG = (10, 7, 22)
MARGIN = 16
GAP = 20

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "docs")
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, locator, pad):
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(350)
    box = locator.bounding_box()
    if box is None:
        raise RuntimeError("Element nicht sichtbar")
    buf = page.screenshot(
        clip={
            "x": max(0, box["x"] - pad),
            "y": max(0, box["y"] - pad),
            "width": box["width"] + 2 * pad,
            "height": box["height"] + 2 * pad,
        }
    )
    tmp = OUT / ".shot.png"
    tmp.write_bytes(buf)
    img = Image.open(tmp).convert("RGB")
    img.load()
    tmp.unlink()
    return img


def name_relation(page):
    return (
        page.locator('[data-testid="stExpander"]')
        .filter(has_text="Namensinvarianz")
        .first
    )


def capture():
    frames = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME)
        page = browser.new_page(viewport={"width": 1280, "height": 1500})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2500)

        page.get_by_role("button", name="Bewerber-Vorauswahl").click()
        page.wait_for_timeout(3000)

        for state, inject in (("a", False), ("b", True)):
            if inject:
                # Das Dropdown rendert keine option-Rolle, Tastatur ist
                # robuster. "(keiner)" ist Index 0, der Namensmerkmal-Mutant
                # folgt direkt danach.
                page.locator('[data-testid="stSelectbox"]').nth(2).click()
                page.wait_for_timeout(900)
                page.keyboard.press("ArrowDown")
                page.keyboard.press("Enter")
                page.wait_for_timeout(3000)

            # In beiden Zustaenden aufgeklappt, damit Quell- und Folgefall
            # sichtbar sind. Streamlit setzt kein aria-expanded; der Zustand
            # steht im Pfeil-Icon. Ohne diese Pruefung wuerde der Klick den
            # bei Fehlschlag automatisch geoeffneten Expander wieder zuklappen.
            summary = name_relation(page).locator("summary").first
            if "keyboard_arrow_right" in summary.inner_text():
                summary.click()
                page.wait_for_timeout(900)

            top = shot(page, name_relation(page), pad=12)
            # pad=0: mit Rand schneidet der Ausschnitt die Nachbarzeilen der
            # Checkliste an. Der Rand kommt sauber aus der Montage.
            bottom = shot(
                page, page.locator("li").filter(has_text="Art. 10").last, pad=0
            )
            frames[state] = (top, bottom)

        browser.close()
    return frames


def montage(frames):
    width = max(im.width for pair in frames.values() for im in pair) + 2 * MARGIN
    height = (
        max(t.height + GAP + b.height for t, b in frames.values()) + 2 * MARGIN
    )
    out = []
    for state in ("a", "b"):
        top, bottom = frames[state]
        canvas = Image.new("RGB", (width, height), BG)
        canvas.paste(top, (MARGIN, MARGIN))
        canvas.paste(bottom, (MARGIN, MARGIN + top.height + GAP))
        out.append(canvas)
    return out


def main():
    out = montage(capture())
    gif = OUT / "demo.gif"
    out[0].save(
        gif,
        save_all=True,
        append_images=out[1:],
        duration=[2400, 3000],
        loop=0,
        optimize=True,
    )
    print(f"{gif} {out[0].size} {gif.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
