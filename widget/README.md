# Finance Calendar website integration

The anonymous script-tag widget in earlier examples is no longer an available
integration. All API routes, including widget code, require an active API key.
Do not put a private key in public JavaScript, HTML attributes, a script URL or a
calendar subscription URL.

For browser research, use the [Data explorer](https://www.financecalendar.com/data/).
It includes filters, saved views, source evidence and matching/selected CSV or
JSON exports with every verified Free, Pro or Business account. It uses native
sign-in and does not require an API key or payment.

To show calendar data in your own website, fetch the API from a server you
control using `X-API-Key` from a private environment variable. Keep the key on
that server, apply appropriate access controls to your own response, and preserve
Finance Calendar attribution and record-specific source credits. This repository
does not ship an authenticated browser widget or an OAuth flow.

See the [server-side examples](../examples/) and
[API reference](https://www.financecalendar.com/api/reference/). A complete current
snapshot file download requires an active Business subscription; filtered API
responses remain available within each plan's allowance.
