"""MCP 工具定义 — 20 个工具的元数据 + 分发处理。"""

import json
import time
from datetime import datetime
from ipaddress import IPv4Network

from mcp.types import Tool, TextContent

from .registry import registry
from . import telnet

# ============================================================
# 工具元数据
# ============================================================

TOOLS = [
    # ── 设备发现 ──
    Tool(
        name="scan_devices",
        description="扫描本地端口（2000-2200），发现当前运行的 eNSP 虚拟设备及其控制台端口。返回设备名称、端口号、设备类型。",
        inputSchema={
            "type": "object",
            "properties": {
                "start_port": {"type": "integer", "description": "扫描起始端口，默认 2000"},
                "end_port": {"type": "integer", "description": "扫描结束端口，默认 2200"},
            },
        },
    ),
    Tool(
        name="list_devices",
        description="列出所有已注册/已发现的设备及其基本信息（名称、端口、类型、最后在线时间）。",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_device_info",
        description="获取指定设备的详细信息：端口号、设备型号、软件版本、运行状态。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称（如 AR1, SW1）"},
            },
            "required": ["device"],
        },
    ),
    # ── 设备状态 ──
    Tool(
        name="get_device_status",
        description="检查设备是否在线、控制台端口是否可达。返回在线状态和响应延迟。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
            },
            "required": ["device"],
        },
    ),
    Tool(
        name="connect_device",
        description="建立到设备控制台的 Telnet 会话。后续可使用 send_command 发送命令。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
                "port": {"type": "integer", "description": "控制台端口（如未指定则从注册表中查找）"},
            },
            "required": ["device"],
        },
    ),
    Tool(
        name="disconnect_device",
        description="断开设备控制台连接，释放会话资源。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
            },
            "required": ["device"],
        },
    ),
    # ── 命令执行 ──
    Tool(
        name="send_command",
        description="在设备上执行一条 CLI 命令并返回输出。自动处理分页。支持任意视图下的 display/diagnose 命令。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
                "command": {"type": "string", "description": "要执行的命令（如 display version）"},
            },
            "required": ["device", "command"],
        },
    ),
    Tool(
        name="send_commands",
        description="在设备上批量执行多条 CLI 命令，按顺序执行并返回所有输出。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
                "commands": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要执行的命令列表",
                },
            },
            "required": ["device", "commands"],
        },
    ),
    # ── 信息查询 ──
    Tool(
        name="get_version",
        description="获取设备软件版本和硬件信息（display version）。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
            },
            "required": ["device"],
        },
    ),
    Tool(
        name="get_running_config",
        description="获取设备当前运行配置（display current-configuration）。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
            },
            "required": ["device"],
        },
    ),
    Tool(
        name="get_startup_config",
        description="获取设备启动配置（display saved-configuration）。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
            },
            "required": ["device"],
        },
    ),
    Tool(
        name="get_interface_brief",
        description="获取设备所有接口的摘要信息（display ip interface brief），包括 IP、状态、协议。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
            },
            "required": ["device"],
        },
    ),
    Tool(
        name="get_interface_detail",
        description="获取指定接口的详细信息：MAC、速率、双工模式、收发包统计等。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
                "interface": {"type": "string", "description": "接口名（如 GigabitEthernet0/0/0）"},
            },
            "required": ["device", "interface"],
        },
    ),
    Tool(
        name="get_lldp_neighbors",
        description="获取 LLDP 邻居信息（display lldp neighbor brief），显示设备间的拓扑连接关系。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
            },
            "required": ["device"],
        },
    ),
    Tool(
        name="get_arp_table",
        description="获取设备 ARP 表（display arp all），查看 IP-MAC 绑定。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
            },
            "required": ["device"],
        },
    ),
    Tool(
        name="get_mac_table",
        description="获取交换机 MAC 地址表（display mac-address），查看端口学习到的 MAC。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称（通常为交换机）"},
            },
            "required": ["device"],
        },
    ),
    # ── 设备配置 ──
    Tool(
        name="configure_interface_ip",
        description="配置接口 IP 地址。自动进入系统视图→接口视图，配置完后返回用户视图。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
                "interface": {"type": "string", "description": "接口名（如 GigabitEthernet0/0/0）"},
                "ip": {"type": "string", "description": "IP 地址，含掩码（如 192.168.1.1/24 或 192.168.1.1 255.255.255.0）"},
            },
            "required": ["device", "interface", "ip"],
        },
    ),
    Tool(
        name="configure_vlan",
        description="创建或删除 VLAN（交换机操作）。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "交换机名称"},
                "vlan_id": {"type": "integer", "description": "VLAN ID（1-4094）"},
                "action": {"type": "string", "enum": ["create", "delete"], "description": "create 或 delete"},
            },
            "required": ["device", "vlan_id", "action"],
        },
    ),
    Tool(
        name="configure_static_route",
        description="配置静态路由。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "设备名称"},
                "destination": {"type": "string", "description": "目标网段（如 10.0.0.0）"},
                "mask": {"type": "string", "description": "子网掩码（如 255.255.255.0 或 /24 形式）"},
                "next_hop": {"type": "string", "description": "下一跳 IP 地址或出接口名"},
                "action": {"type": "string", "enum": ["add", "delete"], "description": "add 添加路由，delete 删除路由"},
            },
            "required": ["device", "destination", "mask", "next_hop", "action"],
        },
    ),
    Tool(
        name="ping_test",
        description="从设备发起 Ping 测试，检查网络连通性。",
        inputSchema={
            "type": "object",
            "properties": {
                "device": {"type": "string", "description": "源设备名称"},
                "target": {"type": "string", "description": "目标 IP 地址"},
                "count": {"type": "integer", "description": "Ping 包数量，默认 5"},
            },
            "required": ["device", "target"],
        },
    ),
]

