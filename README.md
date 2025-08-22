
<div style="display: inline-block; text-align: center;">
    <img src="https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3d3FsMGh1MnFtM2U2dXhqdnY3aG8xMzl2c2hpdW1uNXQ0cmx6MDBrNCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/25Itcrcuwkyq3ohubJ/giphy.gif" width="100" style="border-radius: 50%; transition: transform 0.3s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'"/>
    <br/>
    <strong>Shoshan-anjo</strong>
  </div>


# NOVALYTICS-BOT 🤖

Sistema de automatización y monitoreo para análisis de datos con Playwright y Python.

## 🏗️ Estructura del Proyecto


```bash
NOVALYTICS-BOT/  
├── 📄 .env # Variables de entorno (NO subir a Git)  
├── 📄 .env.example # Template de variables de entorno  
├── 📄 .gitignore # Archivos ignorados por Git  
├── 📄 main.py # Punto de entrada principal  
├── 📄 requirements.txt # Dependencias de Python  
├── 📄 README.md # Documentación del proyecto  
│  
├── 📂 config/ # Configuración de la aplicación  
│ ├── 📄 config.json # Configuración principal con variables {{}}  
│ └── 📄 selectors.json # Selectores CSS/XPATH de la UI  
│  
├── 📂 data/ # Datos y archivos de la aplicación  
│ ├── 📂 downloads/ # Archivos descargados  
│ ├── 📂 uploads/ # Archivos para subir  
│ ├── 📂 screenshots/ # Capturas de pantalla  
│ ├── 📂 reports/ # Reportes generados  
│ ├── 📂 backups/ # Copias de seguridad  
│ └── 📂 processed/ # Archivos procesados  
│  
├── 📂 logs/ # Archivos de registro  
│ └── 📄 app.log # Log principal de la aplicación  
│  
└── 📂 src/ # Código fuente de la aplicación  
├── 📂 core/ # Módulos centrales y configuración  
│ ├── 📄  **init**.py # Paquete Python  
│ ├── 📄 config_loader.py # Cargador de configuración (.env + JSON)  
│ └── 📄 settings.py # Configuración principal con properties  
│  
├── 📂 event/ # Monitoreo de eventos y archivos  
│ ├── 📄  **init**.py # Paquete Python  
│ └── 📄 file_monitor.py # Monitor de carpeta compartida  
│  
├── 📂 robot/ # Automatización del navegador  
│ ├── 📄  **init**.py # Paquete Python  
│ └── 📄 browser_control.py # Control de Playwright y automatización  
│  
└── 📂 utils/ # Utilidades y helpers  
├── 📄  **init**.py # Paquete Python  
├── 📄 helpers.py # Funciones de ayuda  
└── 📄 validators.py # Validaciones de datos
```
## 🚀 Características Principales

### 🔧 Configuración Centralizada
- **`.env`** - Variables sensibles (credenciales, URLs)
- **`config.json`** - Configuración general con templates `{{VARIABLE}}`
- **`selectors.json`** - Selectores de UI organizados por páginas

### 🌐 Automatización Web
- **Playwright** - Navegación y automatización moderna
- **Chromium** - Navegador headless/silencioso
- **Selectores robustos** - CSS y XPath optimizados

### 📁 Monitoreo de Archivos
- **Watchdog** - Monitoreo en tiempo real de carpetas
- **Procesamiento automático** - Detección y procesamiento de archivos
- **Múltiples formatos** - Soporte para .xlsx, .xls, .csv

### ⚙️ Configuración Inteligente
```python
from src.core import settings

# Acceso fácil a toda la configuración
url = settings.base_url
folder = settings.shared_folder
headless = settings.browser_headless