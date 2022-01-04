#!/usr/bin/env python3

import itertools
from typing import Optional, Tuple
import compatibility_check # type: ignore

from btcrecover import btcrseed
import sys, multiprocessing

def main(words: list[list[str]]) -> Tuple[Optional[str], int]:
    total_iterations = 1
    for a in words:
        total_iterations *= len(a)

    base_argv = "--dsw --wallet-type ethereum --addrs 0x82Bd10047dBE588508d5d976d59693E4Ab4ADaC5 --addr-limit 1 --big-typos 1 --mnemonic".split(" ")

    for i, partial_mnemonic in enumerate(itertools.product(*words)):
        partial_mnemonic = " ".join(partial_mnemonic)

        print("")
        print(f"[{i}/{total_iterations}] {partial_mnemonic}")

        argv = base_argv + [partial_mnemonic]
        mnemonic_sentence, path_coin = btcrseed.main(argv) # type: ignore

        # Wait for any remaining child processes to exit cleanly (to avoid error messages from gc)
        for process in multiprocessing.active_children():
            process.join(1.0)

        if mnemonic_sentence:
            return mnemonic_sentence, path_coin # type: ignore

    return None, 0

if __name__ == "__main__":
    print()
    print("Starting", btcrseed.full_version())

    btcrseed.register_autodetecting_wallets()

    words = [
        ["apology", "runway", "argue"],
        ["cheese"],
        ["famous", "empty"],
        ["corn"],
        ["giggle"],
        ["frame"],
        ["pause"],
        ["abuse"],
        ["husband", "expose"],
        ["elegant"],
        ["pride"],
        # ["shrimp"],
    ]

    mnemonic_sentence, path_coin = main(words)

    if mnemonic_sentence:
        print(f"Found match: {mnemonic_sentence}")

        btcrseed.init_gui()
        if btcrseed.tk_root:
            btcrseed.show_mnemonic_gui(mnemonic_sentence, path_coin) # type: ignore

        sys.exit(0)

    else:
        print("No solutions found")
        sys.exit(1)
