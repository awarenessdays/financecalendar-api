# Finance Calendar widget

A drop-in economic calendar for any site. One script tag, no build step, attribution link included.

```html
<div data-fc-widget data-country="US,GB" data-impact="high" data-days="7" data-title="This week's releases"></div>
<script src="https://www.financecalendar.com/wp-json/fc/v1/widget.js" async></script>
```

Options (all optional): `data-country` (comma list), `data-impact` (high, medium, low), `data-series` (codes, comma list), `data-category`, `data-days` (1 to 92), `data-limit`, `data-tz` (defaults to the visitor's zone), `data-title`.

Several widgets on one page work. Call `FinanceCalendarWidget.init()` after adding one dynamically.

Terms: free, including on commercial sites, as long as the Finance Calendar link in the widget stays visible.
