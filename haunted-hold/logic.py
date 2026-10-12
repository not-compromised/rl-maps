"""Generate auditable Kismet for directional, ordered gates and ordered checkpoints."""
from course import PACKAGE,GATES,SPAWNS,TARGETS,STAGE_STARTS,STAGE_NAMES

class Graph:
 def __init__(self):self.nodes={}
 def node(self,cls,name,**props):
  if name in self.nodes:raise ValueError(name)
  self.nodes[name]={'class':cls,'props':props};return name
 def ref(self,name):return self.nodes[name]['class']+"'"+name+"'"
 def bind(self,name,pin,*variables):
  self.nodes[name]['props'][f'VariableLinks({pin})']='(LinkedVariables=('+','.join(self.ref(v) for v in variables)+'))'
 def link(self,a,b,out=0,inp=0):
  props=self.nodes[a]['props'];key=f'OutputLinks({out})';new=f'(LinkedOp={self.ref(b)},InputLinkIdx={inp})'
  if key in props:props[key]=props[key][:-2]+','+new+'))'
  else:props[key]='(Links=('+new+'))'
 def integer(self,n):
  name='Int'+str(n).replace('-','Neg')
  if name not in self.nodes:self.node('SeqVar_Int',name,IntValue=str(n))
  return name
 def setint(self,name,var,value):
  self.node('SeqAct_SetInt',name);self.bind(name,0,self.integer(value));self.bind(name,1,var);return name
 def boolean(self,value):return 'TrueValue' if value else 'FalseValue'
 def setbool(self,name,var,value):
  self.node('SeqAct_SetBool',name);self.bind(name,0,self.boolean(value));self.bind(name,1,var);return name
 def compare(self,name,var,value):
  self.node('SeqCond_CompareInt',name);self.bind(name,0,var);self.bind(name,1,self.integer(value));return name
 def check(self,name,var):
  self.node('SeqCond_CompareBool',name);self.bind(name,0,var);return name
 def touch(self,name,origin):
  self.node('SeqEvent_Touch',name,Originator=f"TriggerVolume'{PACKAGE}.TheWorld:PersistentLevel.{origin}'",MaxTriggerCount='0',ReTriggerDelay='0.0',bPlayerOnly='False',**{'ClassProximityTypes(0)':"Class'TAGame.Car_TA'"})
  self.bind(name,0,'Car');return name
 def object(self,name,actor):
  self.node('SeqVar_Object',name,ObjValue=f"TargetPoint'{PACKAGE}.TheWorld:PersistentLevel.{actor}'");return name
 def text(self,name,message,x,y,seconds=3,variable=None,scale=1.5):
  self.node('SeqAct_DrawText',name,DisplayTimeSeconds=str(seconds),DrawTextInfo=f'(MessageText="{message}",MessageFontScale=(X={scale},Y={scale}),MessageOffset=(X={x},Y={y}),MessageColor=(R=210,G=255,B=235,A=255))')
  if variable:self.bind(name,1,variable)
  return name
 def chain(self,*names):
  for a,b in zip(names,names[1:]):self.link(a,b)
 def serialize(self):
  s=f'Begin Object Class=Sequence Name=Voyage\nObjName="{PACKAGE} - ordered flight"\nObjComment="See STYLE.md for current design. Ordered forward gates; persistent checkpoint; optional stage camera target."\n'
  for i,(name,node) in enumerate(self.nodes.items()):
   s+=f"Begin Object Class={node['class']} Name={name}\nObjPosX={(i%12)*230}\nObjPosY={(i//12)*180}\n"
   s+='\n'.join(k+'='+v for k,v in node['props'].items())+'\nEnd Object\n'
  s+=''.join(f"SequenceObjects({i})={self.ref(name)}\n" for i,name in enumerate(self.nodes))
  return s+'End Object\n'

