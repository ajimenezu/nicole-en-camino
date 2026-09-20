"""El build de Vercel migra la base real: tiene que hacerlo solo en
producción, nunca desde un deploy de preview."""

import build_vercel
import seed_admin


def test_en_preview_no_migra(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "preview")
    llamadas = []
    monkeypatch.setattr(build_vercel.command, "upgrade", lambda *a: llamadas.append(a))
    assert build_vercel.main() == 0
    assert llamadas == []


def test_sin_vercel_env_no_migra(monkeypatch):
    monkeypatch.delenv("VERCEL_ENV", raising=False)
    llamadas = []
    monkeypatch.setattr(build_vercel.command, "upgrade", lambda *a: llamadas.append(a))
    assert build_vercel.main() == 0
    assert llamadas == []


def test_en_produccion_migra_y_despues_siembra_el_admin(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    orden = []
    monkeypatch.setattr(
        build_vercel.command, "upgrade", lambda cfg, rev: orden.append(("migrar", rev))
    )
    monkeypatch.setattr(seed_admin, "main", lambda: orden.append("admin") or 0)
    assert build_vercel.main() == 0
    assert orden == [("migrar", "head"), "admin"]


def test_si_el_seed_falla_el_build_falla(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    monkeypatch.setattr(build_vercel.command, "upgrade", lambda cfg, rev: None)
    monkeypatch.setattr(seed_admin, "main", lambda: 1)
    assert build_vercel.main() == 1
