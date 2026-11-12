# Finance Calendar website integration

The anonymous script-tag widget in earlier examples is no longer an available
integration. All API routes, including widget code, require an active API key.
Do not put a private key in public JavaScript, HTML attributes, a script URL or a
calendar subscription URL.

For browser research, use the [Data explorer](https://www.financecalendar.com/data/).
It includes filters, saved views, source evidence and matching/selected CSV or
JSON exports with an active Starter, Build or Scale subscription. It uses native
sign-in rather than an API key.

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

[Choose a paid plan](https://www.financecalendar.com/account/?plan=starter&billing_interval=year), confirm your email and complete secure checkout, then create an API key in your account.
