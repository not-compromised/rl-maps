"""Check route dimensions and generated graph references before editor import."""
import math,re,json
from pathlib import Path
from course import GATES,SIZES,STAGE_STARTS,STAGE_NAMES,SPAWNS,TARGETS,DECKS,local,dot,sub
from logic import generate
from build_map import sensors

g=generate();text=g.serialize();names=set(g.nodes)
refs=re.findall(r"(?:LinkedOp|LinkedVariables)=\(?\w+'([^']+)'",text)
assert set(refs)<=names,set(refs)-names
volume_names=set(re.findall(r'Begin Actor Class=TriggerVolume Name=(\w+)', ''.join(sensors())))
origins=[re.search(r"Originator=TriggerVolume'[^']+\.([^'.]+)'",block)[1] for block in text.split('Begin Object Class=SeqEvent_Touch ')[1:]]
assert len(origins)==len(set(origins))==len(volume_names)==len(GATES)*18+len(STAGE_STARTS)*3+2
assert set(origins)==volume_names
assert {gate['radius'] for gate in GATES}==set(SIZES.values())
assert [gate['index'] for gate in GATES]==list(range(1,len(GATES)+1))
for gate in GATES:
 for angle in [j*math.tau/96 for j in range(96)]:
  v=sub(local(gate,0,gate['radius']*math.cos(angle),gate['radius']*math.sin(angle)),gate['center'])
  assert abs(dot(v,gate['normal']))<1e-6
  assert abs(math.sqrt(dot(v,v))-gate['radius'])<1e-6
 assert dot(sub(local(gate,190,0,0),local(gate,-190,0,0)),gate['normal'])>379.999
# These are structural obligations, not a claim of engine execution.
assert g.nodes['FinishEligible']['props']['VariableLinks(1)']==f"(LinkedVariables=(SeqVar_Int'Int{len(GATES)+1}'))"
assert 'SeqCond_CompareFloat' in text and 'GetVelocity' in text
for node in g.nodes.values():
 for key,val in node['props'].items():
  if key.startswith(('OutputLinks','VariableLinks')):assert val.count('(')==val.count(')'),(key,val)
assert 5<=len(STAGE_STARTS)<=10
assert len(STAGE_STARTS)==len(STAGE_NAMES)==len(SPAWNS)==len(TARGETS)==len(DECKS)-1
assert list(STAGE_STARTS)==sorted(set(STAGE_STARTS)) and STAGE_STARTS[0]==1
print(f'PASS: three round sizes, {len(GATES)} ordered gates, {len(STAGE_STARTS)} stages, {len(origins)} unique sensor/event pairs, resolved references and gated finish.')
