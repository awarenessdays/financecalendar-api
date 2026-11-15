# Finance Calendar for Claude

Find economic releases, central-bank decisions, exchange holidays and covered
crypto events through your linked Finance Calendar account. Read recorded timing,
available figures and source evidence in the same conversation.

Hosted connector access requires an existing verified Finance Calendar account
with eligible paid access or an applicable retained grant. Data calls share that
account's existing API allowance. Installing this plugin does not create a
subscription or change your account access.

## Connect your account

1. Add the Finance Calendar plugin using Claude's supported plugin controls.
2. Choose **Connect** or **Authenticate** when Claude requests account linking.
3. Sign in on **www.financecalendar.com**, review the client and permissions,
   then approve the connection.
4. Return to Claude and ask a calendar question.

The hosted server is
`https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp`.
OAuth uses read-only `calendar:read`; optional `offline_access` lets the client
renew the connection without a sign-in for every conversation. Manage or revoke
linked assistants in your Finance Calendar account. Revoking a connection does
not cancel your subscription or affect unrelated connections.

## Example questions

- Which UK economic releases are scheduled this week? Include the original sources.
- When is the next supported CPI release for India? Is its exact time verified?
- What are the upcoming London Stock Exchange holidays?

Coverage follows supported sources and their announced horizons. Unknown timing,
missing values, estimated dates and stale data remain explicit. One question may
require several data calls; connection setup and tool discovery do not consume
data quota. Existing account permissions and effective limits remain authoritative.

## Privacy and support

Sign-in and consent happen on Finance Calendar; credentials are handled by the
client's private OAuth connection. Finance Calendar receives the account/client
references, granted permission and the query arguments needed to provide the
requested data. Read the [privacy policy](https://www.financecalendar.com/privacy-policy/)
for collection, retention and revocation information.

[Connection documentation](https://www.financecalendar.com/api/mcp/) ·
[API terms](https://www.financecalendar.com/api/terms/) ·
Support: alex@financecalendar.com.

## Package scope

This package contains one calendar skill, a direct HTTPS OAuth connection, its
icon and an MIT licence. It has no hooks, executable scripts, local server,
package downloads or application examples. It reads calendar data and cannot
publish content, change billing, place trades or transfer funds. Package validation
and repository distribution do not establish an approved Claude directory listing.
