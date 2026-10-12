"""Retain full UDK query output without the guest-agent stdout size limit."""
import sys,runpy,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'bin')]
import editor_query
from vm import powershell,read_file

def file_log_since(offset):
 path='C:\\RLSetup\\AndyQuery-'+uuid.uuid4().hex+'.log'
 script=r"$ErrorActionPreference='Stop';$s=[string](Get-Content C:\UDK\Custom\UDKGame\Logs\Launch.log -Raw);"
 script+=f"if($s.Length -lt {offset}){{throw 'Editor log rotated'}};$s=$s.Substring({offset});$b=[Text.UTF8Encoding]::new($false).GetBytes($s);$f=[IO.File]::Open('{path}',[IO.FileMode]::CreateNew);try{{$f.Write($b,0,$b.Length)}}finally{{$f.Dispose()}};$b.Length"
 r=powershell(script,wait=30);assert r.get('exitcode')==0,r
 b=read_file(path);assert len(b)==int(r['out-data'].strip());return b.decode('utf-8')
editor_query.log_since=file_log_since
runpy.run_path(str(ROOT/'bin/editor_query_batch.py'),run_name='__main__')
