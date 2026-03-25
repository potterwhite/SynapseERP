#!/usr/bin/env python3
# MIT License — SynapseERP
"""
Compile .po translation files to .mo without GNU gettext.

Usage: python compile_messages.py <locale_dir>

This is a pure-Python fallback for systems without msgfmt installed.
It produces binary .mo files that Django can use at runtime.
"""

import ast
import os
import struct
import sys


def compile_po_to_mo(po_path: str, mo_path: str) -> int:
    """Compile a single .po file to .mo format. Returns message count."""
    messages: list[tuple[bytes, bytes]] = []
    msgid_parts: list[str] = []
    msgstr_parts: list[str] = []
    in_msgid = False
    in_msgstr = False

    with open(po_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("msgid "):
                if in_msgstr and (msgid_parts or msgstr_parts):
                    mid = "".join(msgid_parts).encode("utf-8")
                    mstr = "".join(msgstr_parts).encode("utf-8")
                    messages.append((mid, mstr))
                in_msgid = True
                in_msgstr = False
                msgid_parts = [ast.literal_eval(line[6:])]
                msgstr_parts = []
            elif line.startswith("msgstr "):
                in_msgid = False
                in_msgstr = True
                msgstr_parts = [ast.literal_eval(line[7:])]
            elif line.startswith('"'):
                s = ast.literal_eval(line)
                if in_msgid:
                    msgid_parts.append(s)
                elif in_msgstr:
                    msgstr_parts.append(s)

    if msgid_parts or msgstr_parts:
        mid = "".join(msgid_parts).encode("utf-8")
        mstr = "".join(msgstr_parts).encode("utf-8")
        messages.append((mid, mstr))

    messages.sort(key=lambda x: x[0])

    n = len(messages)
    ids = b""
    strs = b""
    offsets: list[tuple[int, int, int, int]] = []
    for mid, mstr in messages:
        offsets.append((len(ids), len(mid), len(strs), len(mstr)))
        ids += mid + b"\x00"
        strs += mstr + b"\x00"

    keystart = 28 + 8 * n * 2
    valuestart = keystart + len(ids)

    output: list[bytes] = []
    output.append(struct.pack("Iiiiiii", 0x950412DE, 0, n, 28, 28 + n * 8, 0, 0))
    for o in offsets:
        output.append(struct.pack("ii", o[1], keystart + o[0]))
    for o in offsets:
        output.append(struct.pack("ii", o[3], valuestart + o[2]))
    output.append(ids)
    output.append(strs)

    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, "wb") as f:
        f.write(b"".join(output))

    return n


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <locale_dir>")
        sys.exit(1)

    locale_dir = sys.argv[1]
    total = 0

    for root, _dirs, files in os.walk(locale_dir):
        for filename in files:
            if filename.endswith(".po"):
                po_path = os.path.join(root, filename)
                mo_path = po_path[:-3] + ".mo"
                n = compile_po_to_mo(po_path, mo_path)
                print(f"  Compiled: {po_path} -> {mo_path} ({n} messages)")
                total += n

    print(f"  Total: {total} messages compiled")


if __name__ == "__main__":
    main()
