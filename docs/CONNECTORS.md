# Connector setup

The starter kit deliberately does **not** auto-configure data-source
connectors at install time. Instead, each connector has a guided
setup recipe that:

1. writes the right `extensions.<name>` block into your Goose
   `config.yaml` (`~/.config/goose/config.yaml` on macOS/Linux,
   `%APPDATA%\Block\goose\config\config.yaml` on Windows),
2. walks you through enabling the extension in Goose Desktop's
   Extensions UI, and
3. helps you trigger the vendor's OAuth flow on first use.

This works much better than trying to do everything from a one-shot
shell installer — the recipe runs *inside* Goose, so the agent itself
can read files, edit YAML, and react to whatever state your install
is in.

## Available

| Connector | Recipe | Notes |
|---|---|---|
| Notion | `goose recipe run set-up-notion` | Verified end-to-end: OAuth fires on first tool call; revoke at <https://www.notion.so/profile/integrations>. |

## Tracked but not yet shipped

We've validated that the **OAuth-on-first-use** pattern works for these
remote MCP servers, but not all of them work out-of-the-box for users
the kit is designed for. Status notes:

- **Google Drive** (`https://drivemcp.googleapis.com/mcp/v1`). The
  endpoint responds and the schema is right, but we haven't yet
  confirmed the OAuth flow actually triggers cleanly via Goose. A
  `set-up-gdrive` recipe ships once we have a working repro.
- **Slack** (`https://mcp.slack.com/mcp`). Requires a Slack workspace
  admin to install the official Slack MCP app first; without that, the
  initial MCP handshake gets a 401 and there's no graceful path to
  user-driven OAuth. We're not shipping a Slack recipe until that
  story is cleaner — workspace-admin pre-setup is a footgun for
  research-team users.
- **GitHub** (`https://api.githubcopilot.com/mcp/`). GitHub allowlists
  the OAuth dynamic-client-registration step to a fixed set of IDEs
  (VS Code, Visual Studio, JetBrains, Eclipse, Xcode, Cursor); Goose
  isn't on that list. Engineers who actually need GitHub access from
  Goose can wire it themselves with a personal access token via
  Goose's Add Extension UI; we're not bundling it.

## Adding any other MCP server

For anything not in the table above (filesystem MCP, Square,
Atlassian, custom servers, …), use:

```
goose recipe run add-an-mcp-server
```

That recipe is a generic walkthrough for adding any MCP-speaking
data source — local stdio or remote HTTP — and explains the schema,
auth, and verification steps as it goes.

You can also edit Goose's `config.yaml` directly (`~/.config/goose/config.yaml`
on macOS/Linux, `%APPDATA%\Block\goose\config\config.yaml` on Windows):

```yaml
extensions:
  filesystem:
    enabled: true
    type: stdio
    name: filesystem
    description: "Read files from a specific local path."
    bundled: false
    timeout: 300
    available_tools: []
    cmd: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/share"]
    env_keys: []
    envs: {}
```

The kit's installer does not own any keys in your `config.yaml`, so
nothing here will be touched on `update`.
