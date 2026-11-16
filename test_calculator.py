import unittest
from calculator import calculate, matches, subnet_page, range_rules, multiple_range_rules


class CalculatorTests(unittest.TestCase):
    def test_multiple_ranges_keep_gaps(self):
        networks, intervals = multiple_range_rules([("192.168.1.0", "192.168.1.255"), ("192.168.3.0", "192.168.3.255")])
        self.assertEqual([str(n) for n in networks], ["192.168.1.0/24", "192.168.3.0/24"])
        self.assertEqual(len(intervals), 2)

    def test_multiple_ranges_merge_overlap_duplicates_and_adjacency(self):
        networks, intervals = multiple_range_rules([("10.0.0.128", "10.0.0.255"), ("10.0.0.0", "10.0.0.127"), ("10.0.0.50", "10.0.0.180"), ("10.0.0.0", "10.0.0.127")])
        self.assertEqual([str(n) for n in networks], ["10.0.0.0/24"])
        self.assertEqual(len(intervals), 1)
        self.assertEqual(sum(n.num_addresses for n in networks), 256)

    def test_multiple_ranges_reject_empty_and_identify_invalid_condition(self):
        with self.assertRaisesRegex(ValueError, "至少添加"):
            multiple_range_rules([])
        with self.assertRaisesRegex(ValueError, "条件 2"):
            multiple_range_rules([("10.0.0.1", "10.0.0.1"), ("bad", "10.0.0.2")])

    def test_multiple_ranges_exact_union(self):
        import random
        randomizer = random.Random(42)
        for _ in range(100):
            ranges = [sorted(randomizer.sample(range(256), 2)) for _ in range(8)]
            expected = {0x0A000000 + value for start, end in ranges for value in range(start, end + 1)}
            networks, _ = multiple_range_rules([(f"10.0.0.{start}", f"10.0.0.{end}") for start, end in ranges])
            self.assertEqual({int(ip) for n in networks for ip in n}, expected)

    def test_aligned_range(self):
        rules = range_rules("192.168.1.0", "192.168.1.255")
        self.assertEqual([str(n) for n in rules], ["192.168.1.0/24"])
        self.assertEqual(str(rules[0].hostmask), "0.0.0.255")

    def test_unaligned_range_exact_coverage(self):
        rules = range_rules("192.168.1.10", "192.168.1.100")
        self.assertGreater(len(rules), 1)
        self.assertEqual(sum(n.num_addresses for n in rules), 91)
        covered = {int(ip) for n in rules for ip in n}
        self.assertEqual(covered, set(range(0xC0A8010A, 0xC0A80165)))

    def test_range_boundaries(self):
        for start, end, expected in (("0.0.0.0", "255.255.255.255", ["0.0.0.0/0"]), ("255.255.255.255", "255.255.255.255", ["255.255.255.255/32"]), ("192.168.1.255", "192.168.2.0", ["192.168.1.255/32", "192.168.2.0/32"])):
            with self.subTest(start=start):
                self.assertEqual([str(n) for n in range_rules(start, end)], expected)

    def test_invalid_ranges(self):
        for start, end in (("10.0.0.2", "10.0.0.1"), ("bad", "10.0.0.1"), ("10.0.0.1", "256.0.0.1")):
            with self.subTest(start=start), self.assertRaises(ValueError):
                range_rules(start, end)

    def test_exact_subnet_decomposition(self):
        _, base, mask = calculate("192.168.0.0", "0.0.5.255", "反掩码 / ACL 通配符")
        networks, total, trailing = subnet_page(base, mask)
        self.assertEqual([str(n) for n in networks], ["192.168.0.0/23", "192.168.4.0/23"])
        self.assertEqual((total, trailing), (2, 9))
        self.assertEqual(sum(n.num_addresses for n in networks), 1024)

    def test_large_decomposition_is_paginated(self):
        networks, total, trailing = subnet_page(0, 1, 128, 3)
        self.assertEqual(total, 2 ** 31)
        self.assertEqual(trailing, 0)
        self.assertEqual([str(n) for n in networks], ["0.0.1.0/32", "0.0.1.2/32", "0.0.1.4/32"])

    def test_subnet_cover_matches_acl_exhaustively(self):
        for wildcard in range(256):
            base = 0xC0A801AA & (0xFFFFFFFF ^ wildcard)
            mask = 0xFFFFFFFF ^ wildcard
            networks, total, _ = subnet_page(base, mask, limit=256)
            self.assertEqual(len(networks), total)
            covered = {int(ip) for network in networks for ip in network}
            expected = {0xC0A80100 + x for x in range(256) if (0xC0A80100 + x) & mask == base}
            self.assertEqual(covered, expected)

    def test_standard_subnet(self):
        result, _, _ = calculate("192.168.1.10", "24")
        self.assertEqual(result["网络地址"], "192.168.1.0")
        self.assertEqual(result["广播地址"], "192.168.1.255")
        self.assertEqual(result["可用地址数量"], "254")
        self.assertEqual(result["反掩码 / ACL 通配符"], "0.0.0.255")

    def test_conversion_modes_agree(self):
        expected = calculate("10.20.30.40", "20")[0]
        self.assertEqual(calculate("10.20.30.40", "255.255.240.0", "正掩码")[0], expected)
        self.assertEqual(calculate("10.20.30.40", "0.0.15.255", "反掩码 / ACL 通配符")[0], expected)

    def test_noncontiguous_acl(self):
        result, base, mask = calculate("192.168.0.0", "0.0.5.255", "反掩码 / ACL 通配符")
        self.assertEqual(result["匹配地址数量"], "1,024")
        self.assertTrue(matches("192.168.4.100", base, mask))
        self.assertTrue(matches("192.168.5.255", base, mask))
        self.assertFalse(matches("192.168.2.100", base, mask))
        self.assertFalse(matches("192.169.4.100", base, mask))

    def test_boundary_prefixes(self):
        for prefix, count in ((0, "4,294,967,294"), (31, "2"), (32, "1")):
            with self.subTest(prefix=prefix):
                self.assertEqual(calculate("10.0.0.1", str(prefix))[0]["可用地址数量"], count)

    def test_invalid_inputs(self):
        for address, value, mode in (("999.0.0.1", "24", "CIDR 前缀"), ("10.0.0.1", "33", "CIDR 前缀"), ("10.0.0.1", "255.0.255.0", "正掩码")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate(address, value, mode)


if __name__ == "__main__":
    unittest.main()
