"""Deterministic shuffle and fixed-seat card allocation.

The first-dealt choice NEVER changes these cards. Player 1 always consumes
positions 0–16, player 2 positions 17–33, regardless of request/display order.
"""
import hmac
import struct
from .protocol import PREFIX, deal_parameters, require, sha


def recreate_deck(commitment, secret, randomness, hand):
    """Recreate the specified HMAC stream and unbiased Fisher–Yates shuffle.

    A different hand number gives a different key. Domain tags separate the
    commitment, hand key, shuffle seed and random-word stream from each other.
    No platform random-number generator or Python random.shuffle is used.
    """
    size = commitment['deck_size']
    require(type(hand) is int and 0 < hand < 2**32, 'Invalid hand number')
    require(type(size) is int and 34 <= size <= 108, 'Invalid deck size')
    hand_key = hmac.digest(secret, PREFIX + b'hand\0' + struct.pack('>I', hand), 'sha256')
    seed = sha(PREFIX + b'seed\0' + hand_key + randomness
               + sha(commitment['game_id'].encode()) + sha(deal_parameters(commitment)) + struct.pack('>I', hand))

    def words():
        counter = 0
        while True:
            block = hmac.digest(seed, PREFIX + b'shuffle\0' + struct.pack('>Q', counter), 'sha256')
            yield from struct.unpack('>8I', block)
            counter += 1

    stream = words()
    deck = list(range(size))
    for i in range(size - 1, 0, -1):
        bound = i + 1
        # Reject the uneven tail: every accepted remainder has equal probability.
        limit = (2**32 // bound) * bound
        word = next(stream)
        while word >= limit:
            word = next(stream)
        j = word % bound
        deck[i], deck[j] = deck[j], deck[i]
    return deck


def build_hand_deals(deck, fantasy_cards):
    """Return every deal for each player: [player_1_deals, player_2_deals].

    Each entry in fantasy_cards is None for normal Pineapple, or the number
    of cards received in Fantasyland/Chinese (13–17). Those are user inputs;
    this script does not determine Fantasyland eligibility from past scoring.
    """
    require(len(deck) >= 34, 'The deck must contain both 17-card player lanes')
    require(len(fantasy_cards) == 2, 'Expected Fantasyland status for both players')
    hands = []
    for player, count in enumerate(fantasy_cards):
        if count is None:
            sizes = [5, 3, 3, 3, 3]
        else:
            require(type(count) is int and 13 <= count <= 17,
                    'Fantasyland/Chinese card count must be 13–17')
            sizes = [count]
        offset = player * 17
        deals = []
        for size in sizes:
            deals.append(deck[offset:offset + size])
            offset += size
        hands.append(deals)
    return hands
