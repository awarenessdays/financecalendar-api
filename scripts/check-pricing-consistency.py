#!/usr/bin/env python3
"""Check current pricing/access at the published OpenAPI and client documentation seam."""
from pathlib import Path
from copy import deepcopy
import json
import re
import urllib.request
import argparse

ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
 'starter':(1000,25000,{'year':999}),
 'build':(100000,None,{'month':999,'year':9590}),
 'scale':(1000000,None,{'month':2900,'year':27840}),
}

def validate_offer(offer):
    assert offer['production_api']['paid_plan_required'] is True
    assert offer['production_api']['renewable_free_tier'] is False
    for key,(daily,monthly,prices) in EXPECTED.items():
        plan=offer['plans'][key]
        assert plan['daily_limit']==daily and plan['monthly_limit']==monthly, key+' quota drift'
        assert set(plan['prices'])==set(prices), key+' billing interval drift'
        for interval,amount in prices.items():
            value=plan['prices'][interval]
            assert value['unit_amount']==amount and value['currency']=='usd' and value['interval']==interval, key+' price drift'
    trial=offer['evaluation']
    assert trial['duration_hours']==48 and trial['successful_requests_total']==25 and trial['max_records_per_response']==10
    assert trial['starts_at']=='first_successful_data_request' and trial['card_required'] is False and trial['automatic_charge'] is False
    assert offer['sample']['max_records']==3 and offer['sample']['filtering'] is False and offer['sample']['pagination'] is False

def main():
    args=argparse.ArgumentParser(description=__doc__);args.add_argument('--live-offer',action='store_true');options=args.parse_args()
    document=json.loads((ROOT/'openapi.json').read_text());offer=document['x-product-offer'];validate_offer(offer)
    assert document['security'], 'Data routes must keep required credentials.'
    for path in ['/sample','/product-offer','/openapi']:
        assert document['paths'][path]['get']['security']==[], path+' must describe public inspection access'
    for key,(daily,monthly,prices) in EXPECTED.items():
        quota=document['x-rate-limits'][key]
        assert quota['per_day']==daily and quota['per_calendar_month']==monthly, key+' OpenAPI quota drift'
    readme=(ROOT/'README.md').read_text()
    assert '## Affordable API access' in readme and '/fc/v1/sample' in readme
    assert '## Free economic calendar API access' not in readme
    for amount in ['9.99/year','95.90/year','278.40/year']:
        assert amount in readme, 'Missing current upfront charge '+amount
    for dirname in ['clients/node','clients/python']:
        guide=(ROOT/dirname/'README.md').read_text()
        for amount in ['9.99/year','95.90/year','278.40/year']:
            assert amount in guide, dirname+' lacks current charge '+amount
    for folder in [ROOT/'clients',ROOT/'integrations',ROOT/'examples']:
        for path in folder.rglob('*'):
            if not path.is_file() or any(part in {'node_modules','tests','test','fixtures','dist','build','__pycache__'} for part in path.relative_to(ROOT).parts):continue
            if path.suffix not in {'.md','.py','.js','.toml','.json'}:continue
            text=path.read_text()
            for stale in [r'250(?: API)? requests (?:per day|per UTC day)',r'(?<![0-9])5,000 (?:requests )?per (?:UTC )?calendar month',r'2,000 keyless',r'free with attribution']:
                assert not re.search(stale,text,re.I), str(path.relative_to(ROOT))+' has obsolete commercial copy'
    if options.live_offer:
        url='https://www.financecalendar.com/wp-json/fc/v1/product-offer'
        request=urllib.request.Request(url,headers={'User-Agent':'FinanceCalendar-consistency-check/1.0','Cache-Control':'no-cache'})
        with urllib.request.urlopen(request,timeout=30) as response:live=json.load(response)
        validate_offer(live)
        assert live['plans']==offer['plans'], 'Published source differs from canonical live offers.'
    for mutate in [lambda x:x['plans']['starter'].update({'daily_limit':250}),lambda x:x['plans']['starter']['prices']['year'].update({'unit_amount':1999}),lambda x:x['production_api'].update({'renewable_free_tier':True})]:
        candidate=deepcopy(offer);mutate(candidate)
        try:validate_offer(candidate)
        except AssertionError:continue
        raise AssertionError('A stale offer mutation was not rejected.')
    print('Pricing/access consistency passed; stale quota, price and free-tier mutations rejected.')

if __name__=='__main__':main()
