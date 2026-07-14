# eNSP MCP Server

华为 eNSP 网络模拟平台的 MCP (Model Context Protocol) 服务器，允许 AI 助手通过标准化的 MCP 接口自动化管理和配置 eNSP 虚拟网络设备。

## 功能

- **设备发现**: 自动扫描并发现运行中的 eNSP 虚拟设备
- **命令执行**: 通过 Telnet 在设备上执行 CLI 命令
- **状态查询**: 获取版本、配置、接口、ARP/MAC 表、LLDP 邻居等信息
- **网络配置**: 配置接口 IP、VLAN、静态路由
- **网络诊断**: Ping 测试

## 安装

```bash
pip install .
```

## 使用

在 Claude Code 或其他 MCP 客户端中添加配置：

```json
{
  "mcpServers": {
    "ensp": {
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "ensp_mcp"],
      "env": {
        "ENSP_CONSOLE_HOST": "127.0.0.1",
        "ENSP_CONSOLE_TIMEOUT": "15"
      }
    }
  }
}
```

## 前置条件

- 华为 eNSP 模拟器已安装并启动
- Python >= 3.10

## 工具列表

| 类别 | 工具 | 说明 |
|------|------|------|
| 设备发现 | `scan_devices` | 扫描本地端口，发现运行中的设备 |
| | `list_devices` | 列出已注册的设备 |
| | `get_device_info` | 获取设备详细信息 |
| 设备状态 | `get_device_status` | 检查设备在线状态 |
| | `connect_device` | 建立 Telnet 连接 |
| | `disconnect_device` | 断开 Telnet 连接 |
| 命令执行 | `send_command` | 执行单条 CLI 命令 |
| | `send_commands` | 批量执行 CLI 命令 |
| 信息查询 | `get_version` | 获取设备版本 |
| | `get_running_config` | 获取运行配置 |
| | `get_startup_config` | 获取启动配置 |
| | `get_interface_brief` | 获取接口摘要 |
| | `get_interface_detail` | 获取接口详情 |
| | `get_lldp_neighbors` | 获取 LLDP 邻居 |
| | `get_arp_table` | 获取 ARP 表 |
| | `get_mac_table` | 获取 MAC 地址表 |
| 网络配置 | `configure_interface_ip` | 配置接口 IP |
| | `configure_vlan` | 创建/删除 VLAN |
| | `configure_static_route` | 配置静态路由 |
| 诊断 | `ping_test` | Ping 测试 |
