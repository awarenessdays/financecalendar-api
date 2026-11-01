# Finance Calendar plugin and skill

A read-only economic-calendar integration for Codex and Claude Code. The plugin bundles the public hosted MCP connection and a portable `financecalendar` Agent Skill. It queries the hosted feed; installing it does not create a local copy of the database. No API key, package runtime or local server is required for this hosted setup.

The skill covers current release schedules, source attribution, unknown clocks/periods, numerical vintages, publication bundles and complete exports. It uses discovered countries/series instead of a fixed coverage promise.

## Downloads

[Plugin and skill beta ZIPs with SHA-256 checksums](https://github.com/awarenessdays/financecalendar-api/releases/tag/plugins-0.1.0) are available for clients that accept package uploads. The plugin ZIP contains the manifests at its root; the skill ZIP contains a `financecalendar/` folder with `SKILL.md` and its supporting files. Use the repository marketplace commands below for Codex or Claude Code. Upload and custom-connector availability depends on the client and workspace settings.

## Claude Code

From Claude Code:

```text
/plugin marketplace add awarenessdays/financecalendar-api
/plugin install financecalendar@financecalendar
```

The plugin's skill is available as `/financecalendar:financecalendar`. Ask, for example, “What are the next CPI releases for India and South Korea? Show the official sources and only verified times.”

For a local checkout, `claude --plugin-dir /absolute/path/financecalendar-api/integrations` loads the same package. The marketplace is maintained by Finance Calendar; installation is separate from an official Anthropic directory listing.

## Codex

Register the public repository marketplace, then add its plugin with the supported plugin controls. The repository includes `.agents/plugins/marketplace.json` pointing to `./integrations`. This is a repository distribution, not an approved public-directory listing.

```sh
codex plugin marketplace add awarenessdays/financecalendar-api
codex plugin add financecalendar@financecalendar
```

For skill-only use, copy `integrations/skills/financecalendar` into your chosen project's `.agents/skills/` directory, retaining its `references/` folder. Connect the hosted server with your MCP settings or:

```sh
codex mcp add financecalendar --url https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp
```

Invoke `$financecalendar`, or ask a financial-event question that matches the skill. Installing the skill alone does not configure an MCP connection. Existing unrelated settings should be merged, not replaced.

## ChatGPT and Claude chat

Use [the hosted connector setup](https://www.financecalendar.com/api/mcp/). Public directory submission and account/workspace-level installation checks are separate release steps. Workspace policies can control availability.

## Formats and validation

`plugin.json` and `mcp.json` use the portable Agent Plugins format. `.claude-plugin/plugin.json` and `.mcp.json` provide the Claude Code format. They share one skill and one hosted endpoint, with explicit `streamable-http` versus `http` transport spelling for the two formats. There are no hooks, embedded credentials or local server commands.

Sources: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), [Claude Code manifest reference](https://code.claude.com/docs/en/plugins-reference), [Claude Code marketplaces](https://code.claude.com/docs/en/plugin-marketplaces). Checked 22 October 2026. Validation and real transport tests do not by themselves prove a directory listing or installation in every account surface.
