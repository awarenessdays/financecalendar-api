# Finance Calendar website integration

Build a calendar into your website by fetching Finance Calendar data on your
server with a private API key. Production data requests need the key; public
OpenAPI, current-offer and fixed-sample inspection routes do not. Keep credentials
out of browser JavaScript, HTML attributes, script URLs and calendar subscription URLs.

For browser research, use the [Data explorer](https://www.financecalendar.com/data/).
It includes filters, saved views, source evidence and matching/selected CSV or
JSON exports with an active Starter, Build or Scale subscription. It uses native
sign-in rather than an API key. Free Developer does not include these browser tools.

To show calendar data in your own website, fetch the API from a server you
control using `X-API-Key` from a private environment variable. Keep the key on
that server, apply appropriate access controls to your own response, and preserve
Finance Calendar attribution and record-specific source credits. This repository
does not ship an authenticated browser widget or an OAuth flow.

See the [server-side examples](../examples/) and
[API reference](https://www.financecalendar.com/api/reference/). A complete current
snapshot file download requires an active Scale subscription; filtered API
responses remain available within each plan's allowance.

[Paid API plans](https://www.financecalendar.com/pricing/) start at **US$9.99/year** for Starter (**1,000 requests/UTC day and 25,000/UTC calendar month**). Build is **US$9.99/month or US$95.90/year** for **100,000/day**. Scale is **US$29/month or US$278.40/year** for **1,000,000/day** and the complete current dataset download. [Inspect the public sample](https://www.financecalendar.com/api/sample/) before choosing a plan.

[Free Developer](https://www.financecalendar.com/account/?free=1) is ongoing schedule JSON access: **100 successful responses per UTC calendar month, at most 10 per UTC day**, one verified account and one active key, no card or automatic charge. Use `GET /calendar` or `/today` for economic-release and central-bank schedules from UTC today through the following six days, with up to 20 records and no pagination. Country (up to three codes) and impact filters are supported; `from` and `to` may narrow, but cannot extend, the seven-date UTC window. Free `/today` is the current UTC date’s schedule, without market-status or holiday payloads. Free responses omit consensus, actual/prior figures and numerical evidence; Starter adds these recorded fields, wider dates/history, formats, hosted MCP and browser tools.
