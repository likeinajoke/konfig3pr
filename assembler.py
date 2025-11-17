import sys
import struct

class UVBMAssembler:
    def __init__(self):
        self.commands = {
            'LOAD_CONST': self._load_const,
            'READ_MEM': self._read_mem,
            'WRITE_MEM': self._write_mem,
            'MIN': self._min_op
        }
        self.ir = []  # Промежуточное представление: список словарей

    def _load_const(self, parts):
        if len(parts) != 3:
            raise SyntaxError("LOAD_CONST expects 2 arguments: <addr_dest>, <const>")
        dest_addr = int(parts[1])
        const_val = int(parts[2])
        return {
            'A': 3,
            'B': const_val,
            'C': dest_addr,
            'D': None
        }

    def _read_mem(self, parts):
        if len(parts) != 3:
            raise SyntaxError("READ_MEM expects 2 arguments: <addr_dest>, <addr_src>")
        dest_addr = int(parts[1])
        src_addr = int(parts[2])
        return {
            'A': 0,
            'B': src_addr,
            'C': dest_addr,
            'D': None
        }

    def _write_mem(self, parts):
        if len(parts) != 3:
            raise SyntaxError("WRITE_MEM expects 2 arguments: <addr_src>, <addr_dest>")
        src_addr = int(parts[1])
        dest_addr = int(parts[2])
        return {
            'A': 5,
            'B': src_addr,
            'C': dest_addr,
            'D': None
        }

    def _min_op(self, parts):
        if len(parts) != 4:
            raise SyntaxError("MIN expects 3 arguments: <addr_result>, <addr_op1>, <addr_op2>")
        result_addr = int(parts[1])
        op1_addr = int(parts[2])
        op2_addr = int(parts[3])
        return {
            'A': 7,
            'B': op1_addr,
            'C': op2_addr,
            'D': result_addr
        }

    def parse_line(self, line):
        line = line.strip()
        if not line or line.startswith(';'):
            return None
        parts = line.split(',')
        cmd_name = parts[0].strip().upper()
        if cmd_name not in self.commands:
            raise SyntaxError(f"Unknown command: {cmd_name}")
        return self.commands[cmd_name](parts)

    def assemble(self, input_path, output_path, test_mode=False):
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        self.ir.clear()
        for i, line in enumerate(lines, 1):
            try:
                cmd_ir = self.parse_line(line)
                if cmd_ir is not None:
                    self.ir.append(cmd_ir)
            except Exception as e:
                print(f"Error at line {i}: {e}")
                sys.exit(1)

        if test_mode:
            self._print_ir()

        # Генерация бинарного файла
        with open(output_path, 'wb') as f:
            for cmd in self.ir:
                # Кодируем команду в 11 байт
                # Байт 0: A (3 бита в младших битах)
                data = bytearray(11)
                data[0] = cmd['A'] & 0x07

                # B: 32-битное little-endian
                b_bytes = struct.pack('<I', cmd['B'])
                data[1:5] = b_bytes

                # C: 32-битное little-endian
                c_bytes = struct.pack('<I', cmd['C'])
                data[5:9] = c_bytes

                # D: 16-битное little-endian (если есть, иначе 0)
                d_val = cmd['D'] if cmd['D'] is not None else 0
                d_bytes = struct.pack('<H', d_val)
                data[9:11] = d_bytes

                f.write(data)

    def _print_ir(self):
        print("=== Internal Representation ===")
        for i, cmd in enumerate(self.ir, 1):
            print(f"{i:2d}: A={cmd['A']}, B={cmd['B']}, C={cmd['C']}, D={cmd['D']}")
        print("===============================")


def main():
    if len(sys.argv) < 3:
        print("Usage: python assembler.py <input_file> <output_file> [--test]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    test_mode = '--test' in sys.argv

    assembler = UVBMAssembler()
    assembler.assemble(input_path, output_path, test_mode)


if __name__ == '__main__':
    main()