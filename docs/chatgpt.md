# Finance Calendar for ChatGPT — review package

The `chatgpt-plugin/` folder contains the dedicated OpenAI directory package:
one calendar skill, a hosted HTTPS OAuth MCP connection, a square brand icon and
the required listing metadata. The connection has 14 read-only tools. Access
follows the linked account's existing permissions and shared API allowance.

This is a prepared draft, not an approved or published ChatGPT listing. OpenAI
business identity verification, domain verification, native ChatGPT tests and a
real walkthrough recording must finish before submission.

```sh
python3 build-chatgpt-plugin.py --check --out /tmp/fc-chatgpt-build
```

The deterministic archive contains exactly seven files. Its README describes
account linking and example questions. It includes no credentials, hooks,
runtime installs, local clients or checkout. The OpenAI review metadata contains
five positive and three negative cases covering the hosted tool surface.

Edit `chatgpt-plugin-source/manifest.json` and its README, then regenerate with
`--stage --check`. Shared hosted skill semantics come from `integrations/`.
The reviewed Claude source remains a separate folder and branch.

Before final submission, supply the actual accessible walkthrough URL using
`--demo-url`, regenerate and build with `--require-review`. That check rejects a
missing recording. Reviewer credentials and sign-in instructions belong only in
OpenAI's private dashboard fields and must never enter the ZIP or repository.

[OpenAI submission requirements](https://developers.openai.com/plugins/deploy/submission)
and [authentication](https://developers.openai.com/plugins/build/auth).
