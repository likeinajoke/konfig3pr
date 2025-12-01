import argparse
import re
import json
from typing import List, Dict, Optional

MNEMONICS = {
    'LOAD_CONST': 3,  # load constant into memory at address
    'READ': 0,        # read from memory
    'WRITE': 5,       # write to memory
    'MIN': 7,         # binary min operation
    # Дополнительные инструкции можно добавить сюда
}


_token_re = re.compile(r"\s*(?P<mnemonic>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<rest>.*)$")


def parse_number(tok: str) -> int:
    tok = tok.strip()
    if not tok:
        raise ValueError("Empty numeric token")
    if tok.lower().startswith('0x'):
        return int(tok, 16)
    return int(tok, 10)

def parse_expr(expr: str) -> Dict:
    expr = expr.strip()
    m = re.match(r"min\((.+),(.+)\)$", expr, re.I)
    if m:
        return {'type': 'min', 'left': parse_expr(m.group(1)), 'right': parse_expr(m.group(2))}
    m = re.match(r"mem\[(.+)\]$", expr, re.I)
    if m:
        return {'type': 'mem_load', 'addr': parse_expr(m.group(1))}
    if re.match(r"^(0x[0-9a-fA-F]+|\d+)$", expr):
        return {'type': 'number', 'value': parse_number(expr)}
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", expr):
        return {'type': 'addr', 'name': expr}
    raise ValueError(f"Невозможно разобрать выражение: {expr}")

var_offset: Dict[str, int] = {}
next_addr = 100

def alloc_addr(name: str) -> int:
    global next_addr
    if name not in var_offset:
        var_offset[name] = next_addr
        next_addr += 1
    return var_offset[name]

def compile_expr(expr: Dict, ir: List[Dict]) -> int:
    t = expr['type']
    if t == 'number':
        target = alloc_addr(f"#const_{expr['value']}")
        ir.append({'mnemonic': 'LOAD_CONST','A': MNEMONICS['LOAD_CONST'],'B': expr['value'],'C': target})
        return target
    if t == 'addr':
        return alloc_addr(expr['name'])
    if t == 'mem_load':
        addr = compile_expr(expr['addr'], ir)
        dest = alloc_addr(f"#tmp_read_{addr}")
        ir.append({'mnemonic': 'READ','A': MNEMONICS['READ'],'B': addr,'C': dest})
        return dest
    if t == 'min':
        left = compile_expr(expr['left'], ir)
        right = compile_expr(expr['right'], ir)
        dest = alloc_addr(f"#tmp_min_{left}_{right}")
        ir.append({'mnemonic': 'MIN','A': MNEMONICS['MIN'],'B': left,'C': right,'D': dest})
        return dest
    raise ValueError(f"Неизвестный тип выражения: {t}")

def compile_assignment(line: str, ir: List[Dict]):
    left, right = [s.strip() for s in line.split('=', 1)]
    if left.startswith('mem['):
        m = re.match(r"mem\[(.+)\]$", left)
        addr_expr = parse_expr(m.group(1))
        dest = compile_expr(addr_expr, ir)
    else:
        dest = alloc_addr(left)
    src = compile_expr(parse_expr(right), ir)
    ir.append({'mnemonic': 'WRITE','A': MNEMONICS['WRITE'],'B': src,'C': dest})

def tokenize_operands(ops_str: str) -> List[str]:
    # Splits operands by commas, trims whitespace
    parts = [p.strip() for p in ops_str.split(',') if p.strip() != '']
    return parts


def assemble_text(text: str) -> List[Dict]:
    ir: List[Dict] = []
    for line in text.splitlines():
        code = re.split(r'[;#]', line)[0].strip()
        if not code:
            continue
        if '=' in code:
            compile_assignment(code, ir)
        else:
            raise ValueError(f"Строка не является присваиванием: {line}")
    return ir


def pretty_print_ir(ir: List[Dict]):
    for i, ins in enumerate(ir, 1):
        print(f"Instruction {i}: {ins['mnemonic']}")
        for k, v in ins.items():
            if k != 'mnemonic':
                print(f" {k}: {v}")
        print()

def main():
    parser = argparse.ArgumentParser(description='UVM assembler — stage 1 (IR output)')
    parser.add_argument('src', help='source assembly file (text)')
    parser.add_argument('--out', help='Optional output file for JSON IR', default=None)
    parser.add_argument('--test', action='store_true', help='print IR to stdout (test mode)')
    parser.add_argument('--emit-json', action='store_true', help='emit IR as JSON to output file')
    args = parser.parse_args()

    text = open(args.src).read()
    ir = assemble_text(text)

    if args.test:
        pretty_print_ir(ir)

    if args.emit_json and args.out:
        with open(args.out, 'w') as f:
            json.dump(ir, f, indent=2)

if __name__ == '__main__':
    main()

