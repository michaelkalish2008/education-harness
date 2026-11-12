# Education Harness in ChatGPT Work

ChatGPT is an optional client for the same local harness. Both clients use
`~/learning` by default. Set `EH_WORKSPACE` to a separate absolute path before
starting the tunnel client if you want a fresh workspace for testing.

The ChatGPT connection supports starting and resuming goals, writing plans,
recording notes, searching memory, revealing worked examples, bookmarking, and
profile review. It exposes a subset of the local tools. Tool inputs and results
used in conversation are sent to ChatGPT.

## Connect privately

1. Create a tunnel in your OpenAI Platform organization and install the official
   `tunnel-client` on your Mac. Follow the
   [Secure MCP Tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
   to supply a restricted runtime key through `CONTROL_PLANE_API_KEY`. Keep
   that key out of chat and repository files.
2. With the harness installed in its existing virtual environment, run:

   ```bash
   cd ~/Documents/education-harness
   tunnel-client init \
     --sample sample_mcp_stdio_local \
     --profile education-harness \
     --tunnel-id YOUR_TUNNEL_ID \
     --mcp-command "$PWD/mcp/.venv/bin/eh-mcp --chatgpt"
   tunnel-client doctor --profile education-harness --explain
   tunnel-client run --profile education-harness
   ```

3. On [ChatGPT Plugins](https://chatgpt.com/plugins), choose **Add custom MCP
   server → Tunnel**, select the tunnel, and create and install a personal
   plugin called **Education Harness**.
4. In a Work chat, mention **Education Harness** and ask “Where did I leave
   off?” Check that it calls `where_am_i` before responding. Keep the Mac
   awake and the tunnel client running while using the plugin.