# ============================================================
# 工具分发映射
# ============================================================

_HANDLERS: dict[str, callable] = {}


def handler(name: str):
    """装饰器：注册工具处理函数。"""
    def decorator(fn):
        _HANDLERS[name] = fn
        return fn
    return decorator


async def dispatch(name: str, arguments: dict) -> list[TextContent]:
    """根据工具名调用对应 handler。"""
    if name in _HANDLERS:
        return await _HANDLERS[name](arguments)
    return [TextContent(type="text", text=f"未知工具: {name}")]


# ============================================================
# 工具实现
# ============================================================

def _resolve(device: str) -> tuple[str, int]:
    return registry.resolve(device)


def _parse_ip_mask(ip_raw: str) -> tuple[str, str]:
    """解析 IP，返回 (ip, mask)。支持 /24 和 255.255.255.0 两种格式。"""
    if "/" in ip_raw:
        ip_addr, prefix = ip_raw.split("/")
        net = IPv4Network(f"{ip_addr}/{prefix}", strict=False)
        return ip_addr, str(net.netmask)
    parts = ip_raw.split()
    return parts[0], parts[1] if len(parts) > 1 else "255.255.255.0"


def _parse_route_mask(mask_raw: str) -> str:
    """解析路由掩码。"""
    if mask_raw.startswith("/"):
        net = IPv4Network(f"0.0.0.0/{mask_raw[1:]}", strict=False)
        return str(net.netmask)
    return mask_raw


@handler("scan_devices")
async def h_scan_devices(args: dict) -> list[TextContent]:
    start = args.get("start_port", 2000)
    end = args.get("end_port", 2200)
    found = await telnet.scan_devices(registry, int(start), int(end))
    if not found:
        return [TextContent(type="text", text="未发现任何运行中的 eNSP 设备。请确保已在 eNSP 中启动设备。")]
    return [TextContent(
        type="text",
        text=json.dumps({"found": len(found), "devices": found}, indent=2, ensure_ascii=False),
    )]


@handler("list_devices")
async def h_list_devices(args: dict) -> list[TextContent]:
    if not registry:
        return [TextContent(type="text", text="设备注册表为空。请先执行 scan_devices 发现设备。")]
    return [TextContent(type="text", text=json.dumps(registry.list_all(), indent=2, ensure_ascii=False))]


@handler("get_device_info")
async def h_get_device_info(args: dict) -> list[TextContent]:
    device = args["device"]
    info = registry.get(device)
    if not info:
        return [TextContent(type="text", text=f"未找到设备 '{device}'。")]
    host, port = _resolve(device)
    ver = await telnet.send_command(host, port, "display version")
    return [TextContent(type="text", text=f"=== {device} 基本信息 ===\n{json.dumps(info, indent=2, ensure_ascii=False)}\n\n=== 版本信息 ===\n{ver}")]


@handler("get_device_status")
async def h_get_device_status(args: dict) -> list[TextContent]:
    device = args["device"]
    info = registry.get(device)
    if not info:
        return [TextContent(type="text", text=f"设备 '{device}' 未注册。请先执行 scan_devices。")]
    port = info.get("port")
    host = info.get("host", "127.0.0.1")
    t0 = time.time()
    online = telnet.port_is_open(host, int(port))
    latency = round((time.time() - t0) * 1000, 1) if online else None
    return [TextContent(type="text", text=json.dumps({
        "device": device, "online": online, "port": port, "latency_ms": latency,
    }, indent=2, ensure_ascii=False))]


@handler("connect_device")
async def h_connect_device(args: dict) -> list[TextContent]:
    device = args["device"]
    if "port" in args:
        host, port = "127.0.0.1", int(args["port"])
        name = await telnet.quick_probe(host, port)
        if name:
            registry.add(name, host, port, "unknown")
            device = name
        else:
            registry.add(device, host, port, "unknown")
    else:
        host, port = _resolve(device)
    await telnet.get_or_create_session(host, port)
    return [TextContent(type="text", text=f"已连接到 {device} ({host}:{port})。")]


@handler("disconnect_device")
async def h_disconnect_device(args: dict) -> list[TextContent]:
    device = args["device"]
    info = registry.get(device)
    if info:
        host = info.get("host", "127.0.0.1")
        port = info.get("port")
        if port:
            telnet.disconnect(host, int(port))
            return [TextContent(type="text", text=f"已断开 {device}。")]
    return [TextContent(type="text", text=f"设备 '{device}' 没有活跃的连接。")]


