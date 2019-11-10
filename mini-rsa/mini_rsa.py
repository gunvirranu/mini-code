#!/usr/bin/env python3

import random
import base64


def calc_blocksize(n):
    blocksize = 1
    while 127**(blocksize+1) <= n:
        blocksize += 1
    return blocksize


def en_block(data, bsize):
    blocks = [0] * -(-len(data) // bsize)
    for i in range(0, len(data), bsize):
        for k in range(bsize):
            if i+k < len(data):
                blocks[i // bsize] += data[i+k] * 127**(bsize-k-1)
    return blocks


def de_block(blocks, bsize):
    data = []
    for block in blocks:
        tmp = [0] * (bsize)
        for k in range(bsize):
            block, tmp[bsize-k-1] = divmod(block, 127)
        data.extend(tmp)
    return data


def encrypt(msg, e, n):
    blocksize = calc_blocksize(n)
    blocks = en_block([ord(x) for x in msg], blocksize)
    enc = [pow(i, e, n) for i in blocks]
    bb = de_block(enc, blocksize+1)
    c = base64.b64encode(bytes(bb)).decode()
    return c


def decrypt(msg, d, n):
    blocksize = calc_blocksize(n)
    bb = list(base64.b64decode(msg))
    blocks = en_block(bb, blocksize+1)
    dec = [pow(i, d, n) for i in blocks]
    asc = de_block(dec, blocksize)
    z = ''.join([chr(i) for i in asc]).rstrip('\0')
    return z


########################################


def sieve_primes_to(n: int) -> [int]:
    """Generate prime numbers up to `n`."""
    size = n // 2
    sieve = [1] * size
    limit = int(n**0.5)
    for i in range(1, limit):
        if sieve[i]:
            val = 2*i + 1
            tmp = ((size-1) - i) // val
            sieve[i+val::val] = [0] * tmp
    return [i*2 + 1 for i, v in enumerate(sieve) if v and i > 0]


def euc_mod_inv(aa: int, bb: int) -> int:
    """"Find modular inverse using the Euclidean algorithm."""
    last_rem, rem, x, last_x, y, last_y = aa, bb, 0, 1, 1, 0
    while rem:
        last_rem, (quot, rem) = rem, divmod(last_rem, rem)
        x, last_x = last_x - quot * x, x
        y, last_y = last_y - quot * y, y
    return (last_x * (-1 if aa < 0 else 1)) % bb


def gen_tokens(p: int, q: int) -> (int, int, int, int):
    """Generate compression tokens from two primes."""
    n, phi = p * q, (p-1) * (q-1)
    e = random.choice([x for x in sieve_primes_to(phi) if phi % x != 0])
    e = 65537
    d = euc_mod_inv(e, phi)
    return n, phi, e, d, 2


def chunks(x, n):
    """Yield chunks of size `n` from `x`.`"""
    for i in range(0, len(x), n):
        yield x[i : i + n]


def encrypt(text: bytes, e: int, n: int, bsize) -> bytes:
    """Encrypt binary data using provided tokens."""
    blocks = (int.from_bytes(x, "big") for x in chunks(text, bsize))
    enc = (pow(i, e, n) for i in blocks)
    bb = b"".join(i.to_bytes(bsize, "big") for i in enc)
    return bb



def main():
    """
    USAGE_TEXT = "Usage: mini_rsa.py {encrypt|decrypt} <infile> <outfile>"
    if len(argv) != 4: exit("Invalid arguments.\n" + USAGE_TEXT)
    FUNCS = {"encrypt": encrypt, "decrypt": decrypt}
    if argv[1] not in FUNCS: exit("Invalid operation.\n" + USAGE_TEXT)
    with open(argv[2], "rb") as f: in_bytes = f.read()
    out_bytes = FUNCS[argv[1]](in_bytes)
    with open(argv[3], "wb") as f: f.write(out_bytes)
    """

    BITS = 8 * 64
    p = 997
    q = 991




    n, phi, e, d, bsize = gen_tokens(p, q)
    print('MODULO    :', n)
    print('TOTIENT   :', phi)
    print('BLOCKSIZE :', bsize)
    print('PUBLIC    :', e)
    print('PRIVATE   :', d)
    print()
    m = b"testing testing lmao brother man"
    c = encrypt(m, e, n, bsize)
    print('CLEARTEXT:', m)
    print('ENCRYPTED:', c)
    """
    z = decrypt(c, d, n)
    print('DECRYPTED:', z)
    assert m == z
    print()
    """


if __name__ == "__main__":
    main()
