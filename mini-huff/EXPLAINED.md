
# Explained

The following aims to explain `mini_huff.py`. Only the non-trivial lines are documented; the others are omitted. Some code may be broken up into multiple lines or temporary variables to explain intermediate, but important values. The code is, however, logically the same.

The primary algorithm used in [Huffman coding](https://wikipedia.org/wiki/Huffman_coding). It is only covered in pasing here, but you can check out the link or additional resources.

## Compression

```python
weights = {}
for let in text:
    weights[let] = weights.get(let, 0) + 1
```

The dict `weights` contains the frequency count of all symbols (i.e. "letters") in the input text. Since I iterate over `bytes`, the symbols are numbers in the range 0-255. For example, if `text = "aab"`, then `weighs = {97: 2, 98: 1}` (remember `ord('a') == 97`).

---

```python
tree = sorted(weights.items(), key=lambda x: x[1], reverse=True)
while len(tree) > 1:
    # Take two nodes with lowest frequency
    smol = tree.pop()
    sec_sol = tree.pop()
    # Combine two nodes into a new node
    new_value = (smol[0], sec_smol[0])
    new_weight = smol[1] + sec_smol[1]
    new_node = (new_value, new_weight)
    # Insert new node into tree and regenerate
    tree.append(new_node)
    tree.sort(key=lambda x: x[1], reverse=True)
```

This actually constructs the Huffman coding tree. What this snippet does is iteratively convert a k-ary tree (initially with only one level) to a binary Huffman tree, which then defines a new coding for each symbol. It does this by sorting the nodes by the frequency of the letters (`lambda x: x[1]`), taking the two least frequent characters, and combining their nodes, and then repeating. The frequency count for for the new node is the sum of the combined nodes. This ends up stuffing nodes with low frequency counts lower in the tree, and leaving high frequency nodes near the top. In the next step, we use this tree to generate new codings for each symbol, where deeper nodes have longer codings. _This_ is where the compression comes from. This step operates only on the possible symbols in `text` (in our case 0-255), so there's little need to optimize.

---

```python
codes = {}
# Initialize stack containing root node and empty path
stak = [(tree[0][0], "" ifisinstance(tree[0][0], tuple) else "1")]
while stak:
    node = stak.pop()
    # Check if inner node
    if isinstance(node[0], tuple):
        # Add both child nodes to stack with modified path
        left = (node[0][0], node[1] + "0")
        right = (node[0][1], node[1] + "1")
        stak.extend((left, right))
    else:
        # If leaf node, save traversal path
        codes[node[0]] = node[1]
```

Given the Huffman tree, this snippet uses a stack to traverse the tree, and convert it to a dict `codes` mapping a symbol to it's new binary coding. The leaf nodes of the tree are symbols, and their encoding is defined as the path from the root node to the leaf. Going down to the left is a `0`, and right is `1`. Inner and leaf nodes are differentiated by checking the type of their node value (`isinstance(node[0], tuple)`). For non-leaf nodes, the node value will be another `tuple`, whereas for leaf nodes, it will be an `int` symbol. The current path down is saved while traversing, and when a symbol is reached, the stored traversal path is assigned the coding for the symbol. Note that the binary codings in `codes` are strings of 0s and 1s (for example `codes = {97: "1011", ...`). The `isinstance` in the declaration of `tree` is in the degenerate case of there only being one character, so it is immediately assigned the code `1`.

---

```python
bits = "".join(codes[let] for let in text)
```

The binary codes are used to iterate over all characters in `text` and create a string of bits representing the compressed text. It's just the concatenation of the generated Huffman codes. Note that `bits` is of type `str`, and contains only the characters `'0'` and `'1'`. This step is quite slow because the compressed string is actually 8 times larger than it needs to be (1 byte is stored as an 8 byte string).

---

```python
# Return serialized metadata and compressed text
return b"".join((
    # Pack metadata at the start
    pack(
        # Format string for the 3 pieces of data
        ">BL" + "LB" * len(codes),
        # Number of bits in the last byte of text
        len(bits) % 8,
        # Number of bytes of `codes` (4 for bit-code, 1 for symbol)
        len(codes) * (4 + 1),
        # Iterate over all bit-codes and characters in `codes`
        *(
            i
            for pair in (
                # `1` is added to MSb to pad codes with MSb of `0`
                (int(code, 2) | (1 << len(code)), let)
                for let, code in codes.items()
            )
            for i in pair
        ),
    ),
    # Convert string of bits to actual `bytes`
    bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8)),
))
```

Some metadata required for decompression, and the compressed text itself is serialized and returned as `bytes`. The four pieces of information that are serialized are as follows.

1. The number of bits in the last compressed byte. This is used by decompression to ignore some padding bits in case the length of `bits` is not an exact number of bytes.

2. Length of the `codes` dictionary, which comes right after this in 3. The number of codes is multiplied by 5, as each code contains a 4-byte bit-string, representing the left-padded code, and 1-byte character code.

3. The actual `codes` dictionary, which is series of 5-byte entires, as described in 2.

4. Bytes of compressed text. The length isn't needed, because the rest of the data is assumed to be encoded text. This step is also quite slow because the string of bits has to be converted to actual `bytes`.

## Decompression

```python
compressed = memoryview(compressed)
# Index of last bit in last byte
last_bits = (compressed[0] - 1) % 8
# Length of codes dictionary
codes_len = unpack(">L", compressed[1:5])[0]
# Leave codes and compressed data
compressed = compressed[5:]
```

A `memoryview` for `compressed` is used to decrease the cost of slicing chunks. The first two pieces of metadata are deserialized.

---

```python
# Deserialize the codes dictionary
codes = dict(iter_unpack(">LB", compressed[:codes_len]))
# Leave only the compressed data
compressed = compressed[code_len:]
```

The `codes` dictionary is deserialized through the use of `iter_unpack`, which returns an iterator of tuples `(<bit-code>, <symbol>)`, and the `dict` constructor, which accepts an iterator of 2-tuples.

---

```python
text = bytearray()
# Current code (used below)
cur = 1
# Iterate over all compressed bytes
for i, byte in enumerate(compressed):
    not_last_byte = (i + 1 != len(compressed))
    # Iterate MSb to LSb of current byte
    # If last byte, don't start at MSb
    for dig in range(7 if not_last_byte else last_bits, -1, -1):
        # Add bit to LSb of current code
        cur = (cur << 1) | ((byte >> dig) & 1)
        # Check if `cur` maps to a character
        if cur in codes:
            text.append(codes[cur])
            # Reset code to `1`, cause all codes start with MSb of 1
            cur = 1
```

The bytes of the compressed data are iterated over. For each byte, the bits are iterated from MSb to LSb. The current code is tracked by `cur`, which represents the current node within the Huffman tree. At each bit, the `codes` dictionary is checked to see if `cur` is a valid leaf node. If not, move onto the next bit. If it is, the code is decoded and added to the decompressed `text`. Also, `cur` is reset to `1`, because during code serialization in `compress`, each code was padded with a MSb of `1`.
