
# Explanation

The following aims to explain the code. Minified code will be broken up into
multiple lines, and temporary variables may be used to explain intermediate,
but important values. The code is, however, functionally the same.

The primary algorithm used is Huffman Coding, but this will only be covered
in passing in the explanation of the code. A basic prerequisite understanding
of the algorithm would be helpful.

# Compression

----------

```python
def compress(text: bytes) -> bytes:
    if not text:
        return bytes()
```

The `compress` function takes a argument `text`, of type `bytes`.
It will return the compressed text, together with a serialization of the
coding tables. If no `text` is passed in, zero bytes are returned.

----------

```python
weights = {}
for let in text:
    weights[let] = weights.get(let, 0) + 1
```

A dictionary `weights` is constructed, which contains the frequency count of
all "letters" used in the input text. For example, if `text` is `"aab"`, then
`weights = {'a': 2, 'b': 1}`.

----------

```python
tree = sorted(weights.items(), key=lambda x: x[1])
while len(tree) > 1:
    # Take two nodes with lowest frequency
    smallest = tree.pop(0)
    second_smallest = tree.pop(0)
    # Combine two nodes into a new node
    new_value = (smallest[0], second_smallest[0])
    new_weight = smallest[1] + second_smallest[1]
    new_node = (new_value, new_weight)
    # Insert node into tree and regenerate
    new_tree = tree.append(new_node)
    tree.sort(key=lambda x: x[1])
```

The idea behind Huffman coding is to create a priority queue, based on the
inverse of the probability / frequency count. The initial declaration of
`tree` creates a k-ary tree, which is sorted by the frequency of the letters
(`key=lambda x: x[1]`, where `x` is `(<letter>, <frequency>)`). This k-ary
tree is then iteratively converted to a binary tree sorted by the frequencies
of the characters (termed a Huffman tree). This is done by taking the two
least frequent characters and combining their nodes to create a new node. The
frequency count of this new node is the sum of the combined nodes. This node
is re-inserted into the original tree, while ensuring the tree remains sorted
by freqency. This is repeated until a single root node is left, meaning that
a binary coding tree has been generated. This step operates only on the
possible symbols in `text`, so there is little need to optimize this step.

----------

```python
codes = {}
stak = [(tree[0][0], "" if isinstance(tree[0][0], tuple) else "1")],
while stak:
    node = stak.pop()
    if not isinstance(node[0], tuple):
        codes[node[0]] = node[1]
    else:
        stak.extend([(node[0][i], node[1] + str(i)) for i in range(2)])
```

A stack is used to iteratively traverse the Huffman tree, while maintaining
the path traversed downwards as a string. The leaf nodes of the tree are
characters, and their encoding is defined as the path from the root node.
Going down to the left node is a `0` and right is a `1`. Terminal nodes are
detected by checking the type of the node value, which is only a tuple for
non-leaf nodes. Once a leaf node is reached, the stored traversal path is
assigned the coding for the node's character. This creates a dictionary
`codes`, mapping characters to their binary coding as a string of 0s and 1s.
An example of what this dictionary could look like is
`codes = {'a': '0', 'b': '10', 'c': '11'}`. The purpose of the `ifinstance`
in the declaration of `tree` is in the degenerate case of there only being
one character, so it immediately assigned the code `1`.

----------

```python
bits = "".join(codes[let] for let in text)
```

The bit codes are used to iterate over all characters in `text` and create
a string of bits representing the compressed text. It is important to realize
that `bits` is of type `str`, and contains only the characters `0` and `1`.

----------

```python
# Join the following four `bytes` objects
return b"".join((
    # Used for decompressing the last byte of text
    bytes((len(bits) % 8,)),
    # Number of bytes of `codes`, `4` for bit-code, `1` for character
    pack(">L", len(codes) * (4 + 1)),
    # Serialize codes dictionary as <bit-code> <char> repeated
    pack(
        # `L` for 4-byte bit-code, `B` for 1-byte character
        ">" + "LB" * len(codes),
        # Iterate over all bit-codes and characters in `codes`
        *(
            i
            for pair in (
                # `1` is added as MSb to pad codes with MSb of `0`
                (int(code, 2) | (1 << len(code)), let)
                for let, code in codes.items()
            )
            for i in pair
        )
    ),
    # Convert string of bits to `bytes`
    bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)),
))
```

The compressed text, as well as all data required to decompress the text is
serialized and returned as `bytes`. The four pieces of information that are
seralized are as follows.

