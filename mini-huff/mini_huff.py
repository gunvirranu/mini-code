#!/usr/bin/env python3

# TODO: Finalize and shrinkify

from sys import exit, argv
from struct import pack, unpack, iter_unpack


def compress(text: bytes) -> bytes:
    if not text:
        return bytes()
    weights = {}
    for let in text:
        weights[let] = weights.get(let, 0) + 1
    tree = sorted(weights.items(), key=lambda x: x[1])
    while len(tree) > 1:
        tree = sorted(tree[2:] + [((tree[0][0], tree[1][0]), tree[0][1] + tree[1][1])], key=lambda x: x[1])
    codes, stak = {}, [(tree[0][0], "" if isinstance(tree[0][0], tuple) else "1")]
    while stak:
        node = stak.pop()
        if not isinstance(node[0], tuple):
            codes[node[0]] = node[1]
        else:
            stak.extend([(node[0][i], node[1] + str(i)) for i in range(2)])
    bits = "".join(codes[let] for let in text)
    compressed_text = bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))
    alt_codes = ((int(code, 2) | (1 << len(code)), let) for let, code in codes.items())
    serial_codes = pack(">" + "LB" * len(codes), *(i for pair in alt_codes for i in pair))
    return b"".join((
        bytes((len(bits) % 8,)),
        pack(">L", len(codes) * (1 + 4)),
        serial_codes,
        compressed_text,
    ))


def decompress(compressed: bytes) -> bytearray:
    if not compressed:
        return bytearray()
    last_bits = (compressed[0] - 1) % 8
    code_len = unpack(">L", compressed[1:5])[0]
    codes = dict(iter_unpack(">LB", compressed[5 : 5 + code_len]))
    compressed = memoryview(compressed)[5 + code_len :]
    text, cur = bytearray(), 1
    for i, byte in enumerate(compressed):
        for dig in range(7 if i + 1 != len(compressed) else last_bits, -1, -1):
            cur = (cur << 1) | ((byte >> dig) & 1)
            tmp = codes.get(cur, None)
            if tmp is not None:
                text.append(tmp)
                cur = 1
    return text


USAGE_TEXT = "Usage: mini_huff.py {compress|decompress} <infile> <outfile>"

if __name__ == "__main__":
    if len(argv) != 4:
        exit("Invalid arguments.\n" + USAGE_TEXT)
    funcs = {"compress": compress, "decompress": decompress}
    if argv[1] not in funcs:
        exit("Invalid operation.\n" + USAGE_TEXT)
    with open(argv[2], "rb") as f:
        in_bytes = f.read()
    out_bytes = funcs[argv[1]](in_bytes)
    print("In: {}, Out: {}, Ratio: {:.2f}%".format(
            len(in_bytes),
            len(out_bytes),
            100 * (len(out_bytes) / len(in_bytes) if in_bytes else 1)
        )
    )
    with open(argv[3], "wb") as f:
        f.write(out_bytes)
