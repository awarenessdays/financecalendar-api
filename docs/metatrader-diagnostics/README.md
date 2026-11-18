# Accountless MT4 timer diagnostic

This is a dated minimal control, excluded from the product ZIP. It contains no Finance Calendar includes, parser, API data or order operations. Its timer call returned true with error 0 and reached the OnInit-returning marker, but no callbacks were recorded within 90 seconds in the accountless Windows runner.

The original raw JSON receipts are retained unchanged. See `../metatrader-acceptance.json` for run links and the separate compiler/parser acceptance. These controls do not claim successful MT4 connected-demo callback or HTTPS acceptance.
