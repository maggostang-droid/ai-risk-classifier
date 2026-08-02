from streamlit.testing.v1 import AppTest


def _run():
    app = AppTest.from_file("app.py", default_timeout=30)
    app.run()
    return app


def test_app_starts_without_exception():
    app = _run()
    assert not app.exception


def test_high_risk_case_shows_all_four_steps():
    app = _run()
    headers = [h.value for h in app.subheader]
    assert any("Einstufung" in h for h in headers)
    assert any("Pflichten" in h for h in headers)
    assert any("Nachweis" in h for h in headers)
    assert any("Artefakt" in h for h in headers)


def test_fault_injection_selectbox_is_present_for_high_risk():
    app = _run()
    labels = [s.label for s in app.selectbox]
    assert any("Fehler injizieren" in label for label in labels)
