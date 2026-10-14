import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tables import (TableEntry, cpu_to_offset, locate_unique, entry_bytes,
                    entry_length, EXAMPLE_ENTRY, RegistryError)
from validate import validate_registry
from ines import Rom

class TestAddressMap(unittest.TestCase):
    def test_switchable_window(self):
        self.assertEqual(cpu_to_offset(2, 0x8000), 2 * 0x4000)
        self.assertEqual(cpu_to_offset(2, 0xBFFF), 2 * 0x4000 + 0x3FFF)

    def test_fixed_bank_window(self):
        self.assertEqual(cpu_to_offset(7, 0xC000), 7 * 0x4000)
        self.assertEqual(cpu_to_offset(7, 0xD64F), 7 * 0x4000 + 0x164F)

    def test_wrong_window_raises(self):
        with self.assertRaises(RegistryError):
            cpu_to_offset(7, 0x8000)
        with self.assertRaises(RegistryError):
            cpu_to_offset(3, 0xC000)

class TestLocateUnique(unittest.TestCase):
    def test_unique_hit(self):
        self.assertEqual(locate_unique(bytes([1, 2, 3, 4, 5]), bytes([3, 4]), 't'), 2)

    def test_zero_or_multi_hit_raises(self):
        with self.assertRaises(RegistryError):
            locate_unique(bytes([1, 1, 1]), bytes([2]), 't')
        with self.assertRaises(RegistryError):
            locate_unique(bytes([1, 1, 1]), bytes([1, 1]), 't')

class TestEntryBytes(unittest.TestCase):
    def test_slices_by_kind(self):
        b0 = bytes(range(256)) + bytes(0x4000 - 256)
        rom = Rom({}, [b0] + [bytes(0x4000)] * 7)
        e = TableEntry('t', 0, 0x8004, 'palette', 4, 'x:1', 'test')
        self.assertEqual(entry_bytes(rom, e), bytes([4, 5, 6, 7]))
        self.assertEqual(entry_length(e), 4)

    def test_example_entry_shape(self):
        self.assertEqual(EXAMPLE_ENTRY.kind, 'palette')
        self.assertEqual(entry_length(EXAMPLE_ENTRY), 32)

class TestValidate(unittest.TestCase):
    def test_out_of_bank_reported(self):
        rom = Rom({}, [bytes(0x4000)] * 8)
        bad = TableEntry('tBad', 7, 0xFFF0, 'palette', 32, 'x:1', 'test')
        errors = validate_registry(rom, [bad])
        self.assertTrue(any('tBad' in e for e in errors))

    def test_ptr_table_roundtrip(self):
        b1 = bytearray(0x4000)
        b1[0x000:2] = bytes([0x00, 0x90])
        b1[0x1000:0x1005] = bytes([1, 0, 0, 0, 0])
        rom = Rom({}, [bytes(0x4000), bytes(b1)] + [bytes(0x4000)] * 6)
        ptr = TableEntry('tPtr', 1, 0x8000, 'ptr_table', 1, 'x:1', 'test')
        ms = TableEntry('tMs', 1, 0x9000, 'metasprite', 1, 'x:2', 'test')
        self.assertEqual(validate_registry(rom, [ptr, ms]), [])

    def test_ptr_table_dangling_reported(self):
        b1 = bytearray(0x4000)
        b1[0x000:2] = bytes([0x34, 0x92])  # 指向未登记的 $9234
        rom = Rom({}, [bytes(0x4000), bytes(b1)] + [bytes(0x4000)] * 6)
        ptr = TableEntry('tPtr', 1, 0x8000, 'ptr_table', 1, 'x:1', 'test')
        errors = validate_registry(rom, [ptr])
        self.assertTrue(any('0x9234' in e or '$9234' in e for e in errors))

    def test_out_of_range_bank_reported(self):
        rom = Rom({}, [bytes(0x4000)] * 8)
        for bad_bank in (8, -1):
            e = TableEntry('tBadBank', bad_bank, 0x8000, 'palette', 32, 'x:1', 'test')
            errors = validate_registry(rom, [e])
            self.assertTrue(any('tBadBank' in msg for msg in errors),
                            f'bank {bad_bank} not reported')

    def test_duplicate_name_reported(self):
        rom = Rom({}, [bytes(0x4000)] * 8)
        a = TableEntry('tDup', 7, 0xC000, 'palette', 4, 'x:1', 'test')
        b = TableEntry('tDup', 7, 0xC100, 'palette', 4, 'x:2', 'test')
        errors = validate_registry(rom, [a, b])
        self.assertTrue(any('tDup' in msg and 'duplicate' in msg for msg in errors))

if __name__ == '__main__':
    unittest.main()