1. The number of bits in the last compressed byte. This is used during
   decompression, as the following few bits must be ignored if the length
   of `bits` is not an exact number of bytes.

2. Length of the `codes` dictionary in bytes, which follows this value. The
   length of `codes` is multiplied by 5, as each code contains a 4-byte
   bit-string, representing the left-padded code, and 1-byte for the
   character the code represents.

3. The `codes` dictionary, which is series of 5-byte entries, as described
   above.

4. Bytes of the compressed text. The length is not needed, as the rest of the
   data is assumed to be encoded text. The bits of this compressed text are
   formed by the concatenation of the generated Huffman codes.

----------

## Decompression

----------

```python
def decompress(compressed: bytes) -> bytearray:
    if not compressed:
        return bytearray()
```

The `decompress` function takes an argument `compressed`, of type `bytes`. It
returns the decompressed text as a `bytearray`. If no data is passed in, zero
bytes are returned.

----------

```python
compressed = memoryview(compressed)
# Index of last bit in last byte
last_bits = (compressed[0] - 1) % 8
# Length of codes dictionary
code_len = unpack(">L", compressed[1:5])[0],
# Leave only codes and compressed data
compresed = compressed[5:]
```

A `memoryview` for `compressed` is used, to decrease the cost of slicing
large chunks of the compressed bytes. A couple preliminary values are
deserialized from `compressed`.

----------

```python
# Parse the codes dictionary
codes = dict(iter_unpack(">LB", compressed[:code_len]))
# Leave only the compressed data
compressed = compressed[code_len:]
# Decompressed text
text = bytearray()
# Will be explained further in the next section
cur = 1
```

The codes dictionary is parsed elegantly through the combined usage of
`iter_unpack`, which returns an iterator of tuples of `(<bit-code>, <char>)`,
and the `dict` constructor, which deals with 2-tuples.

----------

```python
# Iterate over all compressed bytes
for i, byte in enumerate(compressed):
    # Check for if last byte of compressed text
    is_last_byte = i + 1 != len(compressed)
    # Iterate MSb to LSb of current byte
    # If last byte, don't start at MSb
    for dig in range(7 if not is_last_byte else last_bits, -1, -1):
        # Add bit to LSb of current code
        cur = (cur << 1) | ((byte >> dig) & 1)
        # Check if `cur` maps to a character
        if cur in codes:
            # If `cur` is valid code, add character to output
            text.append(codes.get(cur))
            # Reset code to 1, because all codes start with MSb of 1
            cur = 1
return text
```

All bytes of the decompressed data are iterated over. For each byte, the bits
are iterated over from MSb to LSb (left to right). The current code is
tracked by `cur`, which represents the current location within the Huffman
tree. At each bit, the `codes` dictionary is checked to determine if `cur` is
a valid leaf-node code. If not, move onto the next bit. If it, however, is a
valid code, the code is decoded and added to the decompressed output. More
importantly, `cur` is reset to 1, because during code serialization in
`compress`, each code was padded with a MSb of 1. This process decompresses
all the data, and the decompressed `bytearray` is returned.

----------

# Command Line

----------

```python
if __name__ == "__main__":
    main()
```
Run the `main` function only if the module is not imported by another.

----------

```python
def main():
    USAGE_TEXT = "Usage: mini_huff.py {compress|decompress} <infile> <outfile>"
    if len(argv) != 4:
        exit("Invalid arguments.\n" + USAGE_TEXT)
    # Dictionary mapping input command to cooresponding function
    FUNCS = {"compress": compress, "decompress": decompress}
    if argv[1] not in FUNCS:
        exit("Invalid operation.\n" + USAGE_TEXT)
    # Read binary data of input files
    with open(argv[2], "rb") as f:
        in_bytes = f.read()
    # Call either `compress` or `decompress` with input binary data
    out_bytes = FUNCS[argv[1]](in_bytes)
    # Print out lengths of input and output bytes, and size ratio
    print(
        "In: {}, Out: {}, Ratio: {:.2f}%".format(
            len(in_bytes),
            len(out_bytes),
            100 * (len(out_bytes) / len(in_bytes) if in_bytes else 1)
        )
    )
    # Write either compressed or decompressed data to output file
    with open(argv[3], "wb") as f:
        f.write(out_bytes)
```
Create a simple command line tool with rudimentary argument validation.
File exceptions due to reading or writing are not handled.

