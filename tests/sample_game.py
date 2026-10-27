"""Historical test data shared with the Rust protocol's known vector.

This seed is deliberately public. Round 123 is used for repeatable signature
checks; no claim is made that this test commitment predated that round.
Production code never imports this module.
"""

SAMPLE = {'public': {'format_version': 1,
            'game_id': 'v1-known-vector',
            'players': ['alice', 'bob'],
            'rules': 'standard',
            'deck_size': 52,
            'commitment_hash': '40d685fd922e4f8f0f06d01e1e5707351d2f2a34477de787c7a83a1f494d9820',
            'drand_chain_hash': '52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971',
            'drand_round': 123,
            'drand_randomness': 'fb8f7bc29bf24db51871ec8c79f3a1e4bd0557bc0dfcee9ed1d924e69d1c60dc',
            'drand_signature': 'b75c69d0b72a5d906e854e808ba7e2accb1542ac355ae486d591aa9d43765482e26cd02df835d3546d23c4b13e0dfc92'},
 'revealed': {'format_version': 1,
              'game_id': 'v1-known-vector',
              'revealed_secret': '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f',
              'drand_randomness': 'fb8f7bc29bf24db51871ec8c79f3a1e4bd0557bc0dfcee9ed1d924e69d1c60dc',
              'drand_signature': 'b75c69d0b72a5d906e854e808ba7e2accb1542ac355ae486d591aa9d43765482e26cd02df835d3546d23c4b13e0dfc92'},
 'hand': 12,
 'expected_player_cards': [[9, 24, 39, 34, 10, 13, 40, 30, 16, 17, 14, 44, 48, 38],
                           [0, 32, 7, 18, 43, 22, 37, 50, 2, 41, 1, 47, 8, 51]]}
