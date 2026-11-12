# Finance Calendar in Google Sheets

Every API request requires your account API key. `IMPORTDATA` cannot attach the
required header; do not put a key in a formula or URL. You can export CSV from the
[Data explorer](https://www.financecalendar.com/data/) and import it into Sheets,
or use an Apps Script with a private user property.

[Paid API plans](https://www.financecalendar.com/pricing/) start at **US$9.99/year** for Starter (**1,000 requests/UTC day and 25,000/UTC calendar month**). Build is **US$9.99/month or US$95.90/year** for **100,000/day**. Scale is **US$29/month or US$278.40/year** for **1,000,000/day** and the complete current dataset download. [Inspect the public sample](https://www.financecalendar.com/api/sample/) before choosing a plan.

[Choose a paid plan](https://www.financecalendar.com/account/?plan=starter&billing_interval=year), confirm your email and complete secure checkout, then create an API key in your account.

Starter is **US$9.99/year** for **1,000 requests per UTC day and 25,000 per UTC calendar month**; Build includes **100,000/day** and Scale **1,000,000/day**. Account keys share their paid allowance. Check [current plans](https://www.financecalendar.com/pricing/) and your account for effective prices and limits.

The Data explorer, CSV exports and authenticated JSON example below require an active paid subscription. Open **Extensions → Apps Script** in your sheet, then run
`setFinanceCalendarKey` once to store your key in your own user properties, then
run `loadFinanceCalendar`. Only run code you trust; script editors can change
what code does with your credentials. Never commit a real key or log it.

```javascript
function setFinanceCalendarKey() {
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt("Finance Calendar API key", "Enter your own active key. It is stored in your user properties, not a cell.", ui.ButtonSet.OK_CANCEL);
  if (result.getSelectedButton() !== ui.Button.OK) return;
  const key = result.getResponseText().trim();
  if (!/^fc_live_[a-f0-9]{32}$/.test(key)) throw new Error("Use your actual account API key.");
  PropertiesService.getUserProperties().setProperty("FC_API_KEY", key);
}

function loadFinanceCalendar() {
  const key = PropertiesService.getUserProperties().getProperty("FC_API_KEY");
  if (!key) throw new Error("Run setFinanceCalendarKey first.");
  const response = UrlFetchApp.fetch(
    "https://www.financecalendar.com/wp-json/fc/v1/calendar?impact=high&tz=Europe/London&limit=10",
    {headers: {"X-API-Key": key, Accept: "application/json"}, muteHttpExceptions: true, followRedirects: false}
  );
  if (response.getResponseCode() !== 200) throw new Error("Finance Calendar HTTP " + response.getResponseCode() + ". Check your key and account allowance.");
  const data = JSON.parse(response.getContentText());
  // Keep publisher strings as text; a source name must not become a sheet formula.
  const cell = value => value == null ? "" : typeof value === "string" && /^[=+@-]/.test(value) ? "'" + value : value;
  const rows = [["Publisher date", "Release", "Area", "Actual", "Source"]].concat(
    data.events.map(event => [event.date, event.name, event.country, event.actual, event.source_url].map(cell))
  );
  SpreadsheetApp.getActiveSheet().getRange(1, 1, rows.length, rows[0].length).setValues(rows);
  if (data.total > data.events.length) SpreadsheetApp.getUi().alert("This page contains " + data.events.length + " of " + data.total + " matching records. This is a bounded view. A paid plan is needed for wider access; inspect your plan before requesting more records.");
}
```

A real zero stays a value; unavailable fields stay blank. Records are current
recorded vintages, not original first prints. Account keys share their plan allowance. Retain a visible link to https://www.financecalendar.com
and the supplied source credits when sharing data.
