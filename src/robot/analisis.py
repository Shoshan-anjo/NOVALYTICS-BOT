"""
Módulo de automatización para la página 'Iniciar análisis'.
- Navega a /iniciar-analisis
- Selecciona 'Escuchar Reclamos' (value=30) u otra opción si no existe
- Adjunta archivo (evita el diálogo nativo)
- Click en el botón correcto 'Iniciar' (i.bi-power) cuando esté habilitado
"""

import logging
from pathlib import Path
from time import sleep
from typing import Optional, List, Dict, Tuple

from playwright.sync_api import Page, TimeoutError as PWTimeoutError
from src.core import settings

logger = logging.getLogger(__name__)

# Selectores
SEL_NAV_ANALISIS = "a[href='iniciar-analisis']"

# <select id="parameterSelect" class="input-estandar">
SEL_PARAMETRO    = "#parameterSelect"
SEL_SERVICIO     = "#serviceSelect"

# Adjuntar
SEL_UPLOAD_LABEL = "label.upload-btn"
# Intentamos anidado y también un input global con accept por si cambia el DOM
SEL_FILE_INPUT   = "label.upload-btn input[type='file'], input[type='file'][accept*='.xls']"
SEL_FILE_NAME    = "#file-name"

# Botón INICIAR con icono de power
SEL_INICIAR_POWER_BTN_ALL     = "button.custom-button:has(i.bi-power)"
SEL_INICIAR_POWER_BTN_ENABLED = "button.custom-button:has(i.bi-power):not([disabled])"


def _wait(page: Page, selector: str, state: str = "visible", timeout: Optional[int] = None):
    """Wrapper de espera con timeout por default desde settings."""
    page.wait_for_selector(selector, state=state, timeout=timeout or settings.browser_timeout)


def go_to_analisis(page: Page) -> None:
    """Asegura estar en /iniciar-analisis (por click en navbar o por URL directa)."""
    try:
        nav = page.query_selector(SEL_NAV_ANALISIS)
        if nav:
            nav.click()
            page.wait_for_load_state("networkidle", timeout=settings.navigation_timeout)
            return
    except Exception:
        pass

    page.goto(settings.analisis_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout)
    page.wait_for_load_state("networkidle", timeout=settings.navigation_timeout)


# ---------- Helpers de <select> ----------
def _read_options(page: Page, selector: str) -> List[Dict[str, str]]:
    """Lee opciones de un <select> como [{'value': '30', 'label': 'Escuchar Reclamos', 'disabled': false}, ...]."""
    return page.eval_on_selector(
        selector,
        """(el) => Array.from(el.options).map(o => ({
              value: o.value ?? '',
              label: (o.textContent || '').trim(),
              disabled: !!o.disabled
        }))"""
    )

def _choose_option(options: List[Dict[str, str]], preferred: Optional[str], preferred_label: Optional[str]) -> Tuple[Optional[str], Optional[str], str]:
    """
    Prioridad:
      1) value == preferred
      2) label == preferred_label (case-insensitive)
      3) primera opción válida (value != '' y !disabled)
    """
    if not options:
        return None, None, "sin-opciones"

    if preferred:
        for o in options:
            if o.get("value", "") == preferred:
                return o["value"], o.get("label") or o["value"], "value-match"

    if preferred_label:
        pref_cf = preferred_label.casefold()
        for o in options:
            if (o.get("label") or "").casefold() == pref_cf:
                return o["value"], o.get("label") or o["value"], "label-match"

    for o in options:
        if not o.get("disabled") and (o.get("value") or "") != "":
            return o["value"], o.get("label") or o["value"], "first-nonempty"

    return None, None, "solo-vacias/disabled"

