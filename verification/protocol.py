"""Game identity, public commitment and exact protocol byte encoding.

The hash binds the revealed seed to the saved game, seats, rules, deck size
and randomness mode (plus the selected round when using drand).
JSON formatting and key order never enter the hash.
"""
import hashlib
import hmac
import struct

DRAND_CHAIN_HASH = '52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971'
PREFIX = b'fantasy-land/verified-deals/v1/'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(value):
    return hashlib.sha256(value).digest()


def deal_parameters(public):
    """Unambiguous bytes for seats/rules/deck, unaffected by JSON formatting.

    For each string, write its UTF-8 byte length as a big-endian u32, then
    its bytes. The fixed order is player 1, player 2, rules, then u32 deck size.
    New exports append the randomness mode as another length-prefixed string.
    """
    encoded = bytearray()
    for value in [*public['players'], public['rules']]:
        text = value.encode('utf-8')
        encoded.extend(struct.pack('>I', len(text)))
        encoded.extend(text)
    encoded.extend(struct.pack('>I', public['deck_size']))
    # Older future-only exports omitted the mode; retain their original bytes.
    mode = public.get('randomness_mode')
    if mode is not None:
        text = mode.encode('utf-8')
        encoded.extend(struct.pack('>I', len(text)))
        encoded.extend(text)
    return bytes(encoded)



def verify_game_and_format(public, revealed):
    """Both separately entered documents must describe the same v1 game."""
    require(type(public.get('format_version')) is int and public['format_version'] == 1,
            'Unsupported public JSON format. Copy a current game export.')
    require(type(revealed.get('format_version')) is int and revealed['format_version'] == 1,
            'Unsupported revealed-secret JSON format.')
    require(public['game_id'] == revealed['game_id'],
            'The public JSON and revealed-secret JSON belong to different games.')
    if public.get('randomness_mode') == 'server':
        require(not any(key.startswith('drand_') for key in revealed),
                'Server-seed mode has no drand fields in its revealed export')


def verify_public_commitment(public, revealed_secret):
    """Bind the seed and every operator-chosen dealing input to the saved hash."""
    require(type(public['format_version']) is int and public['format_version'] == 1,
            'Unknown format version')
    mode = public.get('randomness_mode')
    require(mode in (None, 'server', 'future'), 'Unknown randomness mode')
    if mode == 'server':
        require(not any(key.startswith('drand_') for key in public),
                'Server-seed mode has no drand fields')
        round_number = 0
    else:
        require(public['drand_chain_hash'] == DRAND_CHAIN_HASH, 'Unknown drand chain')
        require(type(public['drand_round']) is int and 0 < public['drand_round'] < 2**64,
                'Invalid drand round')
        round_number = public['drand_round']
    require(isinstance(public['players'], list) and len(public['players']) == 2 and
            all(isinstance(p, str) and p for p in public['players']), 'Expected two player names')
    require(isinstance(public['rules'], str) and public['rules'], 'Missing dealing rules')
    require(type(public['deck_size']) is int and 34 <= public['deck_size'] <= 108, 'Invalid deck size')
    secret = bytes.fromhex(revealed_secret)
    require(len(secret) == 32, 'Secret must contain 32 bytes')
    root = sha(PREFIX + b'commitment\0' + secret + sha(public['game_id'].encode())
               + sha(deal_parameters(public)) + struct.pack('>Q', round_number)).hex()
    require(hmac.compare_digest(root, public['commitment_hash']),
            'Public hash does not match the revealed secret and committed inputs')
    return secret


