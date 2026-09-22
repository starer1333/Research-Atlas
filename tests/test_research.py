import unittest,tempfile,sys,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from atlas.store import Store
from atlas import drivers,extraction
from atlas.engine import ValidationError
from atlas.seed import DEMO_UPDATE

class ResearchTests(unittest.TestCase):
    def setUp(self):
        folder=ROOT/'.runtime'/'research-tests';folder.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=folder);self.store=Store(Path(self.tmp.name)/'data.sqlite3')
        self.s=self.store.state('NVDA','2025-03-01')
    def tearDown(self):self.tmp.cleanup()
    def call(self,route,**p):return self.store.action(route,{'company':'NVDA','asof':'2025-03-01',**p})
    def payload(self):
        d=drivers.suggested(self.s)
        return {**d,'reason':'Synthetic assumptions only','counter':'Competitors may take demand','trigger':'Actual misses forecast','source_ids':['nv-fy25']}
    def draft(self,**p):
        return self.call('extraction-draft',source_id='nv-fy25',period='FY2025',period_start='2024-01-29',period_end='2025-01-26',unit='million',text='营业收入：130497\n营业成本：32639',**p)
    def test_derived_balance_not_independent(self):
        s=self.store.state('AMD','2025-03-01');r=next(c for c in s['relations']['checks'] if c['id']=='balance' and c['period']=='FY2024')
        self.assertEqual(r['status'],'pass');self.assertEqual(r['verification'],'derived_consistency');self.assertEqual(r['dependent_inputs'],['liabilities']);self.assertFalse(r['reviewed'])
    def test_independent_check_review_separate(self):
        c=next(c for c in self.s['relations']['checks'] if c['id']=='gross' and c['period']=='FY2025')
        self.assertEqual(c['verification'],'independent_disclosures');self.assertFalse(c['reviewed'])
        self.call('review',ids=[o['id'] for o in self.s['observations'] if o['period']=='FY2025' and o['metric'] in ['revenue','cost','gross_profit']])
        c=next(c for c in self.store.state('NVDA','2025-03-01')['relations']['checks'] if c['id']=='gross' and c['period']=='FY2025');self.assertTrue(c['reviewed'])
    def test_hardware_hand_calculation_and_bridge(self):
        s=copy.deepcopy(self.s);s['diagnostics']['current']={'revenue':100,'cost':60,'gross_profit':40,'operating_income':20};s['relations']['checks']=[]
        p={**drivers.suggested(s)['params'],'volume_growth':10,'price_growth':10,'unit_cost_growth':0,'opex_growth':0,'tax_rate':20,'da_ratio':0,'capex_ratio':0,'dso':0,'dio':0,'dpo':0,'opening_nwc':0}
        r=drivers.calculate(s,'hardware',p);first=r['rows'][0]
        self.assertEqual(first['revenue'],121);self.assertEqual(first['cost'],66);self.assertEqual(first['ebit'],35);self.assertEqual(first['fcff'],28)
        self.assertEqual(sum(x['value'] for x in r['bridges'][0]['effects']),21)
    def test_subscription_recognition_is_not_exit_runrate(self):
        s=copy.deepcopy(self.s);s['company']['mode']='software';s['diagnostics']['current']={'revenue':100,'cost':20,'gross_profit':80,'operating_income':30};s['relations']['checks']=[]
        p={**drivers.suggested(s)['params'],'retention':90,'expansion':10,'new_customer_rate':20,'new_customer_timing':.5}
        r=drivers.calculate(s,'software',p);self.assertEqual(r['rows'][0]['revenue'],109);self.assertEqual(r['rows'][0]['assumed_exit_runrate'],119)
        for b in r['bridges']:self.assertAlmostEqual(b['opening_revenue']+sum(x['value'] for x in b['effects']),b['closing_revenue'],places=1)
    def test_working_capital_absorbs_cash(self):
        p=self.payload();base=self.call('driver-calculate',**p);p['params']['dso']+=30;changed=self.call('driver-calculate',**p)
        self.assertEqual(base['rows'][0]['ebit'],changed['rows'][0]['ebit']);self.assertLess(changed['rows'][0]['fcff'],base['rows'][0]['fcff'])
    def test_driver_requires_evidence_and_counter(self):
        for update in [{'counter':''},{'source_ids':['ad-fy24']},{'source_ids':['nv-q1-26']}]:
            with self.assertRaises(ValidationError):self.call('driver-save',**{**self.payload(),**update})
    def test_immutable_driver_revision(self):
        p=self.payload();old=self.call('driver-save',**p);p['params']['price_growth']=-5
        new=self.call('driver-save',**{**p,'parent_id':old['id'],'reason':'Test price pressure'})
        self.assertEqual(old['result']['params']['price_growth'],0);self.assertLess(new['result']['change']['rows'][0]['revenue'],0)
        diff=self.call('driver-diff',before=old['id'],after=new['id']);self.assertEqual(len(diff['params']),1)
        self.call('import-example');saved=self.store.state('NVDA','2025-06-01')['records'];self.assertTrue(all(r['stale'] for r in saved if r['kind']=='driver'))
    def test_financial_and_invalid_driver_rejected(self):
        s=copy.deepcopy(self.s);s['company']['mode']='financial'
        with self.assertRaises(ValidationError):drivers.calculate(s,'hardware',self.payload()['params'])
        p=self.payload();p['params']['dso']=float('nan')
        with self.assertRaises(ValidationError):self.call('driver-calculate',**p)
    def test_intel_negative_net_income_no_cash_conversion_ranking(self):
        r=self.store.compare('AMD',['INTC'],'2025-03-01',True)['rows'][1]
        self.assertEqual(r['values']['net_income'],-19233);self.assertEqual(r['metric_checks']['cash_conversion']['status'],'blocked');self.assertEqual(r['metric_checks']['revenue']['status'],'qualified')
    def test_cross_currency_ratio_but_not_amount(self):
        self.store.create_company({'ticker':'EU','name':'Synthetic Euro company','industry':'semiconductors','currency':'EUR'})
        doc={'id':'eu','company':'EU','title':'test','url':'https://example.com','locator':'test','disclosed_at':'2025-02-01','observations':[{'id':'eu-'+k,'company':'EU','metric':k,'period':'FY2024','period_type':'annual','period_start':'2023-12-31','period_end':'2024-12-28','value':v,'currency':'EUR','unit':'million','basis':'GAAP','scope':'consolidated','kind':'Disclosed'} for k,v in {'revenue':100,'cost':60,'gross_profit':40}.items()]}
        self.store.import_document(doc);r=self.store.compare('AMD',['EU'],'2025-03-01',True)['rows'][1]
        self.assertEqual(r['metric_checks']['revenue']['status'],'blocked');self.assertEqual(r['metric_checks']['gross_margin']['value'],40)
    def test_peer_update_marks_cross_company_snapshot_stale(self):
        saved=self.call('comparison-save',company='AMD',peers=['NVDA'],nearby=True,reason='Test comparison')['id'];self.call('import-example')
        r=next(r for r in self.store.state('AMD','2025-06-01')['records'] if r['id']==saved);self.assertEqual(r['stale'],1);self.assertEqual(r['content']['asof'],'2025-03-01')
    def test_business_note_requires_both_sources(self):
        p={'peer':'AMD','level':'segment','subject':'Data center','dimension':'Product mix','observation':'Different scope','mechanism':'Mix affects margin','alternative':'Accounting classification','trigger':'Comparable disclosure','source_ids':['nv-fy25'],'peer_source_ids':['amd-fy24']}
        self.call('business-note',**p)
        with self.assertRaises(ValidationError):self.call('business-note',**{**p,'peer_source_ids':['ad-fy24']})
    def test_research_revisions_preserve_original(self):
        p={'question':'Why cash?','conclusion':'Open question','alternative':'Timing','next_evidence':'AR detail','change_reason':'Start research','status':'open','source_ids':['nv-fy25']}
        old=self.call('research-save',**p)['id'];new=self.call('research-save',**{**p,'parent_id':old,'status':'challenged','conclusion':'New explanation'})['id']
        rows=self.store.state('NVDA','2025-03-01')['records'];self.assertEqual(next(r for r in rows if r['id']==old)['content']['conclusion'],'Open question');self.assertNotEqual(old,new)
    def test_claim_question_and_evidence_contract_rejects_mismatch(self):
        q=self.call('question-save',question='Why cash?',reason='Investigate cash conversion',finding_id=None,evidence_ids=['NVDA-FY2025-cfo'],source_ids=['nv-fy25'],status='open')['id']
        base={'question':'Why cash?','question_id':q,'conclusion':'Timing explains part of the gap','alternative':'Working capital','next_evidence':'Receivables detail','change_reason':'Initial claim','status':'supported','supporting_evidence_ids':['NVDA-FY2025-cfo'],'counter_evidence_ids':['NVDA-FY2025-receivables'],'source_ids':['nv-fy25']}
        self.call('research-save',**base)
        with self.assertRaises(ValidationError):self.call('research-save',**{**base,'question':'Different question'})
        with self.assertRaises(ValidationError):self.call('research-save',**{**base,'counter_evidence_ids':['NVDA-FY2025-cfo']})
        with self.assertRaises(ValidationError):self.call('research-save',**{**base,'source_ids':['nv-fy25'],'counter_evidence_ids':['NVDA-FY2025-receivables'],'supporting_evidence_ids':['AMD-FY2024-cfo']})

    def test_research_memory_respects_record_asof_and_keeps_all_time_history(self):
        early=self.call('question-save',question='Early question',reason='Visible at early as-of',finding_id=None,evidence_ids=[],source_ids=['nv-fy25'],status='open')['id']
        self.call('import-example')
        late=self.store.action('question-save',{'company':'NVDA','asof':'2025-06-01','question':'Later question','reason':'Only valid after later disclosure','finding_id':None,'evidence_ids':[],'source_ids':['nv-q1-26'],'status':'open'})['id']
        early_state=self.store.state('NVDA','2025-03-01')
        visible={r['id'] for r in early_state['records']}
        all_time={r['id'] for r in early_state['revision_history_all_time']}
        self.assertIn(early,visible);self.assertNotIn(late,visible)
        self.assertIn(early,all_time);self.assertIn(late,all_time)

    def test_extraction_abstains_and_does_not_execute(self):
        r=extraction.extract('Revenue: 1,200\nNet income: (30)\nRevenue 2024 1200 2023 1000\n<script>delete_files()</script>','FY2024','million')
        self.assertEqual([c['value'] for c in r['candidates']],[1200,-30]);self.assertEqual(len(r['unmatched']),2);self.assertFalse(r['model_called'])
    def test_external_candidates_require_literal_quote(self):
        with self.assertRaises(ValidationError):extraction.extract('Revenue: 100','FY2024','million','external-json',[{'metric':'revenue','value':100,'quote':'Revenue: 200'}])
    def test_draft_review_import_are_separate_and_idempotent(self):
        before=len(self.s['observations']);d=self.draft();self.assertEqual(len(self.store.state('NVDA','2025-03-01')['observations']),before)
        r=self.call('extraction-review',id=d['id'],decisions=[{'action':'accept','reason':'Compared source'},{'action':'reject','reason':'Need verify scope'}]);self.assertEqual(r['result']['evaluation']['total'],2)
        self.assertEqual(len(self.store.state('NVDA','2025-03-01')['observations']),before)
        self.call('extraction-import',id=r['id']);s=self.store.state('NVDA','2025-03-01');self.assertEqual(len(s['observations']),before+1);self.assertFalse(s['observations'][-1]['reviewed'])
        with self.assertRaises(ValidationError):self.call('extraction-import',id=r['id'])
    def test_review_corrections_logged_and_duplicates_rejected(self):
        draft=extraction.extract('Revenue: 100\nCost of sales: 60','FY2024','million')
        r=extraction.review(draft,[{'action':'correct','metric':'revenue','value':110,'reason':'Source says 110'},{'action':'reject','reason':'Unclear'}]);self.assertEqual(r[0]['proposed']['value'],100);self.assertEqual(r[0]['accepted']['value'],110)
        with self.assertRaises(ValidationError):extraction.review(draft,[{'action':'accept','reason':'ok'},{'action':'correct','metric':'revenue','value':60,'reason':'test'}])
    def test_extraction_cross_company_record_forbidden(self):
        d=self.draft()
        with self.assertRaises(ValidationError):self.call('extraction-review',company='AMD',id=d['id'],decisions=[])

if __name__=='__main__':unittest.main(verbosity=2)
