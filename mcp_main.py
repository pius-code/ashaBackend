# use this if you wanna run the mcp standalone without the backend, otherwise use main.py to run the whole backend with mcp included # noqa

from agent.mcp_tools.tools import * # noqa
from agent.core.fastmcp import mcp


def main():
    print("Hello from AHSA MCP!")
    mcp.run()


if __name__ == "__main__":
    main()
