#!/usr/bin/env python3
"""Compare allocated ELF32 bytes and an object-level gzip size proxy."""
from pathlib import Path
import argparse
import gzip
import json
import struct


def sections(path, compress=True):
    data=path.read_bytes()
    if data[:6]!=b'\x7fELF\x01\x01' or struct.unpack_from('<H',data,18)[0]!=40:
        raise ValueError(f'{path}: expected arm ELF32 LE')
    shoff=struct.unpack_from('<I',data,32)[0]
    length,n,strings=struct.unpack_from('<HHH',data,46)
    if length!=40 or not n:
        raise ValueError(f'{path}: unsupported section table')
    headers=[struct.unpack_from('<10I',data,shoff+i*length) for i in range(n)]
    names=headers[strings]
    table=data[names[4]:names[4]+names[5]]
    initialized=zero=code=gcov_bytes=0
    payload=[]
    for name,typ,flags,_,offset,size,*_ in headers:
        if not flags&2:
            continue
        s=table[name:].partition(b'\0')[0].decode()
        if 'gcov' in s:
            gcov_bytes+=size
        if flags&4:
            code+=size
        if typ==8:
            zero+=size
        else:
            initialized+=size
            if compress:
                payload.append(data[offset:offset+size])
    result=dict(initialized=initialized, zero=zero, code=code,resident=initialized+zero,gcov_named_bytes=gcov_bytes)
    if compress:
        result["gzip_proxy"]=len(gzip.compress(b''.join(payload),compresslevel=9,mtime=0))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('baseline','gcov','vmlinux','zimage','output'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('object',nargs='+')
    args=p.parse_args()
    objects={}
    keys=('initialized','zero','code','resident','gzip_proxy')
    total={v:dict.fromkeys(keys,0) for v in ('base','gcov')}
    for obj in args.object:
        row={n:sections(d/obj) for n,d in [('base',args.baseline),('gcov',args.gcov)]}
        row['gcno_bytes']=(args.gcov/(obj.removesuffix('.o')+'.gcno')).stat().st_size
        objects[obj]=row
        for variant in ('base','gcov'):
            for metric in keys:
                total[variant][metric]+=row[variant][metric]
    kernel=sections(args.vmlinux,compress=False)
    base_z=args.zimage.stat().st_size
    disk_ratio=total['gcov']['gzip_proxy']/total['base']['gzip_proxy']-1
    ram_ratio=total['gcov']['resident']/total['base']['resident']-1
    availability=1374208
    replace=15031504
    cluster=2048
    floor=524288
    rounded=(replace+cluster-1)//cluster*cluster
    ceiling=(availability+rounded-floor-cluster)//cluster*cluster
    result=dict(objects=objects,sample_totals=total,kbase_linked_alloc=kernel,kbase_zimage_bytes=base_z,
                increase_gzip_proxy=disk_ratio,increase_resident_proxy=ram_ratio,
                representative_projection=dict(zimage_bytes=round(base_z*(1+disk_ratio)),
                                               resident_growth_bytes=round(kernel['resident']*ram_ratio)),
                boot_a=dict(free_bytes=availability,afdo_zimage_bytes=replace,cluster_bytes=cluster,
                            reserve_bytes=floor,tryboot_temp_cluster_bytes=cluster,
                            max_replacement_zimage_bytes=ceiling))
    args.output.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    main()
