"""Keep the shared editor claim while avoiding slow ScheduledTasks startup."""
import csv,io,time
import editor
from vm import execute,powershell
from vm import read_file

def bridge_read_file(path):
    data=read_file(path)
    if 'editor-response-' in path:
        try:data.decode('utf-8-sig')
        except UnicodeDecodeError:
            # Windows PowerShell writes this bridge's JSON in the guest ANSI code page.
            data=data.decode('cp1252').encode('utf-8')
    return data

def guest_powershell(script, wait=10):
    if 'while((Get-ScheduledTask RLMapmakingBridge).State' not in script:
        return powershell(script,wait=max(wait,60))
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        result=execute(r'C:\Windows\System32\schtasks.exe',
                       ['/Query','/TN','RLMapmakingBridge','/FO','CSV','/NH'],15)
        if result.get('exitcode')!=0 or result.get('out-truncated'):
            raise RuntimeError('Cannot establish editor bridge task state: '+str(result))
        rows=list(csv.reader(io.StringIO(result.get('out-data',''))))
        if len(rows)!=1 or len(rows[0])!=3 or rows[0][0]!='\\RLMapmakingBridge':
            raise RuntimeError('Unexpected editor scheduler response: '+str(rows))
        if rows[0][2]=='Ready':return {'exited':True,'exitcode':0}
        if rows[0][2]!='Running':raise RuntimeError('Editor bridge unavailable: '+rows[0][2])
        time.sleep(.2)
    raise TimeoutError('Previous editor bridge task is still running')

# The shared dispatcher still owns locking, nonce matching, desktop verification,
# task launch and response collection. Only its readiness probe changes here.
editor.powershell=guest_powershell
editor.read_file=bridge_read_file
dispatch=editor.dispatch
