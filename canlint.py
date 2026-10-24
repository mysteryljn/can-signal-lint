#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def _bits(start,length):
    return set(range(start,start+length))

def lint(definition):
    errors=[]
    frames=definition.get("frames",[])
    ids={}
    for index,frame in enumerate(frames):
        prefix=f"frames[{index}]"; fid=frame.get("id"); name=frame.get("name","<unnamed>"); dlc=frame.get("dlc")
        if not isinstance(fid,int) or not 0<=fid<=0x1FFFFFFF:
            errors.append(f"{prefix}: invalid CAN id")
        elif fid in ids:
            errors.append(f"{prefix}: duplicate CAN id {fid} (also {ids[fid]})")
        else: ids[fid]=name
        if not isinstance(dlc,int) or not 0<=dlc<=64:
            errors.append(f"{prefix}: DLC must be an integer from 0 to 64"); dlc=0
        used={}; names=set()
        for sindex,signal in enumerate(frame.get("signals",[])):
            sp=f"{prefix}.signals[{sindex}]"; sname=signal.get("name"); start=signal.get("start_bit"); length=signal.get("length"); order=signal.get("byte_order","little")
            if not isinstance(sname,str) or not sname.strip(): errors.append(f"{sp}: signal name is required")
            elif sname in names: errors.append(f"{sp}: duplicate signal name {sname}")
            names.add(sname)
            if order not in ("little","big"): errors.append(f"{sp}: byte_order must be little or big")
            if not isinstance(start,int) or not isinstance(length,int) or length<=0:
                errors.append(f"{sp}: start_bit and positive length are required"); continue
            if start<0 or start+length>dlc*8:
                errors.append(f"{sp}: signal {sname} exceeds {dlc}-byte payload"); continue
            for bit in _bits(start,length):
                if bit in used: errors.append(f"{sp}: signal {sname} overlaps {used[bit]} at bit {bit}")
                else: used[bit]=sname
            factor=signal.get("factor",1)
            if not isinstance(factor,(int,float)) or factor==0: errors.append(f"{sp}: factor must be a non-zero number")
    return errors

def main(argv=None):
    parser=argparse.ArgumentParser(description="Lint a CAN network JSON definition"); parser.add_argument("definition",type=Path); args=parser.parse_args(argv)
    try: errors=lint(json.loads(args.definition.read_text(encoding="utf-8")))
    except (OSError,json.JSONDecodeError) as exc: print(f"error: {exc}"); return 2
    if errors: print("\n".join(f"ERROR {e}" for e in errors)); return 1
    print("OK: CAN definition passed"); return 0

if __name__=="__main__": raise SystemExit(main())
