"""包入口 — 支持 `python -m ensp_mcp` 启动。"""

import asyncio
from .server import run


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
