"""image-ocr — OCR an image with rapidocr (cross-platform) or macOS Vision.

This package implements Phase P2 of the agent-gateway MCP integration spec
(see ``docs/superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md``
§8.1).  The public entry point is :func:`image_ocr.cli.run_ocr`, which is
invoked by ``image-ocr/mcp_tools.py`` over MCP.
"""
from __future__ import annotations

__version__ = "0.1.0"
