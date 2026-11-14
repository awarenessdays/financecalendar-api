#!/usr/bin/env python3
"""Build deterministic, allowlisted plugin/skill ZIPs without runtime installs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent
ENDPOINT = 'https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp'
FILES = ('plugin.json','mcp.json','.claude-plugin/plugin.json','.mcp.json','README.md','LICENSE','assets/icon.png',
         'skills/financecalendar/SKILL.md','skills/financecalendar/references/api.md','skills/financecalendar/agents/openai.yaml')


CLAUDE_ROOT = ROOT.parent / 'claude-plugin'
CLAUDE_FILES = ('.claude-plugin/plugin.json', '.mcp.json', 'README.md', 'LICENSE',
                'assets/icon.png', 'skills/financecalendar/SKILL.md',
                'skills/financecalendar/references/api.md')
CLAUDE_README = """# Finance Calendar for Claude

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
"""
CLAUDE_REFERENCE = """# Finance Calendar hosted tool reference

Use the connected Finance Calendar MCP tools and their discovered schemas.
The connection uses the account's existing permissions and shared API allowance.
OAuth consent grants calendar:read and, when requested, offline_access for renewal.

## Choose a tool

- feed_status: inspect the current feed and source health before a current-data query.
- countries and series_list: discover supported countries and exact series codes.
- series_detail: inspect one discovered series, its definition and available records.
- next_event: find the next covered occurrence for an exact series and country.
- calendar, today and week: query releases for the user's dates, filters and timezone.
- history: inspect supported series history; it is not an exhaustive export by itself.
- economic_results_history: retrieve bounded result histories for supported series.
- release_editions: inspect available publication editions for a returned event ID.
- market_holidays and market_status: inspect supported exchange closures and status.
- changes: follow recorded changes and the returned continuation checkpoint.

The server's discovered tool schemas are authoritative for required arguments,
bounds and accepted values. A familiar generic series name can default to the US;
use an exact discovered code or explicit country for another economy. Global
crypto records can have no country; use discovered canonical asset identifiers.

## Read results accurately

Hosted responses include canonical records in structuredContent.data. Preserve
record IDs, source links, source rights, reference periods, units and timestamps.
Unknown values are null, while a recorded zero is a real value. Provider consensus
and blended market forecasts are different fields; keep each value with its
measure, unit, as-of time and source evidence.

An absent release_at_utc means there is no verified publication instant. Do not
convert an unverified source_clock using a jurisdiction-only release_tz. Date-only
releases with all_day=false have unknown clock times; exchange closures can be
all-day events. Keep approximate windows, estimated schedules, cancellation,
source freshness and numerical observation freshness explicit.

Current-vintage figures, publisher-reported revisions, engine-observed revisions
and original first prints are different concepts. History does not reconstruct an
unobserved first print. An auction bidding deadline is not result publication.

## Pagination and errors

Inspect count, total, next_offset, next_cursor, has_more and truncation metadata.
Hosted pages have bounded sizes; one overview response may not contain all rows.
Narrow filters or paginate with the returned dates and filters. Keep stable IDs
when combining pages. Changes cursors bind the checkpoint and filters; finish all
pages before advancing the checkpoint. A snapshot-change conflict requires
restarting the original checkpoint and deduplicating already consumed records.

