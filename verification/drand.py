"""Verify Quicknet's BLS signature and the copied public randomness.

The public key is pinned here. No key or code is downloaded from the game
server, and no network request is made during verification.
"""
import hashlib
import struct
from .protocol import DRAND_CHAIN_HASH, require, sha

QUICKNET_PUBLIC_KEY = '83cf0f2896adee7eb8b5f01fcad3912212c437e0073e911fb90022d3e760183c8c4b450b6a0a6c3ac6a5776a2d1064510d1fec758c921cc22b0e17e63aaf4bcb5ed66304de9cf809bd274ca73bab4af5a6e9c76a4bc09e76eae8991ef5ece45a'


def verify_signature(signature_hex, round_number):
    """Validate Quicknet's unchained BLS signature, then hash it for randomness.

    Quicknet uses a G1 signature and a G2 public key. Reject infinity and
    non-prime-order points before checking the pairing equation. The hashed
    message and domain tag below are part of drand's published scheme.
    """
    from py_ecc.bls.hash_to_curve import hash_to_G1
    from py_ecc.bls.point_compression import decompress_G1, decompress_G2
    from py_ecc.optimized_bls12_381 import G2, curve_order, is_inf, multiply, pairing

    require(type(round_number) is int and 0 < round_number < 2**64, 'Invalid drand round')
    signature = bytes.fromhex(signature_hex)
    require(len(signature) == 48, 'Invalid Quicknet signature length')
    public_key = bytes.fromhex(QUICKNET_PUBLIC_KEY)
    pk = decompress_G2((int.from_bytes(public_key[:48], 'big'), int.from_bytes(public_key[48:], 'big')))
    sig = decompress_G1(int.from_bytes(signature, 'big'))
    require(not is_inf(pk) and not is_inf(sig), 'Point at infinity')
    require(is_inf(multiply(sig, curve_order)), 'Signature outside prime-order subgroup')
    require(is_inf(multiply(pk, curve_order)), 'Public key outside prime-order subgroup')
    message = sha(struct.pack('>Q', round_number))
    hashed = hash_to_G1(message, b'BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_NUL_', hashlib.sha256)
    require(pairing(pk, hashed) == pairing(G2, sig), 'Invalid Quicknet signature')
    return sha(signature)


def verify_drand_beacon(public, private):
    """The signature must validate for the round chosen in the PUBLIC copy.

    A pre-beacon public copy has null values; a populated copy must match the
    revealed document exactly. None means the game ended before receiving a beacon.
    """
    require(public.get('randomness_mode') != 'server', 'Server-seed mode does not use drand')
    require(public['drand_chain_hash'] == DRAND_CHAIN_HASH, 'Unknown drand chain')
    signature = private['drand_signature']
    if signature is None:
        require(public['drand_signature'] is None and public['drand_randomness'] is None
                and private['drand_randomness'] is None, 'Missing signed drand value')
        return None
    randomness = verify_signature(signature, public['drand_round'])
    require(private['drand_randomness'] == randomness.hex(), 'Revealed drand value mismatch')
    require(public['drand_randomness'] is None or public['drand_randomness'] == randomness.hex(),
            'Public randomness changed')
    require(public['drand_signature'] is None or public['drand_signature'] == signature,
            'Public drand signature changed')
    return randomness

