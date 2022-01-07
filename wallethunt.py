#!/usr/bin/env python3

import re
import itertools
from typing import Optional, Tuple
import compatibility_check  # type: ignore

from btcrecover import btcrseed
import sys
import multiprocessing


def main(
    words: list[list[str]],
    addr: str,
    excluded_filename: Optional[str],
    big_typos: Optional[int] = None
) -> Tuple[Optional[str], int]:
    excluded_sentences: set[str] = (
        get_excluded_inputs(
            excluded_filename) if excluded_filename else set([])
    )

    total_iterations = 1
    for a in words:
        total_iterations *= len(a)

    big_typos = max(1, 12 - len(words)) if big_typos is None else big_typos

    base_argv = [
        "--dsw",
        "--wallet-type", "ethereum",
        "--addrs", f"{addr}",
        "--addr-limit", "1",
        "--passphrase-arg", "",
        "--big-typos", f"{big_typos}",
        "--mnemonic"
    ]

    for i, partial_mnemonic_list in enumerate(itertools.product(*words)):
        partial_mnemonic = " ".join(partial_mnemonic_list)

        print("")
        print(f"[{i+1}/{total_iterations}] {partial_mnemonic}")

        if partial_mnemonic in excluded_sentences:
            print(f"Matches exclusion: {partial_mnemonic}")
            continue

        # Check for also matching partial phrases with fewer words
        for i in (-1, -2):
            partial_mnemonic_less = " ".join(partial_mnemonic_list[:i])
            if partial_mnemonic_less in excluded_sentences:
                print(f"Matches exclusion: {partial_mnemonic_less}")
                continue

        argv = base_argv + [partial_mnemonic]
        mnemonic_sentence, path_coin = btcrseed.main(argv)  # type: ignore

        # Wait for any remaining child processes to exit cleanly (to avoid error messages from gc)
        for process in multiprocessing.active_children():
            process.join(1.0)

        if mnemonic_sentence:
            return mnemonic_sentence, path_coin  # type: ignore

        # Input failed, add to excluded
        if excluded_filename:
            add_excluded_input(excluded_filename, partial_mnemonic)

    return None, 0


def get_excluded_inputs(filename: str) -> set[str]:
    try:
        with open(filename) as f:
            return set([line.strip() for line in f.readlines()])
    except FileNotFoundError:
        return set([])


def add_excluded_input(filename: str, sentence: str):
    with open(filename, "a") as f:
        _ = f.write(f"{sentence}\n")


def get_addr_words_from_lines(lines: list[str]) -> Tuple[str, list[list[str]]]:
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if len(line) > 0]

    addr = lines.pop(0)
    words = [
        [word.strip().lower() for word in re.split(r'[,\s]+', line)]
        for line in lines
    ]

    return addr, words


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    _ = parser.add_argument(
        "file", type=argparse.FileType("r"), help="Input file")
    _ = parser.add_argument(
        "--big-typos", "-t", metavar="N",
        type=int, help="Number of words to randomize")
    args = parser.parse_args()

    addr, words = get_addr_words_from_lines(args.file.readlines())

    print()
    print("Starting", btcrseed.full_version())

    btcrseed.register_autodetecting_wallets()

    print(f"Searching for {addr} from {len(words)} word lists:\n{words}")

    mnemonic_sentence, path_coin = main(
        words, addr, f".exclude-{addr}.txt", big_typos=args.big_typos)

    if mnemonic_sentence:
        print(f"Found match: {mnemonic_sentence}")

        with open(f".match-{addr}.txt", "w") as f:
            _ = f.write(mnemonic_sentence)

        btcrseed.init_gui()
        if btcrseed.tk_root:
            btcrseed.show_mnemonic_gui(  # type: ignore
                mnemonic_sentence, path_coin)

        sys.exit(0)

    else:
        print("No solutions found")
        sys.exit(1)
