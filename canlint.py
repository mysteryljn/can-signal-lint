#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path

VALID_DLC_LENGTHS = tuple(range(9)) + (12, 16, 20, 24, 32, 48, 64)

def _bits(start,length):
    return set(range(start,start+length))

def _signal_bits(start, length, order):
    """Return payload bit positions occupied by a signal.

    Little-endian (Intel) signals use consecutive bit positions.  In the
    Motorola/DBC representation a signal starts at its most-significant bit;
    after bit 0 the next position is the most-significant bit of the next
    byte (for example, 7, 6, ..., 0, 15, 14, ...).
    """
    if order != "big":
        return list(range(start, start + length))
    bits = []
    bit = start
    for _ in range(length):
        bits.append(bit)
        bit = bit + 15 if bit % 8 == 0 else bit - 1
    return bits

def lint(definition):
    errors=[]
    if not isinstance(definition, dict):
        return ["definition: top-level JSON object is required"]
    frames=definition.get("frames",[])
    if not isinstance(frames, list):
        return ["frames: must be a list"]
    ids={}
    for index,frame in enumerate(frames):
        prefix=f"frames[{index}]"
        if not isinstance(frame, dict):
            errors.append(f"{prefix}: frame must be an object")
            continue
        fid=frame.get("id"); name=frame.get("name","<unnamed>"); dlc=frame.get("dlc")
        # ``bool`` is a subclass of ``int`` in Python.  Accepting it here
        # would silently turn JSON true/false into CAN IDs 1/0.
        if type(fid) is not int or not 0<=fid<=0x1FFFFFFF:
            errors.append(f"{prefix}: invalid CAN id")
        elif fid in ids:
            errors.append(f"{prefix}: duplicate CAN id {fid} (also {ids[fid]})")
        else: ids[fid]=name
        if type(dlc) is not int or dlc not in VALID_DLC_LENGTHS:
            errors.append(f"{prefix}: DLC must be a valid CAN payload length (0-8, 12, 16, 20, 24, 32, 48, or 64 bytes)"); dlc=0
        used={}; names=set()
        signals=frame.get("signals",[])
        if not isinstance(signals, list):
            errors.append(f"{prefix}.signals: must be a list")
            continue
        for sindex,signal in enumerate(signals):
            sp=f"{prefix}.signals[{sindex}]"
            if not isinstance(signal, dict):
                errors.append(f"{sp}: signal must be an object")
                continue
            sname=signal.get("name"); start=signal.get("start_bit"); length=signal.get("length"); order=signal.get("byte_order","little")
            if not isinstance(sname,str) or not sname.strip(): errors.append(f"{sp}: signal name is required")
            elif sname in names: errors.append(f"{sp}: duplicate signal name {sname}")
            names.add(sname)
            if order not in ("little","big"): errors.append(f"{sp}: byte_order must be little or big")
            # Bit positions and lengths must be JSON numbers, not booleans;
            # Python otherwise treats True/False as 1/0.
            if type(start) is not int or type(length) is not int or length<=0:
                errors.append(f"{sp}: start_bit and positive length are required"); continue
            # A signal cannot occupy more bits than the frame payload.  Check
            # this before expanding the bit list so a malformed definition
            # cannot force an unnecessarily large allocation/loop in CI.
            if length > dlc * 8:
                errors.append(f"{sp}: signal {sname} exceeds {dlc}-byte payload"); continue
            signal_bits = _signal_bits(start, length, order)
            if start<0 or any(bit < 0 or bit >= dlc*8 for bit in signal_bits):
                errors.append(f"{sp}: signal {sname} exceeds {dlc}-byte payload"); continue
            for bit in signal_bits:
                if bit in used: errors.append(f"{sp}: signal {sname} overlaps {used[bit]} at bit {bit}")
                else: used[bit]=sname
            factor=signal.get("factor",1)
            # Python's bool is an int subclass, and json.loads accepts the
            # non-standard NaN/Infinity constants by default.  Neither is a
            # meaningful physical scaling factor and allowing them to pass
            # can poison generated decoders or calibration calculations.
            invalid_factor = (
                isinstance(factor, bool)
                or not isinstance(factor, (int, float))
                or (isinstance(factor, float) and not math.isfinite(factor))
                or factor == 0
            )
            if invalid_factor: errors.append(f"{sp}: factor must be a finite non-zero number")
    return errors

def main(argv=None):
    parser=argparse.ArgumentParser(description="Lint a CAN network JSON definition"); parser.add_argument("definition",type=Path); args=parser.parse_args(argv)
    try: errors=lint(json.loads(args.definition.read_text(encoding="utf-8")))
    except (OSError,json.JSONDecodeError) as exc: print(f"error: {exc}"); return 2
    if errors: print("\n".join(f"ERROR {e}" for e in errors)); return 1
    print("OK: CAN definition passed"); return 0

if __name__=="__main__": raise SystemExit(main())
