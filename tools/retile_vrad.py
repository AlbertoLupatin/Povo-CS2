"""Reject script-only VRAD retiling, which corrupts the generated lightmap atlas.

The generated script and binary packing inputs form one bake configuration.
Changing only the script's block size is not a supported recovery operation.
"""
import argparse
import math
from pathlib import Path
import re


def retile(text, size=256):
    if size not in (128,256,512,1024):
        raise ValueError('Block size must be 128, 256, 512 or 1024')
    text=text.replace('\r\n','\n')
    image=re.search(r'(?m)^lightmap_image_gpu (\d+) (\d+) (\d+)$',text)
    if image is None:raise ValueError('Missing lightmap image declaration')
    width,height,old=map(int,image.groups())
    if size != old:
        raise ValueError('Script-only lightmap retiling is disabled: it can corrupt the atlas. '
                         'Regenerate the bake with resourcecompiler instead.')
    region=re.search(r'(?ms)^compute_all_lightmap_blocks:\n(.*?)^lightmap_free_memory',text)
    if region is None:raise ValueError('Missing bounded lightmap compute section')
    body=region[1]
    commands=list(re.finditer(r'(?m)^    lightmap_load_block_gpu lightmap_info.dat (\d+)\n'
                             r'    lightmap_compute_block_gpu ([^\n]+)\n',body))
    count=math.ceil(width/old)*math.ceil(height/old)
    if [int(m[1]) for m in commands]!=list(range(count)):
        raise ValueError('Unexpected original lightmap block sequence')
    parameters={m[2] for m in commands}
    if len(parameters)!=1:raise ValueError('Nonuniform sampling parameters')
    if ''.join(m[0] for m in commands)!=body[commands[0].start():commands[-1].end()]:
        raise ValueError('Unexpected commands between lightmap blocks')
    return text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('script',type=Path)
    parser.add_argument('--block-size',type=int,choices=(128,256,512,1024),default=256)
    args=parser.parse_args()
    original=args.script.read_text(encoding='utf-8')
    updated=retile(original,args.block_size)
    backup=args.script.with_suffix(args.script.suffix+'.before-retile')
    if not backup.exists():backup.write_text(original,encoding='utf-8')
    args.script.write_text(updated,encoding='utf-8')
    print(f'Validated unchanged block size in {args.script}; no retiling performed.')


if __name__=='__main__':main()
