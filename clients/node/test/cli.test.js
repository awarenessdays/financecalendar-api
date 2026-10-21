import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { mkdtempSync, rmSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { parseArgs } from "../cli.js";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

function cli(args, env = {}) {
  const r = spawnSync(process.execPath, ["--import", "./test/mock-fetch.mjs", "cli.js", ...args], {
    cwd: ROOT, encoding: "utf8", env: { ...process.env, TZ: "UTC", FC_API_KEY: "", ...env },
  });
  return { code: r.status, out: r.stdout, err: r.stderr };
}

describe("parseArgs", () => {
  test("positional args, value flags, boolean flags and --k=v", () => {
    const { pos, flags } = parseArgs(["calendar", "--from", "2026-10-19", "--holidays", "--tz=Europe/London", "--json", "x"]);
    assert.deepEqual(pos, ["calendar", "x"]);
    assert.deepEqual(flags, { from: "2026-10-19", holidays: true, tz: "Europe/London", json: true });
  });
  test("a value flag at the end of argv becomes true rather than swallowing nothing", () => {
    assert.deepEqual(parseArgs(["week", "--next"]).flags, { next: true });
    assert.deepEqual(parseArgs(["next", "fomc", "--country"]).flags, { country: true });
  });
});

describe("CLI (child process with mocked fetch)", () => {
  test("--help prints usage and exits 0", () => {
    const r = cli(["--help"]);
    assert.equal(r.code, 0);
    assert.match(r.out, /financecalendar 0\.2\.0/);
    assert.match(r.out, /FC_API_KEY/);
  });

  test("npm-style symlinked binary runs the CLI", () => {
    const directory = mkdtempSync(join(tmpdir(), "financecalendar-cli-"));
    try {
      const executable = join(directory, "financecalendar");
      symlinkSync(join(ROOT, "cli.js"), executable);
      const result = spawnSync(process.execPath, [executable, "--help"], { encoding: "utf8" });
      assert.equal(result.status, 0, result.stderr);
      assert.match(result.stdout, /financecalendar 0\.2\.0/);
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });

  test("next fomc --tz Europe/London renders one line plus URL", () => {
    const r = cli(["next", "fomc", "--tz", "Europe/London"]);
    assert.equal(r.code, 0, r.err);
    assert.equal(r.out, "Wed 28 Oct 18:00 GMT  FOMC Rate Decision (US)  cons. Hold at 3.50-3.75%  prior Hold\nhttps://www.financecalendar.com/event/fomc-rate-decision-october-2026/\n");
  });

  test("next fomc --tz America/New_York uses the ET label", () => {
    const r = cli(["next", "fomc", "--tz", "America/New_York"]);
    assert.equal(r.out.split("\n")[0], "Wed 28 Oct 14:00 ET  FOMC Rate Decision (US)  cons. Hold at 3.50-3.75%  prior Hold");
  });

  test("without --tz the local zone (TZ env) is used", () => {
    const r = cli(["next", "fomc"], { TZ: "Asia/Tokyo" });
    assert.match(r.out, /^Thu 29 Oct 03:00 GMT\+9  FOMC Rate Decision \(US\)/);
  });

  test("--json prints the raw response", () => {
    const r = cli(["next", "fomc", "--json"]);
    const data = JSON.parse(r.out);
    assert.equal(data.series_code, "fomc");
    assert.equal(data.attribution.source, "financecalendar.com");
  });

  test("today shows market line, events and closures", () => {
    const r = cli(["today", "--tz", "UTC"]);
    assert.equal(r.code, 0, r.err);
    const lines = r.out.trim().split("\n");
    assert.equal(lines[0], "2026-10-19  NYSE open");
    assert.equal(lines[1], "Mon 19 Oct 02:00 UTC  China GDP (CN)  period Q3 2026");
    assert.ok(lines.includes("Exchange closures today:"));
    assert.ok(lines.some((l) => l.startsWith("Mon 19 Oct all day  HKEX closed")));
  });

  test("week and week --next pick the right fixture", () => {
    assert.match(cli(["week", "--tz", "UTC"]).out, /^This week, 2026-10-19 to 2026-10-25/);
    assert.match(cli(["week", "--next", "--tz", "UTC"]).out, /^Next week, 2026-10-26 to 2026-11-01/);
  });

  test("calendar --csv prints the API's CSV", () => {
    const r = cli(["calendar", "--from", "2026-10-19", "--to", "2026-10-25", "--csv"]);
    assert.equal(r.code, 0, r.err);
    assert.match(r.out, /^date,time_utc,time_et,all_day,name,title/);
    assert.match(r.out, /Source: financecalendar\.com/);
  });

  test("calendar forwards --status and --offset", () => {
    const r = cli(["calendar", "--status", "estimated", "--offset", "5", "--limit", "2", "--json"]);
    assert.equal(r.code, 0, r.err);
    assert.equal(JSON.parse(r.out).from, "2026-10-19");
  });

  test("calendar --holidays includes holiday rows", () => {
    const r = cli(["calendar", "--from", "2026-11-23", "--to", "2026-11-30", "--holidays", "--tz", "UTC"]);
    assert.match(r.out, /2026-11-23 to 2026-11-30: 15 of 15 events/);
    assert.match(r.out, /JPX closed: Labor Thanksgiving Day \(JP\)/);
  });

  test("series, show, history, holidays, status, changes, countries", () => {
    const series = cli(["series", "--country", "us"]).out;
    assert.match(series, /^beige-book\s+Beige Book\s+US\s+low\s+next 2026-11-25$/m);
    assert.match(series, /^us-ppi\s+US Producer Price Index\s+US\s+medium\s+next tbc$/m);
    const show = cli(["show", "fomc", "--tz", "UTC"]).out;
    assert.match(show, /^FOMC Rate Decision \(fomc\)  US  central-banks-monetary-policy  impact high  8x\/year/);
    assert.match(show, /aliases: fed, fomc/);
    assert.match(show, /Next:\nWed 28 Oct 18:00 UTC  FOMC Rate Decision \(US\)/);
    const hist = cli(["history", "us-cpi", "--limit", "4", "--tz", "America/New_York"]).out;
    assert.match(hist, /^us-cpi: 4 releases, 2025-10-19 to 2026-10-19/);
    assert.match(hist, /actual 3\.0% y\/y/);
    const hol = cli(["holidays"]).out;
    assert.match(hol, /^NYSE holidays \(13\)/);
    assert.match(hol, /2026-11-26  Thanksgiving  NYSE  closed/);
    assert.match(hol, /2026-11-27  Day After Thanksgiving  NYSE  early close 13:00/);
    assert.match(cli(["holidays", "lse", "2027"]).out, /^LSE holidays/);
    const st = cli(["status"]).out;
    assert.match(st, /^NYSE open/);
    assert.match(st, /next holiday: 2026-11-26  Thanksgiving  closed/);
    assert.match(cli(["status", "lse"]).out, /LSE/i);
    assert.match(cli(["changes", "--since", "2026-10-18T00:00:00Z"]).out, /^100 changes since 2026-10-18T15:47:45\+00:00\n\n2026-10-19T12:00:00\+00:00  added   holidays-hkex/);
    assert.match(cli(["countries"]).out, /^US  United States {5}25 series {4}290 events/);
  });

  test("API errors go to stderr with exit code 1", () => {
    const r = cli(["calendar", "--tz", "Mars/Olympus"]);
    assert.equal(r.code, 1);
    assert.equal(r.out, "");
    assert.equal(r.err, "Error: tz must be an IANA timezone such as Europe/London or Asia/Tokyo. (HTTP 400)\n");
  });

  test("unknown command and missing argument are reported", () => {
    assert.match(cli(["bogus"]).err, /Unknown command "bogus"/);
    assert.match(cli(["next"]).err, /next needs a series/);
  });
});