@handler("send_command")
async def h_send_command(args: dict) -> list[TextContent]:
    device, command = args["device"], args["command"]
    host, port = _resolve(device)
    out = await telnet.send_command(host, port, command)
    return [TextContent(type="text", text=out)]


@handler("send_commands")
async def h_send_commands(args: dict) -> list[TextContent]:
    device, commands = args["device"], args["commands"]
    host, port = _resolve(device)
    results = []
    for cmd in commands:
        out = await telnet.send_command(host, port, cmd)
        results.append(f"> {cmd}\n{out}")
    return [TextContent(type="text", text="\n\n".join(results))]


@handler("get_version")
async def h_get_version(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    out = await telnet.send_command(host, port, "display version")
    return [TextContent(type="text", text=out)]


@handler("get_running_config")
async def h_get_running_config(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    out = await telnet.send_command(host, port, "display current-configuration")
    return [TextContent(type="text", text=out if out.strip() else "未能获取运行配置。")]


@handler("get_startup_config")
async def h_get_startup_config(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    out = await telnet.send_command(host, port, "display saved-configuration")
    return [TextContent(type="text", text=out if out.strip() else "未能获取启动配置（可能未保存过配置）。")]


@handler("get_interface_brief")
async def h_get_interface_brief(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    out = await telnet.send_command(host, port, "display ip interface brief")
    return [TextContent(type="text", text=out)]


@handler("get_interface_detail")
async def h_get_interface_detail(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    intf = args["interface"]
    out = await telnet.send_command(host, port, f"display interface {intf}")
    return [TextContent(type="text", text=out if out.strip() else f"接口 {intf} 不存在或无数据。")]


@handler("get_lldp_neighbors")
async def h_get_lldp_neighbors(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    out = await telnet.send_command(host, port, "display lldp neighbor brief")
    return [TextContent(type="text", text=out if out.strip() else "未发现 LLDP 邻居（可能未启用 LLDP 或无可发现的邻居）。")]


@handler("get_arp_table")
async def h_get_arp_table(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    out = await telnet.send_command(host, port, "display arp all")
    return [TextContent(type="text", text=out if out.strip() else "ARP 表为空。")]


@handler("get_mac_table")
async def h_get_mac_table(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    out = await telnet.send_command(host, port, "display mac-address")
    return [TextContent(type="text", text=out if out.strip() else "MAC 地址表为空。")]


@handler("configure_interface_ip")
async def h_configure_interface_ip(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    intf = args["interface"]
    ip_addr, mask = _parse_ip_mask(args["ip"])

    cmds = ["system-view", f"interface {intf}", f"ip address {ip_addr} {mask}", "quit", "return"]
    results = []
    for cmd in cmds:
        out = await telnet.send_command(host, port, cmd)
        results.append(f"> {cmd}\n{out}")
    return [TextContent(type="text", text=f"已配置 {args['device']} 接口 {intf} IP={ip_addr}/{mask}\n\n" + "\n".join(results))]


@handler("configure_vlan")
async def h_configure_vlan(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    vlan_id = args["vlan_id"]
    action = args["action"]

    if action == "create":
        cmds = ["system-view", f"vlan {vlan_id}", f"description VLAN{vlan_id}", "quit", "return"]
    else:
        cmds = ["system-view", f"undo vlan {vlan_id}", "return"]

    results = []
    for cmd in cmds:
        out = await telnet.send_command(host, port, cmd)
        results.append(f"> {cmd}\n{out}")
    action_cn = "创建" if action == "create" else "删除"
    return [TextContent(type="text", text=f"已在 {args['device']} 上{action_cn} VLAN {vlan_id}。\n\n" + "\n".join(results))]


@handler("configure_static_route")
async def h_configure_static_route(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    dest = args["destination"]
    mask = _parse_route_mask(args["mask"])
    next_hop = args["next_hop"]
    action = args["action"]

    prefix = "ip route-static"
    route_cmd = f"{prefix} {dest} {mask} {next_hop}" if action == "add" else f"undo {prefix} {dest} {mask} {next_hop}"

    cmds = ["system-view", route_cmd, "return"]
    results = []
    for cmd in cmds:
        out = await telnet.send_command(host, port, cmd)
        results.append(f"> {cmd}\n{out}")
    action_cn = "添加" if action == "add" else "删除"
    return [TextContent(type="text", text=f"已在 {args['device']} 上{action_cn}静态路由：{dest}/{mask} → {next_hop}。\n\n" + "\n".join(results))]


@handler("ping_test")
async def h_ping_test(args: dict) -> list[TextContent]:
    host, port = _resolve(args["device"])
    target = args["target"]
    count = args.get("count", 5)
    out = await telnet.send_command(host, port, f"ping -c {count} {target}")
    return [TextContent(type="text", text=out if out.strip() else f"Ping {target} 无响应。")]
