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

def _looks_logged_in(page) -> bool:
    """
    Heurística de login exitoso:
    - URL ya no contiene '/login'
    - O aparece el link de configuración
    - O aparece algún probe genérico (navbar/dashboard)
    """
    try:
        if "/login" not in page.url.lower():
            return True
    except Exception:
        pass

    probes = [
        "a[href='configuracion']",
        "a.nav-link.active",
        ".navbar",
        "header",
        ".dashboard",
        "[data-test='dashboard']",
    ]
    sel = _first_selector_that_exists(page, ", ".join(probes))
    if not sel:
        return False
    try:
        page.wait_for_selector(sel, timeout=1500)
        return True
    except PWTimeoutError:
        return False

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
            if _looks_logged_in(page):
                return browser, context, page
        except Exception:
            pass  # seguimos al flujo de login si falla

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

    # Esperar navegación tras click de login
    try:
        with page.expect_navigation(wait_until="domcontentloaded", timeout=settings.navigation_timeout):
            page.click(submit_sel)
    except PWTimeoutError:
        # algunos sitios no navegan, solo mutan el DOM
        page.click(submit_sel)

    # 3) Verificar login OK
    try:
        page.wait_for_load_state("networkidle", timeout=settings.login_timeout_ms)
    except PWTimeoutError:
        pass

    if not _looks_logged_in(page):
        # evidencia para debug
        fail_shot = Path("./data/screenshots/login_fail.png")
        fail_shot.parent.mkdir(parents=True, exist_ok=True)
        try:
            page.screenshot(path=str(fail_shot))
        except Exception:
            pass
        raise RuntimeError("❌ Login no confirmado. Se guardó data/screenshots/login_fail.png")

    # 4) Guardar storage_state para próximos runs
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(storage_path))
    return browser, context, page

def go_to_configuracion(page) -> None:
    """
    Navega a la página de Configuración.
    - Primero intenta click en el link.
    - Si no existe, intenta navegar por URL desde settings.configuracion_url.
    """
    # Intento por click
    try:
        if page.query_selector("a[href='configuracion']"):
            page.click("a[href='configuracion']")
            page.wait_for_load_state("networkidle", timeout=settings.navigation_timeout)
            return
    except Exception:
        pass

    # Fallback por URL
    if settings.configuracion_url:
        page.goto(settings.configuracion_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout)
        page.wait_for_load_state("networkidle", timeout=settings.navigation_timeout)
        return

    raise RuntimeError("⚠️ No se pudo navegar a Configuración (ni por click ni por URL).")

def demo_login():
    """
    Arranca Playwright (sin 'with' para no cerrarlo), hace login, navega a Configuración,
    guarda screenshot y devuelve (pw, browser, context, page) SIN cerrarlos.
    """
    pw = sync_playwright().start()   # 👈 NO usamos 'with' para dejarlo vivo
    browser, context, page = ensure_login(pw)

    # Ir a Configuración
    go_to_configuracion(page)
    print("⚙️ Navegación a Configuración exitosa.")

    # Evidencia
    out = Path("./data/screenshots/configuracion.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out))
    print(f"📸 Screenshot guardado en: {out}")

    # 👉 Dejar todo abierto: devolvemos pw también
    return pw, browser, context, page
