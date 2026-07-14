"""设备注册表 — 持久化设备信息到 JSON 文件。"""

import json
from datetime import datetime
from .config import REGISTRY_PATH


class DeviceRegistry:
    """管理已知 eNSP 设备的注册、查询和持久化。"""

    def __init__(self):
        self._devices: dict[str, dict] = {}
        self._load()

    def _load(self):
        if REGISTRY_PATH.exists():
            try:
                self._devices = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._devices = {}

    def save(self):
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        REGISTRY_PATH.write_text(
            json.dumps(self._devices, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, name: str, host: str, port: int, device_type: str = "unknown"):
        self._devices[name] = {
            "host": host,
            "port": port,
            "type": device_type,
            "last_seen": datetime.now().isoformat(),
        }
        self.save()

    def remove(self, name: str):
        self._devices.pop(name, None)
        self.save()

    def get(self, name: str) -> dict | None:
        return self._devices.get(name)

    def list_all(self) -> list[dict]:
        return list(self._devices.values())

    def resolve(self, device: str) -> tuple[str, int]:
        """根据设备名解析 (host, port)。失败则抛出 ValueError。"""
        info = self._devices.get(device)
        if not info:
            raise ValueError(f"设备 '{device}' 未在注册表中。请先执行 scan_devices 发现设备。")
        host = info.get("host", "127.0.0.1")
        port = info.get("port")
        if not port:
            raise ValueError(f"设备 '{device}' 缺少端口信息。")
        return host, int(port)

    def __bool__(self):
        return bool(self._devices)

    def __len__(self):
        return len(self._devices)


# 全局单例
registry = DeviceRegistry()