def generate():
 g=Graph()
 for name,val in [('Stage',1),('Expected',1),('Armed',0),('Deaths',0),('Seconds',0),('Passed',0)]:g.node('SeqVar_Int',name,IntValue=str(val),VarName='"'+name+'"')
 for name,val in [('Running',False),('Finished',False),('ResetBusy',False),('CameraEnabled',True),('TrueValue',True),('FalseValue',False)]:g.node('SeqVar_Bool',name,bValue='1' if val else '0',VarName='"'+name+'"')
 g.node('SeqVar_Object','Car');g.node('SeqVar_Player','Player',bAllPlayers='False')
 g.object('Respawn','Spawn1');g.object('CameraDestination','CameraGate01');g.node('SeqVar_Object','CameraBall')
 g.node('SeqEvent_LevelLoaded','Loaded')
 g.node('SeqEvent_CarSpawned_TA','CarSpawned',MaxTriggerCount='0',bPlayerOnly='False');g.bind('CarSpawned',0,'Car')
 # Ball lifecycle is shared by checkpoint changes, resets, and the explicit camera pads.
 g.node('SeqAct_AddGameBall_TA','ClearCamera');g.bind('ClearCamera',0,'Player')
 g.node('SeqAct_Delay','CameraDelay',Duration='0.05');g.link('ClearCamera','CameraDelay',out=2)
 g.check('WantCamera','CameraEnabled');g.chain('CameraDelay','WantCamera')
 g.node('SeqAct_AddGameBall_TA','AddCamera');g.bind('AddCamera',0,'Player');g.bind('AddCamera',1,'CameraDestination');g.bind('AddCamera',2,'CameraBall');g.link('WantCamera','AddCamera')
 g.node('SeqAct_ChangeCollision','CameraNoCollision',CollisionType='COLLIDE_NoCollision',bCollideActors='False',bBlockActors='False');g.bind('CameraNoCollision',0,'CameraBall')
 g.node('SeqAct_SetBlockRigidBody','CameraNoBlocking');g.bind('CameraNoBlocking',0,'CameraBall')
 g.node('SeqAct_SetPhysics','CameraFixed',NewPhysics='PHYS_None');g.bind('CameraFixed',0,'CameraBall')
 g.chain('AddCamera','CameraNoCollision');g.link('CameraNoCollision','CameraNoBlocking',inp=1);g.chain('CameraNoBlocking','CameraFixed')
 g.setbool('EnableCamera','CameraEnabled',True);g.link('EnableCamera','ClearCamera',inp=2)
 g.setbool('DisableCamera','CameraEnabled',False);g.node('SeqAct_AddGameBall_TA','RemoveCamera');g.bind('RemoveCamera',0,'Player');g.link('DisableCamera','RemoveCamera',inp=2)
 for stage in range(1,len(STAGE_STARTS)+1):
  for switch in ('On','Off'):
   name=f'Camera{switch}{stage}';g.touch(name+'Touch',name+'Volume');g.link(name+'Touch','EnableCamera' if switch=='On' else 'DisableCamera')
 # A single reset entry owns the death increment and lock.
 g.check('CanReset','ResetBusy');g.setbool('LockReset','ResetBusy',True);g.link('CanReset','LockReset',out=1)
 g.check('CountFailure','Running');g.chain('LockReset','CountFailure')
 g.node('SeqAct_AddInt','CountDeath');g.bind('CountDeath',0,'Deaths');g.bind('CountDeath',1,g.integer(1));g.bind('CountDeath',2,'Deaths');g.link('CountFailure','CountDeath')
 g.compare('ChooseSpawn','Stage',1);g.link('CountFailure','ChooseSpawn',out=1);g.chain('CountDeath','ChooseSpawn')
 g.check('SpawnAfterFinish','Finished');g.chain('CarSpawned','SpawnAfterFinish');g.link('SpawnAfterFinish','ChooseSpawn',out=1)
 g.setint('DisarmReset','Armed',0)
 previous=None
 for stage,first in enumerate(STAGE_STARTS,1):
  choice='ChooseSpawn' if stage==1 else g.compare(f'ChooseSpawn{stage}','Stage',stage)
  if previous:g.link(previous,choice,out=1)
  reset=g.setint(f'ResetStage{stage}','Expected',first)
  g.link(choice,reset,out=2);g.chain(reset,'DisarmReset');previous=choice
 g.node('SeqAct_Teleport','TeleportToDeck',bUpdateRotation='True');g.bind('TeleportToDeck',0,'Car');g.bind('TeleportToDeck',1,'Respawn');g.chain('DisarmReset','TeleportToDeck')
 g.node('SeqAct_SetVelocity','StopCar',VelocityDir='(X=0,Y=0,Z=0)',VelocityMag='0');g.bind('StopCar',0,'Car');g.chain('TeleportToDeck','StopCar')
 g.node('SeqAct_GiveBoost_TA','Refill',BoostAmount='100.0');g.bind('Refill',0,'Car');g.chain('StopCar','Refill');g.link('TeleportToDeck','ClearCamera',inp=2)
 g.node('SeqAct_Delay','ResetCooldown',Duration='0.35');g.setbool('UnlockReset','ResetBusy',False);g.chain('TeleportToDeck','ResetCooldown','UnlockReset')
 g.touch('SeaTouch','SeaReset');g.check('NotFinished','Finished');g.chain('SeaTouch','NotFinished');g.link('NotFinished','CanReset',out=1)
 # Completed runs retain their score and remain beside the restart pad.
 g.node('SeqAct_Teleport','ReturnToFinish',bUpdateRotation='True');g.bind('ReturnToFinish',0,'Car');g.bind('ReturnToFinish',1,'CameraDestination')
 g.link('NotFinished','ReturnToFinish');g.link('SpawnAfterFinish','ReturnToFinish');g.chain('ReturnToFinish','StopCar')
 g.node('SeqAct_Delay','BoostClock',Duration='0.5');g.chain('Loaded','BoostClock');g.link('BoostClock','Refill');g.link('BoostClock','BoostClock')
 g.node('SeqAct_Delay','InitialCameraDelay',Duration='0.5');g.chain('Loaded','InitialCameraDelay');g.link('InitialCameraDelay','ClearCamera',inp=2)
 # Integer time is independent of HUD display latency.
 g.node('SeqAct_Delay','Clock',Duration='1.0');g.chain('Loaded','Clock');g.link('Clock','Clock');g.check('ClockRunning','Running');g.chain('Clock','ClockRunning');g.check('ClockFinished','Finished');g.chain('ClockRunning','ClockFinished')
 g.node('SeqAct_AddInt','Tick');g.bind('Tick',0,'Seconds');g.bind('Tick',1,g.integer(1));g.bind('Tick',2,'Seconds');g.link('ClockFinished','Tick',out=1)
 g.setbool('StartClock','Running',True)
 for gate in GATES:
  i=gate['index'];prefix=f'Gate{i:02}'
  entry=g.touch(prefix+'Entry',prefix+'EntryVolume');stage_check=g.compare(prefix+'EntryStage','Stage',gate['stage']);check=g.compare(prefix+'EntryExpected','Expected',i);arm=g.setint(prefix+'Arm','Armed',i);g.chain(entry,stage_check);g.link(stage_check,check,out=2);g.link(check,arm,out=2);g.link(arm,'StartClock')
  exit=g.touch(prefix+'Exit',prefix+'ExitVolume');check=g.compare(prefix+'ExitExpected','Expected',i);armed=g.compare(prefix+'IsArmed','Armed',i);g.chain(exit,check);g.link(check,armed,out=2)
  velocity=g.node('SeqVar_Vector',prefix+'Velocity');get=g.node('SeqAct_GetVelocity',prefix+'GetVelocity');g.bind(get,0,'Car');g.bind(get,2,velocity);g.link(armed,get,out=2)
  split=g.node('SeqAct_GetVectorComponents',prefix+'SplitVelocity');g.bind(split,0,velocity);g.chain(get,split)
  product=[];previous=split
  for axis,component in enumerate('XYZ'):
   value=g.node('SeqVar_Float',prefix+'V'+component);result=g.node('SeqVar_Float',prefix+'Dot'+component);g.bind(split,axis+1,value)
   op=g.node('SeqAct_MultiplyFloat',prefix+'Multiply'+component,ValueB=str(gate['normal'][axis]));g.bind(op,0,value);g.bind(op,2,result);g.chain(previous,op);previous=op;product.append(result)
  xy=g.node('SeqVar_Float',prefix+'DotXY');summed=g.node('SeqVar_Float',prefix+'Dot')
  op=g.node('SeqAct_AddFloat',prefix+'AddXY');g.bind(op,0,product[0]);g.bind(op,1,product[1]);g.bind(op,2,xy);g.chain(previous,op)
  op2=g.node('SeqAct_AddFloat',prefix+'AddZ');g.bind(op2,0,xy);g.bind(op2,1,product[2]);g.bind(op2,2,summed);g.chain(op,op2)
  forward=g.node('SeqCond_CompareFloat',prefix+'Forward',ValueB='1.0');g.bind(forward,0,summed);g.chain(op2,forward)
  advance=g.setint(prefix+'Advance','Expected',i+1);g.link(forward,advance,out=1);disarm=g.setint(prefix+'Disarm','Armed',0);g.chain(advance,disarm)
  miss=g.compare(prefix+'ActiveMiss','Expected',i);miss_stage=g.compare(prefix+'MissStage','Stage',gate['stage']);g.link(miss,miss_stage,out=2);g.link(miss_stage,'CanReset',out=2)
  for wedge in range(16):
   touch=g.touch(prefix+f'Miss{wedge:02}',prefix+f'MissVolume{wedge:02}');g.chain(touch,miss)
 # Each checkpoint requires the preceding section and changes both destinations.
 for stage in range(2,len(STAGE_STARTS)+1):
  prefix=f'Checkpoint{stage}'
  touch=g.touch(prefix+'Touch',prefix+'Volume')
  eligible=g.compare(prefix+'Eligible','Expected',STAGE_STARTS[stage-1])
  once=g.compare(prefix+'Once','Stage',stage-1)
  advance=g.setint(prefix+'Advance','Stage',stage)
  g.chain(touch,eligible);g.link(eligible,once,out=2);g.link(once,advance,out=2)
  respawn=g.node('SeqAct_SetObject',prefix+'Respawn',DefaultValue=f"TargetPoint'{PACKAGE}.TheWorld:PersistentLevel.Spawn{stage}'");g.bind(respawn,1,'Respawn')
  target=g.node('SeqAct_SetObject',prefix+'Target',DefaultValue=f"TargetPoint'{PACKAGE}.TheWorld:PersistentLevel.Camera{stage}'");g.bind(target,1,'CameraDestination')
  g.chain(advance,respawn,target);g.link(target,'ClearCamera',inp=2)
  title=g.text(prefix+'Title',f'{stage:02}  {STAGE_NAMES[stage-1]}',-220,-210,4,scale=2.3);g.chain(target,title)
 g.touch('FinishTouch','FinishVolume');g.compare('FinishEligible','Expected',len(GATES)+1);g.compare('FinishStage','Stage',len(STAGE_STARTS));g.chain('FinishTouch','FinishEligible');g.link('FinishEligible','FinishStage',out=2);g.setbool('Complete','Finished',True);g.link('FinishStage','Complete',out=2)
 g.text('FinishTitle','HOLD CLEARED',-260,-210,30,scale=2.5);g.chain('Complete','FinishTitle');g.link('Complete','RemoveCamera',inp=2);g.chain('Complete','StopCar')
 # Restart is explicit and resets all run state.
 g.touch('RestartTouch','RestartVolume');g.setint('RestartStage','Stage',1);g.setint('RestartDeaths','Deaths',0);g.setint('RestartTime','Seconds',0);g.setbool('RestartFinished','Finished',False);g.setbool('RestartRunning','Running',False)
 g.node('SeqAct_SetObject','RestoreSpawn',DefaultValue=f"TargetPoint'{PACKAGE}.TheWorld:PersistentLevel.Spawn1'");g.bind('RestoreSpawn',1,'Respawn');g.node('SeqAct_SetObject','RestoreTarget',DefaultValue=f"TargetPoint'{PACKAGE}.TheWorld:PersistentLevel.Camera1'");g.bind('RestoreTarget',1,'CameraDestination')
 g.chain('RestartTouch','RestartStage','RestartDeaths','RestartTime','RestartFinished','RestartRunning','RestoreSpawn','RestoreTarget','ChooseSpawn')
 g.node('SeqAct_Delay','HUDClock',Duration='0.2');g.chain('Loaded','HUDClock');g.link('HUDClock','HUDClock')
 g.node('SeqAct_SubtractInt','CountPassed');g.bind('CountPassed',0,'Expected');g.bind('CountPassed',1,g.integer(1));g.bind('CountPassed',2,'Passed');g.chain('HUDClock','CountPassed')
 # DrawText anchors at ClipY/3; the old -590 offset clipped the first lines.
 for var,label,x in [('Stage','Stage: ',-500),('Passed',f'Rings / {len(GATES)}: ',-180),('Deaths','Deaths: ',150),('Seconds','Seconds: ',400)]:
  value=g.node('SeqVar_String','HUD'+var+'String');convert=g.node('SeqAct_ConvertToString','HUD'+var+'Convert');g.bind(convert,0,var);g.bind(convert,1,value);g.chain('CountPassed',convert)
  text=g.text('HUD'+var,label,x,-150,.22,value,1.7);g.chain(convert,text)
 g.text('Instructions','Fly through the green ring. Land at each checkpoint. Green/violet pads toggle camera guide.',-520,280,9,scale=1.1);g.chain('Loaded','Instructions')
 sync_objective(g)
 return g


