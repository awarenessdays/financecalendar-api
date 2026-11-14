# Finance Calendar plugin and skill

A read-only economic-calendar integration for Claude, ChatGPT and compatible MCP clients. Link your existing Finance Calendar account to ask about economic releases, central-bank decisions, market holidays and covered crypto events, with timing precision and source evidence. The plugin bundles a hosted OAuth MCP connection and the portable `financecalendar` Agent Skill; it does not download the database or run a local server.

Hosted MCP is included with eligible paid Finance Calendar access or an applicable retained grant. Linked assistant requests share that account's existing API allowance with REST, SDKs and other connections. One question can require several data calls. Installation does not create a subscription or change your plan; a Claude or ChatGPT subscription is separate from Finance Calendar access. View your actual access and usage in your Finance Calendar account.

## Release status

Version 0.2.0 is the OAuth release candidate. Package validation does not establish that OAuth is deployed, that an account-level installation has passed, or that a platform directory has approved it. Announce this release only after the live OAuth and native-client checks are complete. The earlier [0.1.3 release](https://github.com/awarenessdays/financecalendar-api/releases/tag/plugins-0.1.3) uses API-key headers and remains a separate installation path for compatible clients.

## Link your account

1. Add the plugin or the hosted server using your client's supported controls.
2. Choose **Connect** or **Authenticate** when the client starts its OAuth flow.
3. Sign in on `www.financecalendar.com`, review the client and the read-only `calendar:read` permission, and approve the connection.
4. Return to your assistant and ask a calendar question.

Use only the Finance Calendar sign-in and consent page. Never paste an account password, API key, access token or refresh token into a conversation. This package has no embedded credentials or custom API-key headers. It uses public-client dynamic registration and PKCE; it does not need a client secret in your manifest.

OAuth grants calendar data access only. It does not permit publishing, changing billing, creating API keys, placing trades or moving money. Disconnecting or revoking the connection removes its future access; it does not cancel your Finance Calendar subscription. If account access changes or a credential expires, the next request must pass the same current account checks. Existing paid and retained grants keep their applicable terms.

## Claude Code

From Claude Code, add the Finance Calendar repository marketplace and install the plugin:

```text
/plugin marketplace add awarenessdays/financecalendar-api
/plugin install financecalendar@financecalendar
```

Use Claude Code's MCP authentication controls to authenticate the `financecalendar` server when prompted. The skill is available as `/financecalendar:financecalendar`. For a local checkout, `claude --plugin-dir /absolute/path/financecalendar-api/integrations` loads this package.

Example: “What are the next CPI releases for India and South Korea? Show the official sources and only verified times.”

This repository marketplace is maintained by Finance Calendar. It does not imply an official Anthropic directory listing.

## Claude chat and Cowork

When your Claude account and workspace allow custom connectors, add this hosted HTTPS server and follow its OAuth account-linking flow:

```text
https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp
```

Claude directory publication requires a separate connector submission. A plugin bundle that references the hosted server is submitted separately from that connector. Availability depends on the current Claude plan, client and workspace controls.

## ChatGPT

This package includes the portable plugin manifest and OAuth configuration for OpenAI hosts. The same HTTPS MCP server and Finance Calendar account can support a ChatGPT connection; a Claude installation does not automatically install anything in ChatGPT.

For testing, use the current ChatGPT developer controls to add the server with OAuth. For public distribution, submit the plugin through OpenAI's separate plugin review process. A repository package or successful local test does not establish ChatGPT directory availability.

The ChatGPT experience serves the capabilities already included with your connected account. It does not sell subscriptions or initiate plan changes in chat. Account-linking, data use and the current entitlement checks are the same underlying service used by the other supported clients.

## Codex and other clients

The portable manifest declares a Streamable HTTP connection with OAuth dynamic client registration and `calendar:read`. Use your client's supported plugin and authentication controls; clients differ in manifest and OAuth support. For a skill-only installation, copy `integrations/skills/financecalendar` into the project's `.agents/skills/` directory and retain its `references/` folder, then configure an MCP connection separately. Merge configuration with existing settings.

Clients that already support private API-key headers can continue to use the hosted endpoint with their own `X-API-Key` or `Authorization: Bearer` credential. Set it in the client's private secret configuration, not in this OAuth manifest, a URL or generated source. The [MCP reference](https://www.financecalendar.com/api/mcp/) describes the separate local stdio/API-key setup. Free Developer's permitted schedule REST routes do not include hosted MCP.

## Data and usage

The skill preserves recorded timing, null values, publication periods, numerical vintages and source attribution. It discovers actual countries and series instead of promising universal coverage. Tool discovery provides current schemas; data responses preserve pagination and truncation information.

Data tool calls use the connected account's allowance. Initialization, ping and tool discovery authenticate without consuming data quota. Respect rate-limit reset information; repeated retries do not increase access. Current plan terms, retained grants and effective account allowances remain authoritative. Package copy does not override them.

## Privacy and support

Finance Calendar receives the tool arguments needed to answer the requested calendar query and the credential identifying the authorized connection. OAuth authorization uses your existing Finance Calendar identity and consent; tokens must remain in the client's private credential storage. The connector does not need your conversation history or unrelated files. Response source credits and applicable publisher rights remain relevant.

Before release, verify that the live [privacy notice](https://www.financecalendar.com/privacy-policy/) describes OAuth account identifiers, token hashes, grants, revocation and actual retention practices. Privacy wording must match the implemented service; this package is not a promise of unverified retention periods. Support: `alex@financecalendar.com`.

## Packaging and validation

`plugin.json` and `mcp.json` use the portable Agent Plugins format. `.claude-plugin/plugin.json` and `.mcp.json` provide the Claude Code format. The transports are spelled `streamable-http` and `http` respectively. There are no hooks, embedded credentials, static authentication headers or local server commands in this package.

Build the allowlisted plugin and skill archives:

```sh
python3 integrations/build.py --out /tmp/financecalendar-plugin-build
claude plugin validate ./integrations
```

The ZIPs contain manifests at the plugin root and a separate `financecalendar/` skill directory. Checksums accompany the build. Do not describe a prepared ZIP as a published release until it is uploaded and the target platform checks pass.

Sources checked 14 November 2026: [OpenAI OAuth authentication](https://developers.openai.com/plugins/build/auth), [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), [OpenAI submission](https://developers.openai.com/plugins/deploy/submission), [Claude connector authentication](https://claude.com/docs/connectors/building/authentication), [Claude plugin submission](https://claude.com/docs/plugins/submit).
