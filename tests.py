import unittest
import os
import tempfile
from assembler import UVBMAssembler

class TestUVBMAssembler(unittest.TestCase):

    def setUp(self):
        self.assembler = UVBMAssembler()

    def test_load_const(self):
        ir = self.assembler._load_const(['LOAD_CONST', '946', '133'])
        self.assertEqual(ir['A'], 3)
        self.assertEqual(ir['B'], 133)
        self.assertEqual(ir['C'], 946)
        self.assertIsNone(ir['D'])

    def test_read_mem(self):
        ir = self.assembler._read_mem(['READ_MEM', '649', '794'])
        self.assertEqual(ir['A'], 0)
        self.assertEqual(ir['B'], 794)
        self.assertEqual(ir['C'], 649)
        self.assertIsNone(ir['D'])

    def test_write_mem(self):
        ir = self.assembler._write_mem(['WRITE_MEM', '575', '841'])
        self.assertEqual(ir['A'], 5)
        self.assertEqual(ir['B'], 575)
        self.assertEqual(ir['C'], 841)
        self.assertIsNone(ir['D'])

    def test_min_op(self):
        ir = self.assembler._min_op(['MIN', '493', '333', '1003'])
        self.assertEqual(ir['A'], 7)
        self.assertEqual(ir['B'], 333)
        self.assertEqual(ir['C'], 1003)
        self.assertEqual(ir['D'], 493)

    def test_assemble_file(self):
        test_asm = """LOAD_CONST 946, 133
READ_MEM 649, 794
WRITE_MEM 841, 575
MIN 493, 333, 1003"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.asm') as f:
            f.write(test_asm)
            input_file = f.name

        output_file = input_file + '.bin'

        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            self.assembler.assemble(input_file, output_file, test_mode=True)
        finally:
            sys.stdout.close()
            sys.stdout = old_stdout

        expected_ir = [
            {'A': 3, 'B': 133, 'C': 946, 'D': None},
            {'A': 0, 'B': 794, 'C': 649, 'D': None},
            {'A': 5, 'B': 575, 'C': 841, 'D': None},
            {'A': 7, 'B': 333, 'C': 1003, 'D': 493}
        ]

        self.assertEqual(len(self.assembler.ir), len(expected_ir))
        for i, cmd in enumerate(self.assembler.ir):
            self.assertDictEqual(cmd, expected_ir[i])

        os.unlink(input_file)
        os.unlink(output_file)

if __name__ == '__main__':
    unittest.main()