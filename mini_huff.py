
from sys import exit, argv


def compress(text: bytes) -> (dict, int, bytes):
    weights = {}
    for let in text: weights[let] = weights.get(let, 0) + 1
    tree = sorted(weights.items(), key=lambda x: x[1])
    while len(tree) > 1: tree = sorted(tree[2:] + [((tree[0][0], tree[1][0]), tree[0][1] + tree[1][1])], key=lambda x: x[1])
    codes, stak = {}, [(tree[-1][0], "")]
    while stak:
        node = stak.pop()
        if not isinstance(node[0], tuple): codes[node[0]] = node[1]
        else: stak.extend([(node[0][i], node[1] + str(i)) for i in range(2)])
    bits = "".join(codes[let] for let in text)
    return codes, len(bits) % 8, bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))


def decompress(codes: dict, unpad: int, compressed: bytes) -> bytearray:
    codes = {bits: let for let, bits in codes.items()}
    text, bits = bytearray(), ""
    for i, byte in enumerate(compressed):
        for dig in range(7 if i + 1 != len(compressed) else (unpad - 1) % 8, -1, -1):
            bits += str((byte >> dig) & 1)
            let = codes.get(bits, None)
            if let:
                text.append(let)
                bits = ""
    return text
