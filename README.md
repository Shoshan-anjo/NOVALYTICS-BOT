# Novalitics_Bot

```bash
Novalitics_Bot/
├── 📂 src/                    # TODO el código fuente aquí
│   ├── 📂 core/              # Módulos centrales
│   │   ├── 📄 __init__.py
│   │   ├── 📄 settings.py    # Configuración
│   │   └── 📄 logger.py      # Logging configurado
│   │
│   ├── 📂 event/             # Eventos/Monitoreo (minúscula)
│   │   ├── 📄 __init__.py
│   │   └── 📄 file_monitor.py # detector_archivos.py → nombre inglés
│   │
│   ├── 📂 robot/             # Automatización (minúscula) 
│   │   ├── 📄 __init__.py
│   │   └── 📄 browser_control.py # control_navegador.py → inglés
│   │
│   └── 📂 utils/             # Utilidades
│       ├── 📄 __init__.py
│       ├── 📄 helpers.py
│       └── 📄 validators.py
│
├── 📂 config/                 # Configuración (datos)
│   ├── 📄 config.json
│   └── 📄 selectors.json     # selectores.json → inglés
│
├── 📂 logs/                  # Logs (datos)
│   └── 📄 .gitkeep          # Archivo para que Git trackee carpeta vacía
│
├── 📂 data/                  # Datos de la aplicación
│   └── 📄 .gitkeep
│
├── 📄 .env                   # Variables de entorno
├── 📄 .gitignore
├── 📄 requirements.txt
├── 📄 main.py               # Punto de entrada
├── 📄 README.md
└── 📄 setup.py              # Para instalación como paquete
