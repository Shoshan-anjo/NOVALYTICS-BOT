"""
Módulo de automatización para la página 'Iniciar análisis'.
Selecciona parámetros, adjunta archivo y presiona enviar.
"""

import logging
from pathlib import Path
from time import sleep
from playwright.sync_api import Page, TimeoutError as PWTimeoutError
from src.core import settings

logger = logging.getLogger(__name__)

# Selectores
SEL_NAV_ANALISIS = "a[href='iniciar-analisis']"
SEL_PARAMETRO    = "#parameterSelect"
SEL_SERVICIO     = "#serviceSelect"
SEL_UPLOAD_LABEL = "label.upload-btn"
SEL_FILE_INPUT   = "label.upload-btn input[type='file']"
SEL_FILE_NAME    = "#file-name"
SEL_SUBMIT_BTN   = "button.custom-button"


def _wait(page: Page, selector: str, state: str = "visible", timeout: int | None = None):
    page.wait_for_selector(selector, state=state, timeout=timeout or settings.browser_timeout)


def go_to_analisis(page: Page) -> None:
    """Asegura estar en /iniciar-analisis."""
    try:
        if page.query_selector(SEL_NAV_ANALISIS):
            page.click(SEL_NAV_ANALISIS)
            page.wait_for_load_state("networkidle", timeout=settings.navigation_timeout)
            return
    except Exception:
        pass
    page.goto(settings.analisis_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout)
    page.wait_for_load_state("networkidle", timeout=settings.navigation_timeout)


def perform_upload(page: Page, file_path: Path) -> None:
    logger.info(f"📤 Subiendo archivo: {file_path.name}")
    go_to_analisis(page)

    # Seleccionar parámetros
    try:
        if page.query_selector(SEL_PARAMETRO):
            _wait(page, SEL_PARAMETRO, "visible")
            try:
                page.select_option(SEL_PARAMETRO, value=str(settings.default_parametro))
            except Exception:
                page.select_option(SEL_PARAMETRO, label=str(settings.default_parametro))
            logger.info(f"✔️ Parámetro: {settings.default_parametro}")
    except PWTimeoutError:
        logger.warning("⚠️ No se encontró selector de parámetro a tiempo.")

    try:
        if page.query_selector(SEL_SERVICIO):
            _wait(page, SEL_SERVICIO, "visible")
            try:
                page.select_option(SEL_SERVICIO, value=str(settings.default_servicio))
            except Exception:
                page.select_option(SEL_SERVICIO, label=str(settings.default_servicio))
            logger.info(f"✔️ Servicio: {settings.default_servicio}")
    except PWTimeoutError:
        logger.warning("⚠️ No se encontró selector de servicio a tiempo.")

    # Adjuntar archivo
    try:
        if page.query_selector(SEL_UPLOAD_LABEL):
            page.click(SEL_UPLOAD_LABEL)
            sleep(0.15)
    except Exception:
        pass

    _wait(page, SEL_FILE_INPUT, "attached")
    page.set_input_files(SEL_FILE_INPUT, str(file_path))
    logger.info(f"📎 Archivo adjuntado: {file_path.name}")

    # Confirmar nombre
    try:
        if page.query_selector(SEL_FILE_NAME):
            for _ in range(10):
                val = page.eval_on_selector(SEL_FILE_NAME, "el => el.value || el.getAttribute('value') || el.placeholder")
                if isinstance(val, str) and file_path.name in val:
                    break
                sleep(0.15)
    except Exception:
        pass

    # Enviar
    if not page.query_selector(SEL_SUBMIT_BTN):
        raise RuntimeError("No se encontró el botón de envío en la página de análisis.")

    try:
        with page.expect_navigation(wait_until="domcontentloaded", timeout=settings.navigation_timeout):
            page.click(SEL_SUBMIT_BTN)
    except PWTimeoutError:
        page.click(SEL_SUBMIT_BTN)

    try:
        page.wait_for_load_state("networkidle", timeout=max(2000, settings.wait_after_submit_ms))
    except PWTimeoutError:
        pass

    logger.info("✅ Envío completado (espera 'networkidle').")
