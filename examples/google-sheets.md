# Finance Calendar in Google Sheets

Every API request requires your account API key. `IMPORTDATA` cannot attach the
required header; do not put a key in a formula or URL. You can export CSV from the
[Data explorer](https://www.financecalendar.com/data/) and import it into Sheets,
or use an Apps Script with a private user property.

Create and verify a Free account, create a key in your Finance Calendar workspace,
then open **Extensions → Apps Script** in your sheet. Add the code below. Run
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
    "https://www.financecalendar.com/wp-json/fc/v1/calendar?impact=high&tz=Europe/London&limit=100",
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
  if (data.total > data.events.length) SpreadsheetApp.getUi().alert("This page contains " + data.events.length + " of " + data.total + " matching records. Page with offset for more.");
}
```

A real zero stays a value; unavailable fields stay blank. Records are current
recorded vintages, not original first prints. New Free accounts include 1,000 API
requests per UTC day shared across their keys; existing accounts retain their
effective allowance. Retain a visible link to https://www.financecalendar.com
and the supplied source credits when sharing data.
