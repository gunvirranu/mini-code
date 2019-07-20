
from sys import exit, argv


def compress(text: bytes) -> (tuple, int, bytes):
    weights = {}
    for let in text: weights[let] = weights.get(let, 0) + 1
    tree = sorted(weights.items(), key=lambda x: x[1])
    while len(tree) > 1: tree = sorted(tree[2:] + [((tree[0][0], tree[1][0]), tree[0][1] + tree[1][1])], key=lambda x: x[1])
    codes, stak = {}, [(tree[0][0], "")]
    while stak:
        node = stak.pop()
        if not isinstance(node[0], tuple): codes[node[0]] = node[1]
        else: stak.extend([(node[0][i], node[1] + str(i)) for i in range(2)])
    bits = "".join(codes[let] for let in text)
    return tree[0][0], len(bits) % 8, bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))


def decompress(tree: tuple, unpad: int, compressed: bytes) -> bytearray:
    text, chopped = bytearray(), tree
    for i, byte in enumerate(compressed):
        for dig in range(7 if i + 1 != len(compressed) else (unpad - 1) % 8, -1, -1):
            chopped = chopped[(byte >> dig) & 1]
            if isinstance(chopped, int):
                text.append(chopped)
                chopped = tree
    return text


USAGE_TEXT = "Usage: mini_huff.py {compress|decompress} <infile> <outfile>"

if __name__ == "__main__":
    if len(argv) != 4: exit("Invalid arguments.\n" + USAGE_TEXT)
    if argv[1] not in ("compress", "decompress"): exit("Invalid operation.\n" + USAGE_TEXT)
    with open(argv[2], "rb") as f: in_bytes = f.read()
    if argv[1] == "compress": out_bytes = compress(in_bytes)
    elif argv[1] == "decompress": out_bytes = decompress(f.read())
    print(
        "In: %d, Out: %d, Percent: %.2f"
        % (len(in_bytes), len(out_bytes), 100 * len(out_bytes) / len(in_bytes))
    )
    with open(argv[3], "wb") as f: f.write(out_bytes)
