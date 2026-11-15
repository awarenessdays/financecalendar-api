#!/usr/bin/env python3
"""Stage and validate a minimal Finance Calendar ChatGPT directory package."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'chatgpt-plugin-source'
DEST = ROOT / 'chatgpt-plugin'
PORTABLE = ROOT / ('fc-integrations' if (ROOT/'fc-integrations').is_dir() else 'integrations')
FILES = ('plugin.json', 'mcp.json', 'README.md', 'LICENSE', 'assets/icon.png',
         'skills/financecalendar/SKILL.md', 'skills/financecalendar/references/api.md')
TOOLS = {'feed_status','countries','today','week','calendar','series_list','series_detail',
         'next_event','history','economic_results_history','release_editions',
         'market_holidays','market_status','changes'}
ENDPOINT = 'https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp'


def https_url(value: str):
    assert isinstance(value,str) and len(value)<=1024 and value.strip()==value
    p=urlsplit(value)
    assert p.scheme=='https' and p.hostname and p.username is None and p.password is None
    assert p.hostname not in {'localhost','127.0.0.1','::1'}
    return value


def expected():
    spec=importlib.util.spec_from_file_location('fc_shared_plugin_packager',PORTABLE/'build.py')
    shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
    shared.validate()
    hosted=shared.claude_sources(PORTABLE)
    result={name:hosted[name] for name in ('LICENSE','assets/icon.png','skills/financecalendar/SKILL.md','skills/financecalendar/references/api.md')}
    result['plugin.json']=(json.dumps(json.loads((SOURCE/'manifest.json').read_text()),indent=2,ensure_ascii=False)+'\n').encode()
    result['mcp.json']=(PORTABLE/'mcp.json').read_bytes()
    result['README.md']=(SOURCE/'README.md').read_bytes()
    assert set(result)==set(FILES)
    return result


def check(sources, require_review=False):
    manifest=json.loads(sources['plugin.json']);meta=manifest['extensions']['com.openai'];ui=meta['interface']
    assert manifest['name']=='financecalendar' and re.fullmatch(r'\d+\.\d+\.\d+',manifest['version'])
    assert manifest['author']['name']=='Awareness Days Ltd' and manifest['license']=='MIT'
    for key,limit in [('displayName',30),('shortDescription',30),('longDescription',4000),('developerName',80)]:
        value=ui[key];assert isinstance(value,str) and 0<len(value)<=limit and value.strip()
        if key!='longDescription':assert '\n' not in value
    for key in ['websiteURL','supportURL','privacyPolicyURL','termsOfServiceURL']:https_url(ui[key])
    prompts=ui['defaultPrompt'];assert len(prompts)<=3 and len(set(prompts))==len(prompts)
    for prompt in prompts:assert 0<len(prompt)<=128 and '\n' not in prompt and '@' not in prompt
    for key in ['logo','composerIcon']:assert ui[key]=='./assets/icon.png'
    icon=sources['assets/icon.png'];assert icon.startswith(b'\x89PNG\r\n\x1a\n') and len(icon)<=5*1024*1024
    width,height=struct.unpack('>II',icon[16:24]);assert width==height and 48<=width<=4096
    review=meta['review'];cases=review['test_cases'];assert len(cases['positive'])==5 and len(cases['negative'])==3
    covered=set()
    for kind,rows in cases.items():
        for case in rows:
            assert case['description'].strip() and case['prompt'].strip() and case['expected_behavior'].strip()
            assert len(case['description'])<=4000
            assert not {'test_credentials','reviewer_instructions'} & set(case)
            if kind=='positive':covered.update(n.strip() for n in case['tools_triggered'].split(','))
    assert covered==TOOLS, 'Review cases must cover the complete published 14-tool surface'
    assert review['commerce'] is False and review['commerce_description'].strip()
    assert not {'test_credentials','reviewer_instructions'} & set(review)
    if require_review: https_url(review['demo_recording_url'])
    elif review.get('demo_recording_url'):https_url(review['demo_recording_url'])
    server=json.loads(sources['mcp.json'])['mcpServers'];assert set(server)=={'financecalendar'}
    server=server['financecalendar'];assert server['type']=='streamable-http' and server['url']==ENDPOINT
    assert set(server)=={'type','url','extensions'} and 'headers' not in server
    assert server['extensions']['com.openai']['auth']=={'type':'oauth','client':{'mode':'dcr'},'baseScopes':['calendar:read','offline_access']}
    for name,blob in sources.items():
        if name.endswith(('.md','.json')):
            text=blob.decode();assert not re.search(r'fc_live_[a-zA-Z0-9]{16,}',text), 'Credential-like value in package'
    assert len(re.findall(r'\b\w+\b',sources['README.md'].decode()))>=40
    assert 'Research historical data' not in sources['skills/financecalendar/SKILL.md'].decode()
    return manifest['version'],(width,height)


def stage(sources):
    if DEST.exists():
        assert not DEST.is_symlink()
        actual={str(p.relative_to(DEST)) for p in DEST.rglob('*') if p.is_file()}
        assert not actual-set(FILES), 'Refusing to overwrite unexpected package files'
    for name,blob in sources.items():
        p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True)
        assert not p.is_symlink() and p.resolve().is_relative_to(DEST.resolve())
        p.write_bytes(blob)


def verify_staged(sources):
    paths=list(DEST.rglob('*'));assert DEST.is_dir() and not any(p.is_symlink() for p in paths)
    assert {str(p.relative_to(DEST)) for p in paths if p.is_file()}==set(FILES)
    for name,blob in sources.items():assert (DEST/name).read_bytes()==blob, 'Staging drift: '+name


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',action='store_true');p.add_argument('--check',action='store_true')
    p.add_argument('--out',type=Path);p.add_argument('--demo-url');p.add_argument('--require-review',action='store_true')
    args=p.parse_args();assert args.stage or args.check or args.out
    if args.demo_url:
        value=json.loads((SOURCE/'manifest.json').read_text());value['extensions']['com.openai']['review']['demo_recording_url']=https_url(args.demo_url)
        (SOURCE/'manifest.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    sources=expected();version,dimensions=check(sources,args.require_review)
    if args.stage:stage(sources)
    verify_staged(sources)
    report={'version':version,'files':len(FILES),'valid':True,'icon_dimensions':dimensions,'positive_cases':5,'negative_cases':3,'review_tools':len(TOOLS),'demo_url_present':bool(json.loads(sources['plugin.json'])['extensions']['com.openai']['review'].get('demo_recording_url')),'file_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in sorted(sources.items())},'scope':'Static package checks only; native ChatGPT tests, reviewer credentials, identity/domain verification and portal review are separate.'}
    if args.out:
        args.out.mkdir(parents=True,exist_ok=True);target=args.out/f'financecalendar-chatgpt-plugin-{version}.zip'
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name in sorted(FILES):
                entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o100644<<16
                z.writestr(entry,sources[name])
        report['archive']=target.name;report['archive_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        (args.out/'SHA256SUMS').write_text(report['archive_sha256']+'  '+target.name+'\n')
        (args.out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