def _set_select_exact(page: Page, selector: str, preferred_value: Optional[str], preferred_label: Optional[str], nombre: str) -> None:
    """
    Selecciona una opción específica en el <select>.
    preferred_value='30' (Escuchar Reclamos), preferred_label='Escuchar Reclamos' como respaldo.
    """
    _wait(page, selector, "visible")
    options = _read_options(page, selector)
    value, label, reason = _choose_option(options, preferred_value, preferred_label)

    if value is None or value == "":
        raise RuntimeError(f"{nombre}: no se encontró una opción válida para seleccionar.")

    try:
        page.select_option(selector, value=value)
    except Exception:
        page.select_option(selector, label=label)

    # Eventos para que el frontend reaccione
    try:
        page.evaluate(
            """(sel) => {
                const el = document.querySelector(sel);
                if (!el) return;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            selector
        )
    except Exception:
        pass

    logger.info(f"✔️ {nombre}: '{label}' (value='{value}', preferido='{preferred_value or preferred_label}', modo='{reason}')")


# ---------- Adjuntar archivo robusto ----------
def _attach_file_robusto(page: Page, file_path: Path) -> None:
    """
    Adjunta archivo evitando el diálogo nativo:
    1) set_input_files directo
    2) click al label y reintento
    3) file_chooser fallback
    Intenta sincronizar el display #file-name si el frontend no lo hace.
    """
    file_abs = str(Path(file_path).resolve())
    e1 = e2 = e3 = None

    # Intento 1: directo
    try:
        _wait(page, SEL_FILE_INPUT, "attached")
        page.set_input_files(SEL_FILE_INPUT, file_abs)
        logger.info(f"📎 Archivo adjuntado (directo): {file_path.name}")
    except Exception as _e1:
        e1 = _e1
        logger.debug(f"ℹ️ set_input_files directo no disponible aún: {e1}")

        # Intento 2: click en label + reintento
        try:
            if page.query_selector(SEL_UPLOAD_LABEL):
                page.click(SEL_UPLOAD_LABEL)
                sleep(0.15)
            _wait(page, SEL_FILE_INPUT, "attached", timeout=4000)
            page.set_input_files(SEL_FILE_INPUT, file_abs)
            logger.info(f"📎 Archivo adjuntado (tras click label): {file_path.name}")
        except Exception as _e2:
            e2 = _e2
            logger.debug(f"ℹ️ set_input_files post-label falló: {e2}")

            # Intento 3: capturar file chooser
            try:
                with page.expect_file_chooser(timeout=4000) as fc_info:
                    if page.query_selector(SEL_UPLOAD_LABEL):
                        page.click(SEL_UPLOAD_LABEL)
                    else:
                        if page.query_selector(SEL_FILE_INPUT):
                            page.click(SEL_FILE_INPUT)
                fc = fc_info.value
                fc.set_files(file_abs)
                logger.info(f"📎 Archivo adjuntado (file_chooser): {file_path.name}")
            except Exception as _e3:
                e3 = _e3
                raise RuntimeError(
                    "No fue posible adjuntar el archivo.\n"
                    f"Directo='{e1}'\nLabel='{e2}'\nFileChooser='{e3}'"
                )

    # Confirmación visual (opcional)
    try:
        if page.query_selector(SEL_FILE_NAME):
            for _ in range(8):  # más ágil
                val = page.eval_on_selector(
                    SEL_FILE_NAME,
                    "el => el.value || el.getAttribute('value') || el.placeholder || ''"
                )
                if isinstance(val, str) and file_path.name in val:
                    break
                sleep(0.1)
    except Exception:
        pass


# ---------- Click en el botón correcto 'Iniciar' ----------
def _click_iniciar(page: Page) -> None:
    """
    Click en el botón 'Iniciar' correcto (i.bi-power), esperando a que se habilite.
    Evita asumir navegación completa (muchas UIs hacen XHR sin cambiar URL).
    """
    # Espera ACTIVA a que exista y esté habilitado
    try:
        page.wait_for_function(
            """() => {
                const btns = Array.from(document.querySelectorAll("button.custom-button"));
                const match = btns.find(b => b.querySelector("i.bi.bi-power") && !b.disabled);
                return !!match;
            }""",
            timeout=max(800, min(settings.wait_after_upload_ms, 4000))
        )
    except PWTimeoutError:
        pass

    btn = page.query_selector(SEL_INICIAR_POWER_BTN_ENABLED)
    if not btn:
        any_btn = page.query_selector(SEL_INICIAR_POWER_BTN_ALL)
        if any_btn and any_btn.get_attribute("disabled") is not None:
            raise RuntimeError("El botón 'Iniciar' (con i.bi-power) sigue deshabilitado. Verifica selección y archivo adjunto.")
        raise RuntimeError("No se encontró el botón 'Iniciar' correcto (i.bi-power). Revisa los selectores.")

    try:
        btn.click()
    except PWTimeoutError:
        sleep(0.1)
        btn.click()

    try:
        page.wait_for_load_state("networkidle", timeout=max(1200, min(settings.wait_after_submit_ms, 5000)))
    except PWTimeoutError:
        pass

    logger.info("▶️ Click en 'Iniciar' ejecutado en el botón correcto (i.bi-power).")


# ---------- Flujo principal ----------
def perform_upload(page: Page, file_path: Path) -> None:
    """
    Flujo:
      - Ir a iniciar-analisis
      - Seleccionar parámetro (prioriza '30'/'Escuchar Reclamos' si existe)
      - Seleccionar servicio (opcional) si existe
      - Adjuntar archivo
      - Click en 'Iniciar'
    """
    logger.info(f"📤 Subiendo archivo: {file_path.name}")
    go_to_analisis(page)

    # Parámetro: intenta '30' (Escuchar Reclamos); si no existe, elige la primera opción válida
    try:
        if page.query_selector(SEL_PARAMETRO):
            try:
                _set_select_exact(page, SEL_PARAMETRO, preferred_value="30", preferred_label="Escuchar Reclamos", nombre="Parámetro")
            except Exception as e:
                logger.warning(f"⚠️ No se encontró 'Escuchar Reclamos' por value/label, se elegirá la primera opción válida. Detalle: {e}")
                _set_select_exact(page, SEL_PARAMETRO, preferred_value=None, preferred_label=None, nombre="Parámetro")
    except PWTimeoutError:
        logger.warning("⚠️ Parámetro: no se encontró a tiempo.")

    # Servicio (si existe)
    try:
        if page.query_selector(SEL_SERVICIO):
            _set_select_exact(page, SEL_SERVICIO, preferred_value=str(settings.default_servicio), preferred_label=str(settings.default_servicio), nombre="Servicio")
    except PWTimeoutError:
        logger.warning("⚠️ Servicio: no se encontró a tiempo.")

    # Adjuntar archivo
    _attach_file_robusto(page, file_path)

    # Pequeña pausa para que la UI habilite el botón tras eventos
    sleep(0.1)

    # Iniciar
    _click_iniciar(page)
