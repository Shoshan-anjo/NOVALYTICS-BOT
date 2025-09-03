"""
Login y manejo de sesión con Playwright (sincrónico).
Usa los selectores del login: #userName y #password (según tu HTML).
"""

from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright, TimeoutError as PWTimeoutError
from src.core import settings  # consistente con main.py

def _has_placeholder(s):
    """Detecta placeholders sin resolver tipo {{VAR}}."""
    return isinstance(s, str) and ("{{" in s or "}}" in s)

def _first_selector_that_exists(page, candidates: str) -> str | None:
    """Recibe selectores separados por coma y devuelve el primero que exista."""
    if not candidates:
        return None
    for sel in [c.strip() for c in candidates.split(",")]:
        try:
            if page.query_selector(sel):
                return sel
        except Exception:
            pass
    return None

def ensure_login(pw: Playwright, force: bool | None = None):
    """
    Lanza Chromium, reutiliza storage_state si existe y no se fuerza relogin.
    Hace login si es necesario y guarda storage_state.
    Devuelve (browser, context, page) autenticados.
    """
    headless = settings.browser_headless
    force_relogin = settings.force_relogin if force is None else bool(force)
    storage_path: Path = settings.storage_state_path

    browser = pw.chromium.launch(headless=headless)
    context_kwargs = {
        "viewport": {"width": settings.browser_viewport_width, "height": settings.browser_viewport_height},
        "user_agent": settings.browser_user_agent,
    }

    if storage_path.exists() and not force_relogin:
        context_kwargs["storage_state"] = str(storage_path)

    context = browser.new_context(**context_kwargs)
    page = context.new_page()

    # 1) ¿Ya está logueado?
    if settings.post_login_url:
        try:
            page.goto(settings.post_login_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout)
            page.wait_for_load_state("networkidle", timeout=1500)
            return browser, context, page
        except PWTimeoutError:
            pass
        except Exception:
            pass

    # 2) Ir a login (validando URL)
    login_url = settings.login_url
    if not isinstance(login_url, str) or _has_placeholder(login_url) or not login_url.startswith(("http://", "https://")):
        raise RuntimeError(f"URL de login inválida: {login_url}. Revisa BASE_URL/LOGIN_URL en tu .env o config.json.")

    page.goto(login_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout)

    # Llenar formulario
    username_sel = "#userName"
    password_sel = "#password"
    submit_sel_candidates = "button[type='submit'], button.custom-button"

    page.fill(username_sel, settings.username or "")
    page.fill(password_sel, settings.password or "")

    submit_sel = _first_selector_that_exists(page, submit_sel_candidates)
    if not submit_sel:
        raise RuntimeError("No se encontró el botón de submit del login. Ajusta selectores.")

    page.click(submit_sel)

    # 3) Verificar login OK
    timeout_ms = settings.login_timeout_ms
    probe_candidates = "a.nav-link.active, .navbar, header, .dashboard"
    probe_sel = _first_selector_that_exists(page, probe_candidates)

    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PWTimeoutError:
        pass

    if settings.post_login_url:
        try:
            page.goto(settings.post_login_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout)
        except Exception:
            pass

    ok = False
    if probe_sel:
        try:
            page.wait_for_selector(probe_sel, timeout=timeout_ms)
            ok = True
        except PWTimeoutError:
            ok = False

    if not ok:
        raise RuntimeError("❌ Login no confirmado. Revisa credenciales y selectores.")

    # 4) Guardar storage_state para próximos runs
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(storage_path))
    return browser, context, page

def demo_login():
    """Ejemplo de uso: abre sesión, toma screenshot y cierra."""
    with sync_playwright() as pw:
        browser, context, page = ensure_login(pw)
        out = Path("./data/screenshots/dashboard.png")
        out.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out))
        print(f"📸 Screenshot guardado en: {out}")
        context.close()
        browser.close()
