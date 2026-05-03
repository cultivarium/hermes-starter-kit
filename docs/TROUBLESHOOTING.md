# Troubleshooting

## Installer

**`Goose missing and --non-interactive set`**

The installer won't auto-install Goose without a prompt. Either drop
`--non-interactive`, or install Goose first:

```bash
curl -fsSL https://github.com/aaif-goose/goose/releases/download/stable/download_cli.sh \
  | CONFIGURE=false bash
```

**`Installed Goose (1.x.y) is older than recommended`**

Advisory only — the installer continues. Newer skills or recipes may
not work against older Goose; upgrade if anything misbehaves.

## Connectors

**Notion stanza is in `config.yaml` but Goose Desktop doesn't show it
in the Extensions panel**

Quit Goose Desktop completely and reopen it. Goose only loads
extensions from `config.yaml` at startup; a hot edit isn't picked up.

**OAuth flow doesn't open a browser tab**

Some Goose CLI versions on macOS don't reliably trigger browser
launches from the terminal. Use Goose Desktop instead — invoke a
notion tool from the chat panel and the auth tab will open as
expected.

**Tool call fails with `Auth required` or `401`**

The OAuth flow hasn't completed yet. Either:

1. The connector was added to `config.yaml` but the user hasn't
   exercised a tool from that connector yet (auth fires lazily on
   first use). Ask the agent to do something the connector covers,
   e.g. *"List the most recently edited pages in my Notion
   workspace."*
2. The vendor's MCP server requires a workspace-admin pre-installation
   step (this is the case for Slack and GitHub today — see
   `docs/CONNECTORS.md` for which connectors that affects).

## Skills

**A skill's instructions don't match my workflow**

Edit the skill's `SKILL.md` directly. The next install run will detect
your edit via sha256 and leave it alone. To opt back into the kit's
version, delete the file and re-run the installer.

**Skills aren't being loaded by Goose**

Confirm the path: skills must be at `~/.config/goose/skills/<name>/SKILL.md`
(macOS / Linux) or `%APPDATA%\Block\goose\config\skills\<name>\SKILL.md`
(Windows). Restart your Goose session after editing — Goose loads
skills at session start.

## Memory

**The agent doesn't remember anything between sessions**

Confirm the memory extension is enabled in Goose Desktop's Extensions
panel (or in Goose's `config.yaml` — `~/.config/goose/config.yaml` on
macOS/Linux, `%APPDATA%\Block\goose\config\config.yaml` on Windows —
under `extensions.memory.enabled: true`). The kit no longer enforces
memory-on at install time — Goose's per-version default applies.

If memory is enabled but the agent still seems amnesiac, try asking it
explicitly: "What do you have in memory about my setup?" — Goose's
memory extension is keyed by the topic the agent decides to write
under, so a clean session may simply not have surfaced an old note
yet.

## CLI session suspends with `EINTR` or `suspended (tty input/output)` (macOS)

Known Goose CLI bug on macOS interactive sessions, especially when an
stdio MCP extension is enabled. Workarounds:

- Use Goose Desktop instead of `goose session`.
- Use single-shot mode for testing: `goose run --recipe <name> --max-turns 3`.

Tracking issue: search `aaif-goose/goose` for `EINTR` /
`suspended (tty)` reports.
