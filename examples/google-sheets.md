# Finance Calendar in Google Sheets

No script needed. The CSV endpoints work with `IMPORTDATA`.

Every release in the next 14 days:

```
=IMPORTDATA("https://www.financecalendar.com/wp-json/fc/v1/calendar?format=csv")
```

High impact only, 30 days, London time column:

```
=IMPORTDATA("https://www.financecalendar.com/wp-json/fc/v1/calendar?impact=high&to=" & TEXT(TODAY()+30, "yyyy-mm-dd") & "&tz=Europe/London&format=csv")
```

This week:

```
=IMPORTDATA("https://www.financecalendar.com/wp-json/fc/v1/week?format=csv")
```

Exchange holidays for 2027, all exchanges (JSON, so use a script or paste the CSV from the docs page):

```
https://www.financecalendar.com/wp-json/fc/v1/calendar?category=market-holidays&from=2027-01-01&to=2027-03-31&format=csv
```

Sheets refreshes `IMPORTDATA` about once an hour. Add a visible link to https://www.financecalendar.com on the sheet.
