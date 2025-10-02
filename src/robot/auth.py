"""
Login y manejo de sesión con Playwright.
Usa los selectores del login: #userName y #password (según tu HTML).
"""

from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright, TimeoutError as PlaywrightTimeoutError
from src.core import settings
from src.core.settings import has_placeholder  # función auxiliar de settings

# Selectores del login
SEL_USERNAME = "#userName"
SEL_PASSWORD = "#password"
SEL_SUBMIT   = "button[type='submit'], button.custom-button"


def _first_selector_that_exists(page, candidates: str) -> str | None:
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
    Devuelve (browser, context, page).
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

    # Ir a login
    login_url = settings.login_url
    if not isinstance(login_url, str) or has_placeholder(login_url) or not login_url.startswith(("http://", "https://")):
        raise RuntimeError(f"URL de login inválida: {login_url}. Revisa BASE_URL/LOGIN_URL en tu .env o config.json.")

    page.goto(login_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout)

    # Llenar login
    page.fill(SEL_USERNAME, settings.username or "")
    page.fill(SEL_PASSWORD, settings.password or "")

    submit_sel = _first_selector_that_exists(page, SEL_SUBMIT)
    if not submit_sel:
        raise RuntimeError("No se encontró el botón de submit del login.")

    page.click(submit_sel)

    # Verificar login
    try:
        page.wait_for_load_state("networkidle", timeout=settings.login_timeout_ms)
    except PlaywrightTimeoutError:
        pass

    # Guardar storage_state
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(storage_path))
    return browser, context, page


def demo_login():
    """Ejemplo de uso: abre sesión y devuelve (pw, browser, context, page)."""
    pw = sync_playwright().start()
    browser, context, page = ensure_login(pw)
    # Navegar directamente a iniciar-analisis
    page.goto(settings.analisis_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout)
    return pw, browser, context, page
