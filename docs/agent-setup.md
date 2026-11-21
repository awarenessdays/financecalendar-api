# Build a US CPI and FOMC watchlist with an AI agent

Start with the [public US CPI and FOMC sample](https://www.financecalendar.com/api/sample/) to read a recorded inflation result and upcoming schedule examples. Then prepare an owner-approved setup for live paid access. Starter supports the numerical data and tools used in this workflow; use [live pricing](https://www.financecalendar.com/pricing/) and the [machine-readable offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer) for the current charge and allowances.

## Read the public example before connecting

The sample guide renders the selected records in HTML. Read the same fixed response without an account or API key:

```sh
curl --fail-with-body -sS \
  'https://www.financecalendar.com/wp-json/fc/v1/sample'
```

Use `sample.captured_at` as the example's capture time. Read the `completed_release`, `scheduled_release` and `scheduled_decision` records for a published US CPI result, a scheduled CPI release and a scheduled FOMC decision. For a short briefing:

- Report the reference period and `release_at_utc`, or `time_et` together with `release_tz`.
- Report the recorded `actual` and its `unit` when present. Cite `actual_evidence.edition_url` for the published CPI result.
- Cite each record's `source_url` for official schedules. Preserve `null` for future or unrecorded results.
- Label the briefing as a recorded example at its capture time. It is not a live-data or uptime check; an elapsed scheduled time does not prove a result was captured.

The sample is limited to at most three publisher-selected records. It has no configurable filters, dates or pagination. Use the canonical URL above without filter parameters. If an assistant cannot open JSON, it can read the [same sample as HTML](https://www.financecalendar.com/api/sample/).

### Read the sample through a connected hosted MCP client

If the assistant already has an authenticated hosted Finance Calendar connection but cannot fetch the public HTML or JSON, call `feed_status`. Its `structuredContent.recorded_public_sample` contains the same fixed sample response as the public JSON endpoint. Read its `sample.captured_at`, event roles and official source fields using the briefing rules above.

The recorded sample is distinct from `feed_status`'s live service or snapshot-health fields. A successful status call does not turn the captured examples into live results. This fallback does not provide anonymous hosted access, expand a plan, or create an owner setup; the existing hosted authentication and access requirements continue to apply.

## Use browser preparation when the agent cannot send a POST

Open the [browser preparation page for ChatGPT](https://www.financecalendar.com/api/sample/?setup_client=chatgpt#prepare-owner-setup). A person or browser-capable agent can review the workflow and select **Prepare setup link**. The button sends a same-origin POST to the existing setup endpoint and, after an HTTP 201 response, displays the genuine server-returned `owner_url`.

Opening the page with GET only renders the form. It does not create a setup, sign in, link an account or start checkout. The preparation page link is not the returned `owner_url`. A text-only assistant can offer that link, but must not claim to have created a setup unless the POST actually succeeds. No existing paid account or connector is needed for this preparation step; the owner still completes the account and payment approvals below.

This is useful when ChatGPT can browse documentation but its code tool cannot send API requests. OpenAI documents that the [Python data-analysis environment cannot make external web requests or API calls](https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt). A hostname-resolution error there does not establish that Finance Calendar's public DNS is broken. Use browser preparation or a network-enabled agent or CLI rather than retrying from that restricted environment.

The browser keeps the private status token out of chat. Do not copy it into the conversation to let a text-only assistant poll. Continue using the owner link and the account's connection instructions, or resume through an authorized tool connection once available.

## Prepare live access without an API key

The current setup recipe preserves a next-US-CPI query. It does not create an account, make a payment or return a production credential. Create the setup from trusted agent or CLI tool state:

```sh
curl --fail-with-body -sS \
  'https://www.financecalendar.com/wp-json/fc-handoff/v1/setup' \
  -H 'Content-Type: application/json' \
  --data '{"recipe":"next-us-cpi","client":"claude","plan":"starter","billing_interval":"year","timezone":"America/New_York"}'
```

Supported clients are `claude`, `chatgpt`, `cursor`, `rest` and `cli`. The only current recipe is `next-us-cpi`. Use `starter`, `build` or `scale` with a billing interval offered for that plan; Starter bills monthly or annually. The optional IANA `timezone` defaults to `America/New_York`. The endpoint rejects extra fields such as prompts, email addresses, prices and redirects. See the [live OpenAPI contract](https://www.financecalendar.com/wp-json/fc/v1/openapi).

The response provides `owner_url`, `status_url`, `status_token`, `poll_after_seconds` and `expires_at`. Share **only `owner_url`** with the owner. Keep the polling token in private tool state, out of chat, URLs and logs. The setup expires after two hours; prepare another setup if it expires.

## What the owner approves

The owner opens their setup link, signs in or creates and verifies a Finance Calendar account, then selects **Link this setup to my account** to share readiness with the agent. If payment is needed, the owner selects **Continue to Stripe**, reviews the selected plan and charge, and completes payment themselves. An owner with an active matching subscription can resume after linking the account.

The owner can reopen the original setup link until it expires, including in the tab opened by email confirmation. Returning from Stripe alone does not establish readiness: Finance Calendar checks the verified subscription and selected billing interval.

## Poll readiness and resume

Send the private token to the returned `status_url` in the `X-FC-Handoff-Token` header. Wait at least `poll_after_seconds` between requests and stop at `expires_at`.

- `owner_required`: share the owner link so the owner can sign in and approve linking.
- `payment_pending`: wait for the owner to review checkout and for subscription confirmation.
- `plan_mismatch` or `billing_review`: ask the owner to review the plan or billing shown in their account.
- `ready`: follow the returned `resume` instructions to connect the account and run the preserved query.
- HTTP 404: the setup is expired or invalid; prepare a new setup if needed.

Readiness returns no API key, OAuth token, email or payment identifier. For hosted MCP, the owner still completes [supported OAuth account linking](https://www.financecalendar.com/api/mcp/), or configures their own API-key header in a compatible client. For REST or CLI, the owner configures the account API key privately. Do not ask them to paste a credential into chat.

After the account is connected, the initial MCP calls can be:

```json
{"tool":"next_event","arguments":{"series":"us-cpi","tz":"America/New_York"}}
{"tool":"next_event","arguments":{"series":"fomc","tz":"America/New_York"}}
```

The equivalent REST requests are:

```sh
curl --fail-with-body -sS \
  'https://www.financecalendar.com/wp-json/fc/v1/next?series=us-cpi&tz=America/New_York' \
  -H "X-API-Key: $FC_API_KEY"
curl --fail-with-body -sS \
  'https://www.financecalendar.com/wp-json/fc/v1/next?series=fomc&tz=America/New_York' \
  -H "X-API-Key: $FC_API_KEY"
```

The preserved setup query is CPI; the second request adds FOMC to the watchlist after authentication. These are paid routes and count against the connected account's allowance. Ongoing Free Developer supports bounded schedule JSON through `/calendar` and `/today`; it does not include `/next`, numerical results, history or hosted MCP. See the [current offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer) for scope and limits.

In a test or handoff report, distinguish records actually read, a setup actually created, owner steps awaiting approval, and authenticated queries actually executed. Preparing the examples alone does not complete those actions.
