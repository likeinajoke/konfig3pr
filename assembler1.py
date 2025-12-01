import argparse
import re
import json
from typing import List, Dict, Optional

# --------------------
# Config: supported mnemonics and their A codes
# --------------------
MNEMONICS = {
    'LOAD_CONST': 3,  # load constant into memory at address
    'READ': 0,        # read from memory
    'WRITE': 5,       # write to memory
    'MIN': 7,         # binary min operation
    # Дополнительные инструкции можно добавить сюда
}

# --------------------
# Parsing helpers
# --------------------
_token_re = re.compile(r"\s*(?P<mnemonic>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<rest>.*)$")


def parse_number(tok: str) -> int:
    tok = tok.strip()
    if not tok:
        raise ValueError("Empty numeric token")
    if tok.lower().startswith('0x'):
        return int(tok, 16)
    return int(tok, 10)


def tokenize_operands(ops_str: str) -> List[str]:
    # Splits operands by commas, trims whitespace
    parts = [p.strip() for p in ops_str.split(',') if p.strip() != '']
    return parts


def assemble_line(line: str, line_no: int = 0) -> Optional[Dict]:
    """Parse one assembly source line and return an IR dict or None.

    Supported forms:
      LOAD_CONST <CONST>, <ADDRESS>
      READ <B_addr>, <C_addr>
      WRITE <B_addr>, <C_addr>
      MIN <B_addr>, <C_addr>, <D_addr>

    Comments start with ';' or '#'. Empty lines are ignored.
    """
    # remove comments
    code = re.split(r'[;#]', line, 1)[0].strip()
    if not code:
        return None
    m = _token_re.match(code)
    if not m:
        raise ValueError(f"Syntax error on line {line_no}: {line}")
    mnemonic = m.group('mnemonic').upper()
    rest = m.group('rest').strip()
    if mnemonic not in MNEMONICS:
        raise ValueError(f"Unknown mnemonic '{mnemonic}' on line {line_no}")
    A = MNEMONICS[mnemonic]
    operands = tokenize_operands(rest) if rest else []
    instr: Dict = {'mnemonic': mnemonic, 'A': A}

    # Instruction-specific operand handling
    if mnemonic == 'LOAD_CONST':
        # Correct format: LOAD_CONST CONST, ADDRESS
        if len(operands) != 2:
            raise ValueError(f"LOAD_CONST expects 2 operands (CONST, ADDRESS) on line {line_no}")
        instr['B'] = parse_number(operands[0])   # CONST -> field B
        instr['C'] = parse_number(operands[1])   # ADDRESS -> field C
    elif mnemonic == 'READ':
        if len(operands) != 2:
            raise ValueError(f"READ expects 2 operands (B_addr, C_addr) on line {line_no}")
        instr['B'] = parse_number(operands[0])
        instr['C'] = parse_number(operands[1])
    elif mnemonic == 'WRITE':
        if len(operands) != 2:
            raise ValueError(f"WRITE expects 2 operands (B_addr, C_addr) on line {line_no}")
        instr['B'] = parse_number(operands[0])
        instr['C'] = parse_number(operands[1])
    elif mnemonic == 'MIN':
        if len(operands) != 3:
            raise ValueError(f"MIN expects 3 operands (B, C, D) on line {line_no}")
        instr['B'] = parse_number(operands[0])
        instr['C'] = parse_number(operands[1])
        instr['D'] = parse_number(operands[2])
    else:
        instr['operands'] = operands
    return instr


def assemble_text(text: str) -> List[Dict]:
    """Assemble whole program text to IR (list of instruction dicts)."""
    lines = text.splitlines()
    ir: List[Dict] = []
    for i, line in enumerate(lines, start=1):
        parsed = assemble_line(line, line_no=i)
        if parsed:
            ir.append(parsed)
    return ir


def pretty_print_ir(ir: List[Dict]):
    """Print IR in human-readable format (fields and values)."""
    for i, ins in enumerate(ir, start=1):
        mnemonic = ins.get('mnemonic', '?')
        A = ins.get('A', 0)
        print(f"Instruction {i}: {mnemonic}")
        print(f"  A: {A} (0x{A:X})")
        for key in ('B', 'C', 'D', 'CONST'):
            if key in ins:
                val = ins[key]
                print(f"  {key}: {val} (0x{val:X})")
        print()


# --------------------
# File utilities
# --------------------

def load_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def save_json_ir(ir: List[Dict], path: str):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(ir, f, indent=2, ensure_ascii=False)


# --------------------
# CLI entrypoint
# --------------------

def main():
    parser = argparse.ArgumentParser(description='UVM assembler — stage 1 (IR output)')
    parser.add_argument('src', help='source assembly file (text)')
    parser.add_argument('--out', help='Optional output file for JSON IR', default=None)
    parser.add_argument('--test', action='store_true', help='print IR to stdout (test mode)')
    parser.add_argument('--emit-json', action='store_true', help='emit IR as JSON to output file')
    args = parser.parse_args()

    src_text = load_file(args.src)
    ir = assemble_text(src_text)

    if args.test:
        print('=== Assembled IR (test mode) ===\n')
        pretty_print_ir(ir)

    if args.emit_json:
        save_json_ir(ir, args.out)
        print(f'IR saved as JSON to {args.out}')
    else:
        print('Note: stage 1 does not write final binary. Use --emit-json to save IR to out file')


if __name__ == '__main__':
    main()

