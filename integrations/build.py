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
        if filename=='mcp.json':assert server['extensions']['com.openai']['auth']=={'type':'none'}
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
    args=argparse.ArgumentParser(description=__doc__);args.add_argument('--out',type=Path,required=True);opts=args.parse_args()
    version=validate();opts.out.mkdir(parents=True,exist_ok=True)
    plugin=archive(opts.out/f'financecalendar-plugin-{version}.zip',[(name,ROOT/name) for name in FILES])
    prefix='skills/financecalendar/'
    skill=archive(opts.out/f'financecalendar-skill-{version}.zip', [('financecalendar/'+name.removeprefix(prefix),ROOT/name) for name in FILES if name.startswith(prefix)])
    report={'version':version,'transport':'hosted Streamable HTTP, no local commands or embedded credentials','files':[plugin,skill],
            'scope':'Static packaging/containment checks; not a claim of a directory listing or account-level model evaluation.'}
    (opts.out/'SHA256SUMS').write_text(''.join(f"{x['sha256']}  {x['name']}\n" for x in report['files']))
    (opts.out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