def sync_objective(g):
 """Select a single highlight and matching camera from Stage and Expected."""
 lights=[]
 for gate in GATES:
  i=gate['index'];var=f'Gate{i:02}Highlight'
  g.node('SeqVar_Object',var,ObjValue=f"StaticMeshActor'{PACKAGE}.TheWorld:PersistentLevel.Gate{i:02}Light_Actor'")
  lights.append(var)
 g.node('SeqAct_ToggleHiddenGame','HideGateHighlights');g.bind('HideGateHighlights',0,*lights)
 previous=None
 for i in range(1,len(GATES)+2):
  name=g.compare(f'ObjectiveExpected{i}','Expected',i)
  if previous:g.link(previous,name,out=1)
  else:g.chain('HideGateHighlights',name)
  previous=name
  # After a section's last ring, guide to its checkpoint until that landing is accepted.
  checkpoint=next((stage for stage,first in enumerate(STAGE_STARTS,1) if first==i and stage>1),None)
  choose=name
  if checkpoint:
   stage_test=g.compare(f'ObjectiveStage{i}','Stage',checkpoint)
   g.link(name,stage_test,out=2)
   target=g.node('SeqAct_SetObject',f'ObjectiveCheckpoint{checkpoint}',DefaultValue=f"TargetPoint'{PACKAGE}.TheWorld:PersistentLevel.Camera{checkpoint-1}'")
   g.bind(target,1,'CameraDestination');g.link(stage_test,target,out=0);g.link(target,'ClearCamera',inp=2)
   choose=stage_test
  destination=f'CameraGate{i:02}' if i<=len(GATES) else f'Camera{len(STAGE_STARTS)}'
  target=g.node('SeqAct_SetObject',f'ObjectiveTarget{i}',DefaultValue=f"TargetPoint'{PACKAGE}.TheWorld:PersistentLevel.{destination}'")
  g.bind(target,1,'CameraDestination');g.link(choose,target,out=2)
  if i<=len(GATES):
   show=g.node('SeqAct_ToggleHiddenGame',f'ShowGate{i:02}');g.bind(show,0,f'Gate{i:02}Highlight')
   g.link(target,show,inp=1);g.link(show,'ClearCamera',inp=2)
  else:g.link(target,'ClearCamera',inp=2)
 # Replace the old section-only camera refresh edges. Choice happens after state changes.
 for source in ['InitialCameraDelay','TeleportToDeck']+[f'Checkpoint{stage}Target' for stage in range(2,len(STAGE_STARTS)+1)]:
  props=g.nodes[source]['props'];key='OutputLinks(0)'
  import re
  if key in props:
   props[key]=re.sub(r"\(LinkedOp=SeqAct_AddGameBall_TA'ClearCamera',InputLinkIdx=2\),?",'',props[key]).replace(',)',')')
   if props[key]=='(Links=())':del props[key]
  g.link(source,'HideGateHighlights')
 for gate in GATES:g.chain(f'Gate{gate["index"]:02}Disarm','HideGateHighlights')
 g.chain('Complete','HideGateHighlights')
 # Finished runs have no guide/highlight; branch before any objective selection.
 original=g.nodes['HideGateHighlights']['props'].pop('OutputLinks(0)')
 g.check('ObjectivesAfterFinish','Finished')
 g.nodes['ObjectivesAfterFinish']['props']['OutputLinks(1)']=original
 g.chain('HideGateHighlights','ObjectivesAfterFinish')
