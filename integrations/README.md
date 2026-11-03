# Finance Calendar plugin and skill

A read-only economic-calendar integration for Codex and Claude Code. The plugin bundles an authenticated hosted MCP connection and a portable `financecalendar` Agent Skill. It queries the hosted feed; installing it does not create a local copy of the database. Create and verify a Finance Calendar account, then create an API key. Every request requires credentials.

Set `FC_API_KEY` securely in your client environment. The manifests use an environment-expanded `X-API-Key` header. This setup requires a client that supports both custom headers and environment expansion; do not assume every plugin installer supports them. If unsupported, use the [local stdio setup](https://www.financecalendar.com/api/mcp/#install-the-mcp-server-from-source). Never replace the placeholder with a real key in committed files or put a key in a URL.

The skill covers current release schedules, source attribution, unknown clocks/periods, numerical vintages, publication bundles and complete exports. It uses discovered countries/series instead of a fixed coverage promise.

## Downloads

Use the current repository source and authenticated configuration below. The [older 0.1.0 beta ZIPs](https://github.com/awarenessdays/financecalendar-api/releases/tag/plugins-0.1.0) predate required API keys and need their connection settings updated before use. The plugin ZIP contains the manifests at its root; the skill ZIP contains a `financecalendar/` folder with `SKILL.md` and its supporting files. Upload, environment expansion and custom-header availability depend on the client and workspace settings.

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

Configure the hosted URL `https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp` with an `X-API-Key` header read from `FC_API_KEY`. A URL-only connection will receive HTTP 401. Use local stdio if your client cannot attach the required header.

Invoke `$financecalendar`, or ask a financial-event question that matches the skill. Installing the skill alone does not configure an MCP connection. Existing unrelated settings should be merged, not replaced.

## ChatGPT and Claude chat

Use [the hosted connector setup](https://www.financecalendar.com/api/mcp/). Public directory submission and account/workspace-level installation checks are separate release steps. Workspace policies can control availability.

## Formats and validation

`plugin.json` and `mcp.json` use the portable Agent Plugins format. `.claude-plugin/plugin.json` and `.mcp.json` provide the Claude Code format. They share one skill and one hosted endpoint, with explicit `streamable-http` versus `http` transport spelling for the two formats. There are no hooks, embedded credentials or local server commands. Hosted transport validates the caller key for all protocol requests and forwards it for data calls; linked keys share the account allowance.

Sources: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), [Claude Code manifest reference](https://code.claude.com/docs/en/plugins-reference), [Claude Code marketplaces](https://code.claude.com/docs/en/plugin-marketplaces). Checked 22 October 2026. Validation and real transport tests do not by themselves prove a directory listing or installation in every account surface.

## Working application example

The [economic calendar dashboard starter](examples/economic-calendar-dashboard/README.md) includes a Node backend, responsive browser calendar, labelled demo mode and a shared 30-minute cache. Your API key stays on the server; browser filters work locally. Follow the README and its coding-assistant prompt to adapt the working app.
