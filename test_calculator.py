import unittest
from calculator import calculate, matches, subnet_page


class CalculatorTests(unittest.TestCase):
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
