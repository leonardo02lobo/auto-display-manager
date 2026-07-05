# Auto Display Manager

Gestión automática de pantallas externas en Linux con detección automática de conexión/desconexión.

## Características

- **Detección automática**: Detecta automáticamente cuando conectas o desconectas un monitor externo (HDMI, DisplayPort)
- **Múltiples modos de pantalla**:
  - **Extender**: Extiende la pantalla al monitor externo
  - **Clonar**: Clona la pantalla principal en el monitor externo
  - **Solo externo**: Usa solo el monitor externo
  - **Solo interno**: Usa solo la pantalla interna
  - **Automático**: Detecta automáticamente y aplica la mejor configuración
- **Interfaz gráfica intuitiva**: Fácil de usar con PyQt6
- **System Tray**: Icono en la barra de tareas para acceso rápido
- **Auto-aplicar**: Opción para aplicar configuración automáticamente al conectar un monitor

## Requisitos del Sistema

- Linux (probado en Kali Linux, Debian, Ubuntu)
- Python 3.10 o superior
- xrandr (instalado por defecto en la mayoría de distribuciones Linux)
- Servidor X11 o Wayland con soporte XWayland

## Instalación

### 1. Clonar el repositorio

```bash
cd /home/leonardo/Documentos/Project
git clone https://github.com/TU_USUARIO/auto-display-manager.git
cd auto-display-manager
```

### 2. Crear entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Verificar que xrandr está instalado

```bash
xrandr --version
```

Si xrandr no está instalado, instálalo con:

```bash
sudo apt-get install x11-xserver-utils
```

## Uso

### Ejecutar la aplicación

```bash
python src/main.py
```

O si instalaste el paquete:

```bash
auto-display-manager
```

### Uso de la interfaz

1. **Lista de monitores**: En el panel izquierdo verás todos los monitores detectados con su estado (conectado/desconectado)
2. **Seleccionar modo**: En el panel derecho, selecciona el modo de pantalla deseado del dropdown
3. **Auto-aplicar**: Activa "Aplicar automáticamente al conectar" para que la configuración se aplique automáticamente cuando conectes un monitor
4. **Aplicar configuración**: Haz clic en "Aplicar Configuración" para aplicar el modo seleccionado
5. **System Tray**: La aplicación minimiza al system tray, puedes acceder a ella desde el icono en la barra de tareas

### Modos de pantalla

| Modo | Descripción |
|------|-------------|
| Extender | Extiende el escritorio al monitor externo (ideal para productividad) |
| Clonar | Muestra la misma imagen en ambos monitores (ideal para presentaciones) |
| Solo externo | Usa solo el monitor externo y apaga la pantalla interna |
| Solo interno | Usa solo la pantalla interna (útil al desconectar monitor externo) |
| Automático | Detecta automáticamente y aplica la mejor configuración |

## Troubleshooting

### La aplicación no detecta monitores

1. Verifica que xrandr funcione correctamente:
   ```bash
   xrandr
   ```
2. Asegúrate de tener los permisos necesarios (generalmente no requiere sudo)
3. Verifica que el monitor esté correctamente conectado

### La aplicación no inicia

1. Verifica que Python 3.10+ esté instalado:
   ```bash
   python3 --version
   ```
2. Verifica que todas las dependencias estén instaladas:
   ```bash
   pip list
   ```
3. Revisa el log de errores en la terminal

### Error: "xrandr is not installed"

Instala xrandr:
```bash
sudo apt-get install x11-xserver-utils
```

### Error de permisos

La aplicación generalmente no requiere permisos especiales. Si encuentras problemas de permisos, asegúrate de que tu usuario tenga acceso al sistema de displays.

## Desarrollo

### Estructura del proyecto

```
display-manager/
├── src/
│   ├── main.py              # Punto de entrada
│   ├── gui/
│   │   └── main_window.py   # Ventana principal
│   ├── core/
│   │   ├── display_manager.py   # Lógica de gestión de displays
│   │   ├── xrandr_wrapper.py    # Wrapper para comandos xrandr
│   │   └── monitor_detector.py  # Detección automática
│   └── config/
│       └── modes.py        # Definición de modos
├── requirements.txt
├── setup.py
└── README.md
```

### Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.

## Autor

Auto Display Manager - 2024

## Agradecimientos

- PyQt6 por el framework GUI
- xrandr por la gestión de displays en Linux
