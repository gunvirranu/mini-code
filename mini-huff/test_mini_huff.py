#!/usr/bin/env python3

from sys import stderr
from random import seed, randrange

from mini_huff import compress, decompress


def check(t):
    c = compress(t)
    d = decompress(c)
    assert t == d, "{} (original) != {} (decompressed)".format(t, d)


def test_empty():
    check(bytes())

def test_len_one():
    check(b"Q")

def test_one_symbol():
    check(b"WWW")

def test_two_symbol():
    check(b"ABABA")


def fuzz(iters, max_len):
    for _ in range(iters):
        n = randrange(2, max_len + 1)
        t = bytes(randrange(256) for _ in range(n))
        check(t)

def test_fuzz():
    N_ITERS = 100
    MAX_LEN = 100
    seed(0xABCD)
    fuzz(N_ITERS, MAX_LEN)


def main():
    funcs = ((name, f) for name, f in globals().items() if callable(f))
    tests = ((name, f) for name, f in funcs if name.startswith("test_"))
    for name, f in tests:
        print("Testing", name, file=stderr)
        f()
    print("\033[92mAll good :)\033[0m", file=stderr)

if __name__ == "__main__":
    main()
