"""Mask Studio — a dependency-free Windows desktop calculator."""
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys
from calculator import calculate, matches, subnet_page
from version import __version__


class App:
    def __init__(self, root):
        self.root = root
        self.page_offset = 0
        self.last_key = None
        assets = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets"
        if (assets / "mask-studio.ico").exists():
            root.iconbitmap(str(assets / "mask-studio.ico"))
        root.title(f"Mask Studio v{__version__} · IPv4 掩码与 ACL 计算器")
        root.geometry("1040x940")
        root.minsize(940, 820)
        root.configure(bg="#eef2f7")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#eef2f7")
        style.configure("TLabel", background="#eef2f7", foreground="#182a43", font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 24, "bold"))
        style.configure("Sub.TLabel", foreground="#61718a")
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=8)
        style.configure("Accent.TButton", background="#2563eb", foreground="white")
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])
        style.configure("Treeview", font=("Microsoft YaHei UI", 10), rowheight=32, background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))

        frame = ttk.Frame(root, padding=28)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Mask Studio", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text="IPv4 网络工具  /  正掩码 · 反掩码 · ACL 通配符", style="Sub.TLabel").pack(anchor="w", pady=(3, 20))
        form = ttk.Frame(frame)
        form.pack(fill="x")
        self.address = tk.StringVar(value="192.168.1.10")
        self.mode = tk.StringVar(value="CIDR 前缀")
        self.value = tk.StringVar(value="24")
        self.candidate = tk.StringVar(value="192.168.1.100")
        for col, title in enumerate(("IPv4 地址", "输入类型", "掩码 / 前缀值")):
            ttk.Label(form, text=title).grid(row=0, column=col, sticky="w", pady=(0, 6))
            form.columnconfigure(col, weight=1)
        ttk.Entry(form, textvariable=self.address, font=("Consolas", 13)).grid(row=1, column=0, sticky="ew", padx=(0, 12), ipady=6)
        combo = ttk.Combobox(form, textvariable=self.mode, values=("CIDR 前缀", "正掩码", "反掩码 / ACL 通配符"), state="readonly", font=("Microsoft YaHei UI", 10))
        combo.grid(row=1, column=1, sticky="ew", padx=(0, 12), ipady=6)
        combo.bind("<<ComboboxSelected>>", self.change_mode)
        ttk.Entry(form, textvariable=self.value, font=("Consolas", 13)).grid(row=1, column=2, sticky="ew", ipady=6)
        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=14)
        ttk.Button(actions, text="计算结果", style="Accent.TButton", command=self.run).pack(side="left")
        ttk.Button(actions, text="复制结果", command=self.copy).pack(side="left", padx=10)
        ttk.Button(actions, text="载入非连续 ACL 示例", command=self.example).pack(side="right")
        self.status = tk.StringVar()
        ttk.Label(frame, textvariable=self.status, wraplength=840).pack(anchor="w", pady=(0, 10))
        self.bits = tk.Canvas(frame, height=94, bg="#eef2f7", highlightthickness=0)
        self.bits.pack(fill="x", pady=(0, 10))
        self.bits.bind("<Configure>", lambda _: self.draw_bits() if hasattr(self, "current") else None)
        self.notebook = ttk.Notebook(frame)
        self.notebook.pack(fill="both", expand=True)
        overview = ttk.Frame(self.notebook)
        subnet_panel = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(overview, text="  计算总览  ")
        self.notebook.add(subnet_panel, text="  子网层级与地址范围  ")
        self.tree = ttk.Treeview(overview, columns=("item", "value"), show="headings", height=10)
        self.tree.heading("item", text="计算项目", anchor="w")
        self.tree.heading("value", text="结果", anchor="w")
        self.tree.column("item", width=220, minwidth=200, stretch=False)
        self.tree.column("value", width=580, minwidth=480)
        self.tree.pack(fill="both", expand=True)
        for tag, color in (("network", "#e7efff"), ("wildcard", "#f0eaff"), ("range", "#e6f5ee")):
            self.tree.tag_configure(tag, background=color)
        self.subnet_summary = tk.StringVar()
        ttk.Label(subnet_panel, textvariable=self.subnet_summary).pack(anchor="w", pady=(0, 8))
        table = ttk.Frame(subnet_panel)
        table.pack(fill="both", expand=True)
        self.subnets = ttk.Treeview(table, columns=("range", "count"), height=8)
        self.subnets.heading("#0", text="地址层级 / CIDR 子网", anchor="w")
        self.subnets.heading("range", text="匹配地址范围（含首尾）", anchor="w")
        self.subnets.heading("count", text="地址数量", anchor="w")
        self.subnets.column("#0", width=290)
        self.subnets.column("range", width=380)
        self.subnets.column("count", width=110)
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.subnets.yview)
        self.subnets.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.subnets.pack(fill="both", expand=True)
        self.subnets.tag_configure("group", background="#dce7f7", foreground="#183d70", font=("Microsoft YaHei UI", 10, "bold"))
        self.subnets.tag_configure("even", background="#eef4ff", foreground="#244b86")
        self.subnets.tag_configure("odd", background="#e9f7f2", foreground="#18654e")
        pager = ttk.Frame(subnet_panel)
        pager.pack(fill="x", pady=(8, 0))
        self.prev = ttk.Button(pager, text="上一页", command=lambda: self.move_page(-128))
        self.prev.pack(side="left")
        self.next = ttk.Button(pager, text="下一页", command=lambda: self.move_page(128))
        self.next.pack(side="left", padx=8)
        ttk.Label(pager, text="精确 CIDR 分解 · 每页最多 128 个子网", style="Sub.TLabel").pack(side="right")
        check = ttk.Frame(frame)
        check.pack(fill="x", pady=(16, 6))
        ttk.Label(check, text="ACL 匹配检查").pack(side="left", padx=(0, 12))
        ttk.Entry(check, textvariable=self.candidate, font=("Consolas", 12)).pack(side="left", fill="x", expand=True, ipady=5)
        ttk.Button(check, text="检查地址", command=self.check).pack(side="left", padx=(12, 0))
        self.check_status = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.check_status).pack(anchor="w")
        ttk.Label(frame, text="ACL 通配符：0 表示必须匹配，1 表示忽略该位。非连续通配符的最小、最大地址之间可能有不匹配的地址。\n/31 按点对点网络计算两个可用地址；/32 为单主机。ACL 输出为地址与通配符片段。", style="Sub.TLabel", wraplength=840).pack(anchor="w", pady=(12, 0))
        root.bind("<Return>", lambda _: self.run())
        self.run()

    def change_mode(self, _=None):
        self.value.set({"CIDR 前缀": "24", "正掩码": "255.255.255.0", "反掩码 / ACL 通配符": "0.0.0.255"}[self.mode.get()])
        self.run()

    def run(self):
        try:
            result, base, mask = calculate(self.address.get(), self.value.get(), self.mode.get())
        except ValueError as exc:
            self.tree.delete(*self.tree.get_children())
            self.subnets.delete(*self.subnets.get_children())
            self.bits.delete("all")
            self.subnet_summary.set("")
            if hasattr(self, "current"):
                del self.current
            self.check_status.set("")
            self.status.set(f"输入有误：{exc}")
            return None
        self.tree.delete(*self.tree.get_children())
        for key, value in result.items():
            tag = "wildcard" if "通配符" in key else "range" if any(word in key for word in ("范围", "地址数量", "广播", "匹配地址")) else "network"
            self.tree.insert("", "end", values=(key, value), tags=(tag,))
        key = (base, mask)
        if key != self.last_key:
            self.page_offset = 0
            self.last_key = key
        self.current = (base, mask)
        self.draw_bits()
        self.show_subnets()
        self.status.set("计算完成 · 可复制全部结果，或输入地址检查 ACL 是否匹配。")
        self.check_status.set("")
        return result, base, mask

    def draw_bits(self):
        self.bits.delete("all")
        base, mask = self.current
        _, _, trailing = subnet_page(base, mask, 0, 1)
        width = max(self.bits.winfo_width(), 840)
        cell = (width - 36) / 32
        for octet in range(4):
            self.bits.create_text(18 + (octet * 8 + 4) * cell, 12, text=f"第 {octet + 1} 段", fill="#61718a", font=("Microsoft YaHei UI", 9))
        for index in range(32):
            bit = 31 - index
            fixed = bool(mask & (1 << bit))
            bg, fg = ("#dce9ff", "#2456a6") if fixed else (("#e2f4eb", "#18724f") if bit < trailing else ("#eee3ff", "#7840ac"))
            x = 18 + index * cell
            self.bits.create_rectangle(x + 1, 28, x + cell - 2, 57, fill=bg, outline="")
            self.bits.create_text(x + cell / 2, 43, text=str((base >> bit) & 1) if fixed else "*", fill=fg, font=("Consolas", 12, "bold"))
        self.bits.create_text(18, 79, anchor="w", text="蓝色  固定匹配位      紫色  非连续分支位      绿色  连续地址位     ·     * 可取 0 或 1", fill="#52647d", font=("Microsoft YaHei UI", 9))

    def show_subnets(self):
        networks, total, _ = subnet_page(*self.current, self.page_offset)
        self.subnets.delete(*self.subnets.get_children())
        groups = {}
        for index, network in enumerate(networks):
            parts = str(network.network_address).split(".")
            group = ".".join(parts[:2]) + ".0.0/16" if network.prefixlen >= 16 else parts[0] + ".0.0.0/8" if network.prefixlen >= 8 else "IPv4 地址空间"
            if group not in groups:
                groups[group] = self.subnets.insert("", "end", text=group, open=True, tags=("group",))
            self.subnets.insert(groups[group], "end", text=str(network), values=(f"{network.network_address} ～ {network.broadcast_address}", f"{network.num_addresses:,}"), tags=("even" if index % 2 == 0 else "odd",))
        self.subnet_summary.set(f"精确匹配 {total:,} 个 CIDR 子网   ·   当前 {self.page_offset + 1:,}–{self.page_offset + len(networks):,}   ·   层级节点用于分组，不代表整组均匹配")
        self.prev.configure(state="normal" if self.page_offset else "disabled")
        self.next.configure(state="normal" if self.page_offset + 128 < total else "disabled")

    def move_page(self, delta):
        self.page_offset = max(0, self.page_offset + delta)
        self.show_subnets()

    def check(self):
        data = self.run()
        if data is None:
            return
        try:
            matched = matches(self.candidate.get(), data[1], data[2])
            self.check_status.set(f"{self.candidate.get()}：{'匹配 ✓' if matched else '不匹配 ✕'}")
        except ValueError as exc:
            self.check_status.set(str(exc))

    def copy(self):
        data = self.run()
        if data is not None:
            self.root.clipboard_clear()
            networks, total, _ = subnet_page(data[1], data[2], self.page_offset)
            detail = f"\n\n精确 CIDR 分解：共 {total:,} 个，当前页 {self.page_offset + 1}–{self.page_offset + len(networks)}\n" + "\n".join(str(n) for n in networks)
            self.root.clipboard_append("IPv4 地址：" + self.address.get() + "\n" + "\n".join(f"{k}：{v}" for k, v in data[0].items()) + detail)
            self.status.set("已复制全部计算结果。")

    def example(self):
        self.address.set("192.168.0.0")
        self.mode.set("反掩码 / ACL 通配符")
        self.value.set("0.0.5.255")
        self.candidate.set("192.168.4.100")
        self.check()
        self.notebook.select(1)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
