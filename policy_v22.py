"""V2.2 sequential policy: clarification-aware + uncertainty-aware + global greedy allocation.
Standard-library only. Uses only observable simulator state and policy memory.
"""
import itertools, math, random, sys, json
from kit import HARD, SOFT, eligibility

DAILY_BUDGET = 12
BUNDLE_COST = 3
ASK_CAP = DAILY_BUDGET // BUNDLE_COST


def soft_fit(a, b):
    vals=[]
    for k in SOFT:
        x=a['fields'].get(k); y=b['fields'].get(k)
        if x is not None and y is not None:
            vals.append(1.0 if x == y else 0.0)
    return sum(vals)/len(vals) if vals else 0.0


def pair_signature(a,b):
    vals=[]
    for k in SOFT:
        x=a['fields'].get(k); y=b['fields'].get(k)
        vals.append(None if x is None or y is None else int(x==y))
    return tuple(vals)


def historical_stats(state):
    intros={i['introduction_id']:i for i in state.get('introductions',[])}
    events=state.get('feedback',[])
    by_intro={}
    for e in events:
        by_intro.setdefault(e.get('introduction_id'),[]).append(e)
    stats={}
    for iid,intro in intros.items():
        a=intro.get('user_a'); b=intro.get('user_b')
        if not a or not b: continue
        yes=[]
        for e in by_intro.get(iid,[]):
            if e.get('event')=='introduction_response' and e.get('value') in ('yes','no'):
                yes.append(e['value']=='yes')
        if len(yes)!=2: continue
        # Store only observed historical outcome. Feature signature is filled later
        # from member snapshots by the caller.
        stats[tuple(sorted((a,b)))] = 1.0 if all(yes) else 0.0
    return stats


def feedback_feature_stats(state):
    members={m['member_id']:m for m in state.get('members',[])}
    intros={i['introduction_id']:i for i in state.get('introductions',[])}
    events=state.get('feedback',[])
    grouped={}
    for e in events:
        grouped.setdefault(e.get('introduction_id'),[]).append(e)
    out={}
    for iid,intro in intros.items():
        a_id,b_id=intro.get('user_a'),intro.get('user_b')
        if a_id not in members or b_id not in members: continue
        rs=[e for e in grouped.get(iid,[]) if e.get('event')=='introduction_response' and e.get('value') in ('yes','no')]
        if len(rs)!=2: continue
        a,b=members[a_id],members[b_id]
        sig=pair_signature(a,b)
        key=(sig, tuple(sorted((a['gender'],b['gender']))))
        s=out.setdefault(key,[0,0])
        s[0]+=1; s[1]+=int(all(e['value']=='yes' for e in rs))
    return out


def empirical_value(a,b,feature_stats):
    sig=pair_signature(a,b)
    key=(sig, tuple(sorted((a['gender'],b['gender']))))
    n,s=feature_stats.get(key,[0,0])
    # Laplace prior around 0.5. UCB-like bonus rewards informative but uncertain patterns.
    mean=(s+1)/(n+2)
    uncertainty=1/math.sqrt(n+1)
    return mean, uncertainty, n


def ask_priority(state):
    members=[m for m in state['members'] if m.get('available')]
    # Already introduced / waiting people should not consume clarification budget if busy.
    busy=set()
    day=state['day']
    for i in state.get('introductions',[]):
        if i.get('assigned_day',-1) <= day <= i.get('response_deadline_day',-1):
            busy.add(i.get('user_a')); busy.add(i.get('user_b'))
    members=[m for m in members if m['member_id'] not in busy]
    rows=[]
    for m in members:
        missing=[k for k in HARD if m['fields'].get(k) is None and m['field_status'].get(k) != 'declined']
        if not missing: continue
        # A declined hard field can never be filled by another clarification, so don't ask.
        if any(m['field_status'].get(k)=='declined' for k in HARD):
            continue
        potential=0; complete_other=0; fit_sum=0; fit_n=0
        for o in members:
            if o['member_id']==m['member_id']: continue
            if any(o['field_status'].get(k)=='declined' for k in HARD): continue
            status=eligibility(m,o)
            if status['status']=='infeasible': continue
            if status['status']=='needs_clarification':
                potential += 1
                other_missing=[k for k in HARD if o['fields'].get(k) is None]
                if not other_missing:
                    complete_other += 1
                    fit_sum += soft_fit(m,o); fit_n += 1
        avg_fit=fit_sum/fit_n if fit_n else 0.0
        # Clarification value: prioritize people whose answer can resolve many edges,
        # especially edges where the other person is already fully known.
        value=complete_other*(0.5+0.5*avg_fit)+0.25*max(0,potential-complete_other)
        # Small bonus for fewer missing fields: one clarification can still resolve the bundle,
        # but lower uncertainty makes the resulting state easier to use.
        value += 0.05*(1.0/(1+len(missing)))
        rows.append((value,complete_other,potential,m['member_id']))
    rows.sort(reverse=True)
    return [r[3] for r in rows[:ASK_CAP]]


def match_policy(state, memory):
    members=[m for m in state['members'] if m.get('available')]
    past={tuple(sorted((i['user_a'],i['user_b']))) for i in state.get('introductions',[])}
    stats=feedback_feature_stats(state)
    edges=[]
    degree={m['member_id']:0 for m in members}
    for a,b in itertools.combinations(members,2):
        key=tuple(sorted((a['member_id'],b['member_id'])))
        if key in past: continue
        e=eligibility(a,b)
        if e['status']!='feasible': continue
        degree[a['member_id']]+=1; degree[b['member_id']]+=1
        mean,unc,n=empirical_value(a,b,stats)
        fit=soft_fit(a,b)
        # Exploration/exploitation: exploit historical evidence when available,
        # otherwise uncertainty receives a controlled bonus.
        explore_bonus=0.10*unc
        score=0.55*mean + 0.35*fit + explore_bonus
        edges.append([score,mean,fit,n,a['member_id'],b['member_id']])
    # Global allocation heuristic: prefer high value, but protect scarce people.
    # Scarcity bonus makes the policy less likely to consume a person who has only one edge.
    for e in edges:
        scarcity=(1/(degree[e[4]]+1)+1/(degree[e[5]]+1))*0.10
        e[0]+=scarcity
    edges.sort(reverse=True)
    used=set(); pairs=[]
    for e in edges:
        a,b=e[4],e[5]
        if a in used or b in used: continue
        pairs.append([a,b]); used.update([a,b])
    return pairs


def decide(request):
    state=request['state']; memory=request.get('memory') or {}
    if request['phase']=='ask':
        return {'asks':[{'member_id':x,'field':'constraints'} for x in ask_priority(state)],'memory':memory}
    return {'pairs':match_policy(state,memory),'memory':memory}

if __name__=='__main__':
    req=json.load(sys.stdin)
    print(json.dumps(decide(req),allow_nan=False))
