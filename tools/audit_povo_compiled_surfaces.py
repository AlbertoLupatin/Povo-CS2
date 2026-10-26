#!/usr/bin/env python3
"""Verify physical surfaces in actual compiled ModelDoc PHYS data."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def token(name):
    """Source 2's lowercase Murmur2 string token; default = 1977497166."""
    data=name.lower().encode('ascii');m=0x5bd1e995;h=(0x31415926^len(data))&0xffffffff
    for i in range(0,len(data)//4*4,4):
        k=struct.unpack_from('<I',data,i)[0];k=k*m&0xffffffff;k^=k>>24;k=k*m&0xffffffff
        h=(h*m&0xffffffff)^k
    tail=data[len(data)//4*4:]
    if tail:h^=int.from_bytes(tail,'little');h=h*m&0xffffffff
    h^=h>>13;h=h*m&0xffffffff;h^=h>>15
    return h


def audit(model,expect,*,decoder=None,output=None):
    decoder=decoder or ROOT/'build/tools/vrf-20.1/Source2Viewer-CLI.exe'
    result=subprocess.run([str(decoder),'-i',str(model),'-b','PHYS'],check=True,capture_output=True,text=True,encoding='utf-8')
    found=re.search(r'm_surfacePropertyHashes\s*=\s*\[([^\]]*)\]',result.stdout,re.S)
    if not found:raise RuntimeError('Compiled model has no physical surface table')
    table=list(map(int,re.findall(r'\d+',found[1])));actual=set(table)
    expected={name:token(name) for name in expect}
    indices=Counter(int(n) for block in re.findall(r'm_Materials\s*=\s*\[([^\]]*)\]',result.stdout,re.S)
                    for n in re.findall(r'\d+',block))
    used=set(indices)
    material_counts={name:indices[table.index(value)] if value in table else 0 for name,value in expected.items()}
    valid=actual==set(expected.values()) and used==set(range(len(table)))
    report=dict(status='passed' if valid else 'failed',
                model=str(model),model_sha256=hashlib.sha256(Path(model).read_bytes()).hexdigest(),
                expected_surface_tokens=expected,compiled_surface_tokens=table,
                contact_material_counts=material_counts)
    if output:
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,indent=2)+'\n')
    if report['status']!='passed':raise RuntimeError('Physical surface table mismatch: '+str(report))
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path)
    parser.add_argument('--expect',nargs='+',required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();audit(args.model,args.expect,output=args.output)
