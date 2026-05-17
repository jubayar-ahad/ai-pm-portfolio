# Model Context Protocol (MCP)

## What is MCP?

Model Context Protocol enables Cursor to connect to external tools and data sources. Rather than repeatedly describing project structure, you can integrate directly with your existing tools.

MCP servers can be written in any language capable of printing to `stdout` or serving an HTTP endpoint, including Python, JavaScript, and Go.

## Why Use MCP?

The protocol connects Cursor to external systems and data, allowing developers to leverage their existing toolsets without manual explanations of project context.

## Transport Methods

Cursor supports three transport approaches:

**stdio** operates locally with manual authentication, managed by Cursor for single users via shell commands.

**SSE** and **Streamable HTTP** both support local or remote deployment as servers, accommodating multiple users with OAuth authentication.

## Supported Features

Cursor implements tools, prompts, resources, roots, elicitation, and the MCP Apps extension, which enables interactive UI returns from MCP tools with progressive enhancement fallback.

## Installation Options

Official plugins install via the Cursor Marketplace with one-click setup. Community servers are available through cursor.directory.

Custom servers configure through `mcp.json` files, supporting environment variables, OAuth credentials, and config interpolation using `${env:NAME}`, `${workspaceFolder}`, and similar variables.

## Security Practices

When installing servers, verify sources, review permissions, use restricted API keys, and audit code for critical integrations. MCP servers execute code on your behalf and access external services.
