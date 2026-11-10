"""Disabled: script-only VRAD retiling produced a corrupt atlas in-game.

Retained as an explicit failure for existing build instructions. Rebuild through
resourcecompiler so its generated packing inputs and script remain consistent.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from . import cs2_project as project
except ImportError:
    import cs2_project as project

ROOT=Path(__file__).resolve().parents[1]
MAPS=('trento_povo_campus','trento_povo_campus_winter')


def normalized(value):
    return str(value).replace('\\','/').casefold()


def select_job(processes, cs2, map_name):
    if map_name not in MAPS:raise ValueError('Unknown campus map')
    source=normalized(cs2/'content/csgo_addons/trento_povo/maps'/(map_name+'.vmap'))
    parents=[p for p in processes if p['Name'].casefold()=='resourcecompiler.exe'
             and source in normalized(p.get('CommandLine') or '')]
    if len(parents)!=1:raise RuntimeError('Requires exactly one compiler for the selected campus map')
    parent=parents[0]
    workers=[p for p in processes if p['Name'].casefold()=='vrad3.exe'
             and p['ParentProcessId']==parent['ProcessId']
             and 'maps/'+map_name+'.vmap' in normalized(p.get('CommandLine') or '')]
    if len(workers)!=1:raise RuntimeError('Requires exactly one matching lighting child')
    return parent,workers[0]


def recover(cs2, map_name, block_size, output):
    raise RuntimeError('Script-only VRAD recovery is disabled after native atlas corruption. '
                       'Recompile the map with resourcecompiler and its original generated settings.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cs2-root',type=Path)
    parser.add_argument('--map',dest='map_name',choices=MAPS,default=MAPS[0])
    parser.add_argument('--block-size',type=int,choices=(128,256,512,1024),default=256)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    cs2=project.discover_cs2_root(args.cs2_root)
    output=args.output or ROOT/'build/lighting-recovery'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    try:
        recover(cs2,args.map_name,args.block_size,output)
    except RuntimeError as error:
        parser.exit(2,str(error)+'\n')


if __name__=='__main__':main()
