"""异步 Telnet 客户端 — 连接 eNSP 虚拟设备控制台、执行 CLI 命令。"""

import asyncio
import re
import socket
import time
from datetime import datetime
from typing import Optional

from .config import SCAN_START_PORT, SCAN_END_PORT, CONNECT_TIMEOUT, COMMAND_TIMEOUT

# 活跃连接池: "host:port" -> (reader, writer)
_active_connections: dict[str, tuple] = {}


def _conn_key(host: str, port: int) -> str:
    return f"{host}:{port}"


async def _telnet_connect(host: str, port: int) -> tuple:
    """建立 telnet 连接，返回 (reader, writer)。"""
    import telnetlib3
    reader, writer = await telnetlib3.open_connection(
        host, port,
        connect_minwait=0.5,
        connect_maxwait=CONNECT_TIMEOUT,
    )
    # 等待初始提示符，丢弃 banner
    try:
        await asyncio.wait_for(reader.read(8192), timeout=2.0)
    except (asyncio.TimeoutError, TimeoutError):
        pass
    return reader, writer


async def get_or_create_session(host: str, port: int) -> tuple:
    """获取或新建 telnet 会话。"""
    key = _conn_key(host, port)
    if key in _active_connections:
        reader, writer = _active_connections[key]
        if not writer.is_closing():
            return reader, writer
        del _active_connections[key]
    reader, writer = await _telnet_connect(host, port)
    _active_connections[key] = (reader, writer)
    return reader, writer


async def send_command(
    host: str, port: int, command: str, timeout: float = COMMAND_TIMEOUT
) -> str:
    """发送 CLI 命令到设备，返回输出。自动处理 ---- More ---- 分页。"""
    reader, writer = await get_or_create_session(host, port)

    # 排空残留
    try:
        while True:
            chunk = await asyncio.wait_for(reader.read(4096), timeout=1.0)
            if not chunk:
                break
    except (asyncio.TimeoutError, TimeoutError):
        pass

    writer.write(command + "\r\n")
    await writer.drain()

    parts: list[str] = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            chunk = await asyncio.wait_for(reader.read(8192), timeout=2.0)
        except (asyncio.TimeoutError, TimeoutError):
            break
        if not chunk:
            break
        text = chunk if isinstance(chunk, str) else chunk.decode("utf-8", errors="replace")
        parts.append(text)

        # 分页
        if "---- More ----" in text or "--- More ---" in text:
            writer.write(" ")
            await writer.drain()
            await asyncio.sleep(0.3)
            continue

        # 检查是否回到设备提示符
        tail = text.strip().rsplit("\n", 2)[-1] if "\n" in text.strip() else text.strip()
        if re.search(r"[<\[]\S+[>\]]", tail):
            break

    return "".join(parts)


def disconnect(host: str, port: int):
    """断开指定连接。"""
    key = _conn_key(host, port)
    if key in _active_connections:
        _, writer = _active_connections.pop(key)
        try:
            writer.close()
        except Exception:
            pass


def disconnect_all():
    """断开所有连接。"""
    for key in list(_active_connections.keys()):
        _, writer = _active_connections.pop(key)
        try:
            writer.close()
        except Exception:
            pass


def port_is_open(host: str, port: int) -> bool:
    """快速 TCP 端口检查。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


async def quick_probe(host: str, port: int) -> Optional[str]:
    """快速探测端口是否为 eNSP 设备，返回设备名或 None。"""
    try:
        reader, writer = await asyncio.wait_for(
            _telnet_connect(host, port),
            timeout=3.0,
        )
        writer.write("\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(4096), timeout=2.0)
        if not data:
            return None
        text = data if isinstance(data, str) else data.decode("utf-8", errors="replace")
        m = re.search(r"[<\[](\S+)[>\]]", text)
        if m:
            return m.group(1)
        writer.close()
    except Exception:
        pass
    return None


def _classify_device(name: str) -> str:
    """根据设备名称推断设备类型。"""
    n = name.upper()
    if any(k in n for k in ("AR", "ROUTER")):
        return "router"
    if any(k in n for k in ("SW", "LSW", "SWITCH")):
        return "switch"
    if any(k in n for k in ("FW", "USG", "FIREWALL")):
        return "firewall"
    return "unknown"


async def scan_devices(
    registry,
    start_port: int = SCAN_START_PORT,
    end_port: int = SCAN_END_PORT,
) -> list[dict]:
    """扫描本地端口范围，发现并注册运行中的 eNSP 虚拟设备。"""
    found = []
    for port in range(start_port, end_port + 1):
        if not port_is_open("127.0.0.1", port):
            continue
        name = await quick_probe("127.0.0.1", port)
        if name:
            dev_type = _classify_device(name)
            registry.add(name, "127.0.0.1", port, dev_type)
            found.append({"name": name, "port": port, "type": dev_type})
    return found
