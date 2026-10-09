import argparse,json,os,csv
from itertools import combinations

HARD=['age_min','age_max','who_to_meet','relationship_structure','smoking','partner_smoking','has_children','partner_children','wants_children','acceptable_zones','schedule']
SOFT=['relationship_goal','relationship_pace','lifestyle','conversations','emotional_availability','space_for_relationship','relocate']

def load(path):
    with open(path,encoding='utf-8') as f:return [json.loads(x) for x in f if x.strip()]

def state_at(m,day):
    x={k:(None if m['fields'].get(k) is None else m['fields'][k]) for k in m['fields']}
    status={}
    for k in m['fields']:
        od=m.get('field_observed_day',{}).get(k)
        fs=m.get('field_status',{}).get(k)
        if fs=='observed' and od is not None and od<=day:
            status[k]='observed'; x[k]=m['fields'][k]
        elif fs=='declined':
            status[k]='declined'; x[k]=None
        else:
            status[k]='not_asked'; x[k]=None
    return x,status

def pair(a,b):
    fa,fb=a['fields'],b['fields']; fails=[]; miss=[]
    for m,f in ((a,fa),(b,fb)):
        for k in HARD:
            if f.get(k) is None: miss.append((m['member_id'],k))
    for x,y,fx,fy in ((a,b,fa,fb),(b,a,fb,fa)):
        if fx.get('who_to_meet') is not None and y['gender'] not in fx['who_to_meet']:fails.append('gender')
        if fx.get('age_min') is not None and y['age']<fx['age_min']:fails.append('age')
        if fx.get('age_max') is not None and y['age']>fx['age_max']:fails.append('age')
        if fx.get('acceptable_zones') is not None and y['zone'] not in fx['acceptable_zones']:fails.append('geography')
        if fx.get('partner_smoking')=='no_smoking' and fy.get('smoking') in ('yes','occasionally'):fails.append('smoking')
        if fx.get('partner_children')=='no_children' and fy.get('has_children') is True:fails.append('children')
    if fa.get('relationship_structure') is not None and fb.get('relationship_structure') is not None and fa['relationship_structure']!=fb['relationship_structure']:fails.append('relationship_structure')
    if {fa.get('wants_children'),fb.get('wants_children')}=={'yes','no'}:fails.append('children_plans')
    if fa.get('schedule') is not None and fb.get('schedule') is not None and not set(fa['schedule'])&set(fb['schedule']):fails.append('schedule')
    return bool(fails),miss

def soft(a,b):
    vals=[]
    for k in SOFT:
        if a['fields'].get(k) is not None and b['fields'].get(k) is not None: vals.append(a['fields'][k]==b['fields'][k])
    return sum(vals)/len(vals) if vals else 0

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',default='data');ap.add_argument('--out',default='analysis_output/clarification_backtest');args=ap.parse_args();os.makedirs(args.out,exist_ok=True)
    summary=[]; detail=[]
    for name in sorted(os.listdir(args.data_dir)):
        d=os.path.join(args.data_dir,name)
        if not name.startswith('public_') or not os.path.exists(os.path.join(d,'members.jsonl')):continue
        members=load(os.path.join(d,'members.jsonl')); by={m['member_id']:m for m in members}
        state=json.load(open(os.path.join(d,'state.json'),encoding='utf-8'))
        asks=[a for a in state.get('ask_log',[]) if a.get('field')=='constraints']
        days=sorted(set(a['observed_day'] for a in asks))
        for day in days:
            ask_ids={a['member_id'] for a in asks if a['observed_day']==day}
            snap=[]
            for m in members:
                if m['arrived_day']>day:continue
                fields,status=state_at(m,day)
                # Do not recommend a person who has already declined any hard field.
                askable=[k for k in HARD if status[k]=='not_asked']
                if not askable or any(status[k]=='declined' for k in HARD):continue
                mm=dict(m);mm['fields']=fields;snap.append((mm,askable))
            scored=[]
            for m,askable in snap:
                potential=0;complete_partner=0;sf=0;sn=0
                for o,_ in snap:
                    if o['member_id']==m['member_id']:continue
                    fail,missing=pair(m,o)
                    if fail:continue
                    if missing:
                        potential+=1
                        # If all o hard fields known, asking m is the only unresolved side.
                        omiss=[k for k in HARD if o['fields'].get(k) is None]
                        if not omiss:
                            complete_partner+=1;sf+=soft(m,o);sn+=1
                avg=sf/sn if sn else 0
                value=complete_partner*(0.5+0.5*avg)+0.25*max(0,potential-complete_partner)
                scored.append({'dataset':name,'day':day,'member_id':m['member_id'],'missing_fields':len(askable),'potential_pairs':potential,'complete_partner_opportunities':complete_partner,'avg_soft_fit':round(avg,4),'clarification_value':round(value,4),'actual_asked':int(m['member_id'] in ask_ids)})
            scored.sort(key=lambda r:(-r['clarification_value'],-r['complete_partner_opportunities'],-r['potential_pairs'],r['member_id']))
            for i,r in enumerate(scored,1):r['rank']=i;detail.append(r)
            top={r['member_id'] for r in scored[:4]}
            actual=len(ask_ids);hit=len(top & ask_ids)
            summary.append({'dataset':name,'day':day,'actual_asks':actual,'top4_hits':hit,'top4_precision':round(hit/max(1,actual),3),'available_askable_candidates':len(scored),'top_value':scored[0]['clarification_value'] if scored else 0})
    with open(os.path.join(args.out,'clarification_backtest_detail.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=detail[0].keys() if detail else ['dataset']);w.writeheader();w.writerows(detail)
    with open(os.path.join(args.out,'clarification_backtest_summary.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=summary[0].keys() if summary else ['dataset']);w.writeheader();w.writerows(summary)
    print('\n'+'='*70);print('CLARIFICATION BACKTEST');print('='*70)
    print('Historical clarification days:',len(summary))
    if summary:
        print('Mean top-4 hit count:',round(sum(x['top4_hits'] for x in summary)/len(summary),3))
        print('Mean top-4 precision:',round(sum(x['top4_precision'] for x in summary)/len(summary),3))
        print('Total historical asks:',sum(x['actual_asks'] for x in summary))
        print('Total top-4 hits:',sum(x['top4_hits'] for x in summary))
        print('\nFIRST 15 DAYS')
        for x in summary[:15]:print(x)
    print('OUTPUT:',os.path.abspath(args.out))
if __name__=='__main__':main()