Respect rate-limit reset times and Retry-After rather than repeated retries.
Expired or revoked authorization needs the client's account-linking flow again.
An unavailable entitlement is an account-access fact, not an instruction to create
a subscription or change the user's plan. Do not infer a missing release or figure.
"""


def claude_sources(root=ROOT):
    """Derive the seven-file Claude directory; no examples or runtime scripts."""
    skill = (root/'skills/financecalendar/SKILL.md').read_text()
    skill = skill.split('## Build an integration', 1)[0].rstrip()
    start = skill.index('description: ')
    end = skill.index('\n', start)
    skill = skill[:start] + ('description: Find economic releases, central-bank decisions, '
        'exchange holidays and covered crypto events through the linked Finance '
        'Calendar account, preserving recorded timing and source evidence.') + skill[end:]
    skill = skill.replace('Local MCP and REST limits differ. ', '')
    skill = skill.replace('Paid REST calendar windows are at most 92 days. ', '')
    skill = skill.replace('; human CLI output is a summary', '')
    skill += '\n\nRead [hosted tool usage and record semantics](references/api.md) for tool selection, interpretation and continuation handling.\n'
    sources = {name: (root/name).read_bytes() for name in
               ('.claude-plugin/plugin.json', '.mcp.json', 'LICENSE', 'assets/icon.png')}
    sources.update({'README.md': CLAUDE_README.encode(),
                    'skills/financecalendar/SKILL.md': skill.encode(),
                    'skills/financecalendar/references/api.md': CLAUDE_REFERENCE.encode()})
    assert set(sources) == set(CLAUDE_FILES)
    return sources


def validate_claude(destination=CLAUDE_ROOT, root=ROOT):
    sources = claude_sources(root)
    paths = list(destination.rglob('*'))
    assert destination.is_dir() and not destination.is_symlink()
    assert not any(path.is_symlink() for path in paths), 'Claude directory cannot contain symlinks'
    actual = {str(path.relative_to(destination)) for path in paths if path.is_file()}
    assert actual == set(CLAUDE_FILES), 'Claude directory must contain exactly the seven allowlisted files'
    allowed_dirs = {str(parent) for name in CLAUDE_FILES for parent in Path(name).parents if str(parent) != '.'}
    assert {str(path.relative_to(destination)) for path in paths if path.is_dir()} == allowed_dirs, 'Claude directory contains an unexpected directory'
    for name, expected in sources.items():
        path = destination/name
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(destination.resolve())
        assert path.read_bytes() == expected, 'Claude staging drift: '+name
    return sources


def stage_claude(destination=CLAUDE_ROOT, root=ROOT):
    sources = claude_sources(root)
    if destination.exists():
        extras = {str(p.relative_to(destination)) for p in destination.rglob('*') if p.is_file()} - set(CLAUDE_FILES)
        assert not extras, 'Refusing to overwrite a Claude directory with extra files: '+str(sorted(extras))
    for name, value in sources.items():
        path = destination/name
        path.parent.mkdir(parents=True, exist_ok=True)
        assert not path.is_symlink() and path.resolve().is_relative_to(destination.resolve())
        path.write_bytes(value)
    validate_claude(destination, root)


def validate(root=ROOT):
    manifests=[json.loads((root/path).read_text()) for path in ('plugin.json','.claude-plugin/plugin.json')]
    assert manifests[0]['name']==manifests[1]['name']=='financecalendar'
    assert manifests[0]['version']==manifests[1]['version'] and re.fullmatch(r'\d+\.\d+\.\d+',manifests[0]['version'])
    for manifest in manifests:
        assert manifest['author']['name']=='Awareness Days Ltd' and manifest['license']=='MIT'
        assert not any(k in manifest for k in ('hooks','commands','agents','lspServers','userConfig'))
    assert manifests[1]['mcpServers']=='./.mcp.json' and manifests[1]['skills']=='./skills/'
    for filename,kind in [('mcp.json','streamable-http'),('.mcp.json','http')]:
        doc=json.loads((root/filename).read_text());assert set(doc['mcpServers'])=={'financecalendar'}
        server=doc['mcpServers']['financecalendar'];assert server['type']==kind and server['url']==ENDPOINT
        assert set(server)<= {'type','url','extensions'}
        assert 'headers' not in server
        if filename=='mcp.json':
            assert server['extensions']['com.openai']['auth']=={'type':'oauth','client':{'mode':'dcr'},'baseScopes':['calendar:read','offline_access']}
        else:
            assert set(server)=={'type','url'}
    for name in FILES:
        p=root/name
        assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root.resolve())
    skill=(root/'skills/financecalendar/SKILL.md').read_text()
    assert skill.startswith('---\nname: financecalendar\n') and 'references/api.md' in skill
    return manifests[0]['version']


def archive(path,files):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as output:
        for name,source in sorted(files):
            item=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=0o100644<<16
            output.writestr(item,source.read_bytes())
    return {'name':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--out',type=Path)
    args.add_argument('--stage-claude',type=Path,nargs='?',const=CLAUDE_ROOT)
    args.add_argument('--check-claude',action='store_true')
    opts=args.parse_args()
    if not opts.out and not opts.stage_claude and not opts.check_claude:
        args.error('Choose --out, --stage-claude or --check-claude')
    version=validate()
    if opts.stage_claude:
        stage_claude(opts.stage_claude)
    if opts.check_claude or CLAUDE_ROOT.exists():
        validate_claude()
    if not opts.out:
        print(json.dumps({'version':version,'claude_files':len(CLAUDE_FILES),'claude_directory':str(opts.stage_claude or CLAUDE_ROOT),'valid':True}))
        return
    opts.out.mkdir(parents=True,exist_ok=True)
    plugin=archive(opts.out/f'financecalendar-plugin-{version}.zip',[(name,ROOT/name) for name in FILES])
    prefix='skills/financecalendar/'
    skill=archive(opts.out/f'financecalendar-skill-{version}.zip', [('financecalendar/'+name.removeprefix(prefix),ROOT/name) for name in FILES if name.startswith(prefix)])
    outputs=[plugin,skill]
    if CLAUDE_ROOT.exists():
        validate_claude()
        outputs.append(archive(opts.out/f'financecalendar-claude-plugin-{version}.zip',[(name,CLAUDE_ROOT/name) for name in CLAUDE_FILES]))
    report={'version':version,'transport':'hosted Streamable HTTP with OAuth account linking, no local commands or embedded credentials','files':outputs,
            'scope':'Static packaging/containment checks; not a claim of a directory listing or account-level model evaluation.'}
    (opts.out/'SHA256SUMS').write_text(''.join(f"{x['sha256']}  {x['name']}\n" for x in report['files']))
    (opts.out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
