"""全局配置常量。"""

from pathlib import Path

SCAN_START_PORT = 2000
SCAN_END_PORT = 2200
CONNECT_TIMEOUT = 5.0
COMMAND_TIMEOUT = 15.0
REGISTRY_PATH = Path.home() / ".ensp-mcp" / "devices.json"
