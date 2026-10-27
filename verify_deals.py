#!/usr/bin/env python3
"""Verify Fantasy Land deals on your own computer (Python 3.10+).

Run from this folder:
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python verify_deals.py

The program asks for the public JSON and revealed-secret JSON separately.
Then enter a hand number, each player's Fantasyland status/card count, and
who was dealt to first. It prints EVERY deal for that hand. Enter q to finish.
For Chinese games, answer yes for both players and enter their hand size.

No source editing or network access is needed. Helper modules in verification/
contain the exact hash, drand-signature, shuffle and card-allocation algorithms.
"""
import sys

from verification.protocol import verify_game_and_format, verify_public_commitment
from verification.drand import verify_drand_beacon
from verification.deals import recreate_deck, build_hand_deals
from verification.console import (
    ask_for_json, ask_hand_number, ask_fantasyland, ask_first_player, show_hand,
)


def main():
    # 1. Read the two independently saved copies from the user.
    public = ask_for_json('Public JSON — Copy Cryptographic Commitment')
    revealed = ask_for_json('Revealed-secret JSON — Copy Revealed Secret')

    # 2. Verify the documents describe the same game and supported format.
    verify_game_and_format(public, revealed)

    # 3. Verify the revealed seed matches the original public commitment hash.
    secret = verify_public_commitment(public, revealed['revealed_secret'])
    print('Public commitment hash verified.')

    # 4. Verify drand's signature for the round fixed in the public commitment.
    randomness = verify_drand_beacon(public, revealed)
    if randomness is None:
        print('This game ended before its beacon was received; no cards were dealt.')
        return
    print('drand signature and public randomness verified.')
    print('Compare the expected cards below with your own game records.')
    print('For Chinese deals, answer yes for both players. Ctrl+C stops at any prompt.')

    # 5. Recreate and show every deal for each hand the user wants to inspect.
    while True:
        hand = ask_hand_number()
        if hand is None:
            return
        fantasy_cards = ask_fantasyland(public['players'])
        first_player = ask_first_player(public['players'])
        deck = recreate_deck(public, secret, randomness, hand)
        deals = build_hand_deals(deck, fantasy_cards)
        show_hand(hand, public['players'], deals, fantasy_cards, first_player)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nStopped.')
    except Exception as error:
        print(f'Verification failed: {error}', file=sys.stderr)
        sys.exit(1)
