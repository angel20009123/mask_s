"""IPv4 subnet and ACL wildcard calculations, independent of the UI."""
import ipaddress

MAX = 0xFFFFFFFF


def ipv4(value):
    try:
        return int(ipaddress.IPv4Address(value.strip()))
    except ipaddress.AddressValueError:
        raise ValueError("请输入有效的 IPv4 地址，例如 192.168.1.1") from None


def dotted(value):
    return str(ipaddress.IPv4Address(value))


def calculate(address, value, mode="CIDR 前缀"):
    address_int = ipv4(address)
    if mode == "CIDR 前缀":
        try:
            prefix = int(value.strip().removeprefix("/"))
        except ValueError:
            raise ValueError("CIDR 前缀必须是 0～32 的整数") from None
        if not 0 <= prefix <= 32:
            raise ValueError("CIDR 前缀必须在 0～32 之间")
        mask = (MAX << (32 - prefix)) & MAX
        wildcard = mask ^ MAX
    elif mode == "正掩码":
        mask = ipv4(value)
        wildcard = mask ^ MAX
        if wildcard & (wildcard + 1):
            raise ValueError("正掩码必须由连续的 1 和连续的 0 组成")
    else:
        wildcard = ipv4(value)
        mask = wildcard ^ MAX

    contiguous = wildcard & (wildcard + 1) == 0
    base = address_int & mask
    last = base | wildcard
    count = 1 << wildcard.bit_count()
    prefix = mask.bit_count() if contiguous else None
    result = {
        "正掩码": dotted(mask),
        "反掩码 / ACL 通配符": dotted(wildcard),
        "CIDR 前缀": f"/{prefix}" if contiguous else "非连续通配符，无单一 CIDR",
        "匹配地址数量": f"{count:,}",
        "网络地址" if contiguous else "最小匹配地址": dotted(base),
        "广播地址" if contiguous else "最大匹配地址": dotted(last),
    }
    if contiguous:
        first_host = base + 1 if prefix < 31 else base
        last_host = last - 1 if prefix < 31 else last
        result["可用地址范围"] = f"{dotted(first_host)} ～ {dotted(last_host)}"
        result["可用地址数量"] = f"{count - 2 if prefix < 31 else count:,}"
    result["ACL 地址与通配符"] = f"{dotted(base)} {dotted(wildcard)}"
    result["掩码（二进制）"] = ".".join(f"{int(n):08b}" for n in dotted(mask).split("."))
    result["通配符（二进制）"] = ".".join(f"{int(n):08b}" for n in dotted(wildcard).split("."))
    return result, base, mask


def matches(candidate, base, mask):
    return ipv4(candidate) & mask == base


def subnet_page(base, mask, offset=0, limit=128):
    """Minimal exact CIDR cover, paginated without enumerating all addresses."""
    wildcard = mask ^ MAX
    trailing = 0
    while trailing < 32 and wildcard & (1 << trailing):
        trailing += 1
    branches = [bit for bit in range(trailing, 32) if wildcard & (1 << bit)]
    total = 1 << len(branches)
    networks = []
    for index in range(offset, min(offset + limit, total)):
        network = base
        for digit, bit in enumerate(branches):
            if index & (1 << digit):
                network |= 1 << bit
        networks.append(ipaddress.IPv4Network((network, 32 - trailing)))
    return networks, total, trailing


def range_rules(start, end):
    """Exact minimal CIDR cover of an inclusive IPv4 interval (at most 62 rules)."""
    first, last = ipv4(start), ipv4(end)
    if first > last:
        raise ValueError("起始地址不能大于结束地址")
    return list(ipaddress.summarize_address_range(
        ipaddress.IPv4Address(first), ipaddress.IPv4Address(last)))
