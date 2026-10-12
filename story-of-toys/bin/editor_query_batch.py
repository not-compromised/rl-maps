"""Read fresh properties under the toolkit lock, flushing this UDK log buffer."""
import json,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from editor_transport import dispatch
from editor_session import transaction
from editor_query import log_length,log_since
handle=sys.argv[1];queries=sys.argv[2:]
assert queries and all(re.fullmatch(r'\w+ \w+',q) for q in queries)
with transaction(handle):
 start=log_length()
 for q in queries:dispatch(handle,'console:GETALL '+q)
 dispatch(handle,'console:GETALL WorldInfo TimeDilation')
 dispatch(handle,'console:FLUSHLOG')
 text=log_since(start)
 assert 'TimeDilation = ' in text,'Missing completion sentinel'
 p=ROOT/'evidence'/'editor';p.mkdir(parents=True,exist_ok=True)
 f=p/(str(time.time_ns())+'-query.log');f.write_text(text)
 print(str(f))
 print('\n'.join(l for l in text.splitlines() if 'Log:' in l and ') ' in l))
