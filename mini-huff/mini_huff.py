#!/usr/bin/env python3

from sys import exit, argv
from struct import pack, unpack, iter_unpack


def compress(text: bytes) -> bytes:
    if not text:
        return bytes()

    weights = {}
    for let in text:
        weights[let] = weights.get(let, 0) + 1

    tree = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    while len(tree) > 1:
        smol, sec_smol = tree.pop(), tree.pop()
        tree.append(((smol[0], sec_smol[0]), smol[1] + sec_smol[1]))
        tree.sort(key=lambda x: x[1], reverse=True)

    codes = {}
    stak = [(tree[0][0], "" if isinstance(tree[0][0], tuple) else "1")]
    while stak:
        node = stak.pop()
        if isinstance(node[0], tuple):
            stak.extend((node[0][i], node[1] + str(i)) for i in range(2))
        else:
            codes[node[0]] = node[1]

    bits = "".join(codes[let] for let in text)
    return b"".join((
        pack(
            ">BL" + "LB" * len(codes),
            len(bits) % 8,
            len(codes) * (4 + 1),
            *(
                i
                for pair in (
                    (int(code, 2) | (1 << len(code)), let)
                    for let, code in codes.items()
                )
                for i in pair
            ),
        ),
        bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8)),
    ))


def decompress(compressed: bytes) -> bytearray:
    if not compressed:
        return bytearray()

    compressed = memoryview(compressed)
    last_bits = (compressed[0] - 1) % 8
    codes_len = unpack(">L", compressed[1:5])[0]
    compressed = compressed[5:]
    codes = dict(iter_unpack(">LB", compressed[:codes_len]))
    compressed = compressed[codes_len:]

    text, cur = bytearray(), 1
    for i, byte in enumerate(compressed):
        not_last_byte = (i + 1 != len(compressed))
        for dig in range(7 if not_last_byte else last_bits, -1, -1):
            cur = (cur << 1) | ((byte >> dig) & 1)
            if cur in codes:
                text.append(codes[cur])
                cur = 1
    return text


USAGE_TEXT = "Usage: mini_huff.py {compress|decompress} <infile> <outfile>"
FUNCS = {"compress": compress, "decompress": decompress}


def main():
    if len(argv) != 4:
        exit("Invalid arguments.\n" + USAGE_TEXT)
    if argv[1] not in FUNCS:
        exit("Invalid operation.\n" + USAGE_TEXT)

    with open(argv[2], "rb") as f:
        in_bytes = f.read()
    out_bytes = FUNCS[argv[1]](in_bytes)

    print(
        "In: {}, Out: {}, Ratio: {:.2f}%".format(
            len(in_bytes),
            len(out_bytes),
            100 * (len(out_bytes) / len(in_bytes) if in_bytes else 1)
        )
    )
    with open(argv[3], "wb") as f:
        f.write(out_bytes)


if __name__ == "__main__":
    main()
