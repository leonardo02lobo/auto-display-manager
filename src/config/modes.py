"""
Display mode configurations
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class ModeConfig:
    """Configuration for a display mode"""
    name: str
    description: str
    command_template: str


# Available display modes with descriptions
DISPLAY_MODES: Dict[str, ModeConfig] = {
    "extend": ModeConfig(
        name="Extender",
        description="Extiende la pantalla al monitor externo",
        command_template="extend"
    ),
    "mirror": ModeConfig(
        name="Clonar",
        description="Clona la pantalla principal en el monitor externo",
        command_template="mirror"
    ),
    "external-only": ModeConfig(
        name="Solo externo",
        description="Usa solo el monitor externo",
        command_template="external-only"
    ),
    "internal-only": ModeConfig(
        name="Solo interno",
        description="Usa solo la pantalla interna",
        command_template="internal-only"
    ),
    "auto": ModeConfig(
        name="Automático",
        description="Detecta automáticamente y aplica la mejor configuración",
        command_template="auto"
    )
}


def get_mode_list() -> List[str]:
    """Get list of available mode keys"""
    return list(DISPLAY_MODES.keys())


def get_mode_config(mode_key: str) -> ModeConfig:
    """Get configuration for a specific mode"""
    if mode_key not in DISPLAY_MODES:
        raise ValueError(f"Unknown mode: {mode_key}")
    return DISPLAY_MODES[mode_key]
