import copy
import json
from pathlib import Path
import unittest

from verification.protocol import verify_game_and_format, verify_public_commitment
from verification.drand import verify_signature, verify_drand_beacon
from verification.deals import recreate_deck, build_hand_deals
from verification.console import ask_hand_number, ask_fantasyland, ask_first_player, ask_for_json, show_hand
from tests.sample_game import SAMPLE
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def verify_exports(public, private):
    # The same explicit verification sequence as the entry file.
    verify_game_and_format(public, private)
    secret = verify_public_commitment(public, private['revealed_secret'])
    return public, secret, verify_drand_beacon(public, private)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = copy.deepcopy(SAMPLE)

    def exports(self, pending=False):
        public = copy.deepcopy(self.fixture['public'])
        if pending:
            public['drand_randomness'] = None
            public['drand_signature'] = None
        return public, copy.deepcopy(self.fixture['revealed'])

    def test_known_vector_without_any_exported_hand_history(self):
        public, private = self.exports()
        c, secret, random = verify_exports(public, private)
        deck = recreate_deck(c, secret, random, 12)
        self.assertEqual(sorted(deck), list(range(52)))
        self.assertEqual(build_hand_deals(deck, [14, 14])[0][0], self.fixture['expected_player_cards'][0])
        self.assertEqual(build_hand_deals(deck, [14, 14])[1][0], self.fixture['expected_player_cards'][1])
        self.assertNotIn('hands', private)
        self.assertNotIn('deals', private)

    def test_changed_committed_inputs_are_rejected(self):
        for key, value in [('players', ['bob', 'alice']), ('rules', 'joker'),
                           ('deck_size', 54), ('drand_round', 124), ('game_id', 'other-game'),
                           ('drand_chain_hash', '00' * 32), ('format_version', 2)]:
            public, private = self.exports()
            public[key] = value
            with self.assertRaises(ValueError):
                verify_exports(public, private)
        public, private = self.exports()
        private['revealed_secret'] = 'ff' * 32
        with self.assertRaises(ValueError):
            verify_exports(public, private)

    def test_wrong_round_and_forged_signature_rejected(self):
        with self.assertRaises(ValueError):
            verify_signature(self.fixture['revealed']['drand_signature'], 124)
        public, private = self.exports(pending=True)
        private['drand_signature'] = '00' * 48
        with self.assertRaises(ValueError):
            verify_exports(public, private)

    def test_json_order_and_whitespace_do_not_change_decks(self):
        public, private = self.exports()
        reordered = json.loads(json.dumps(dict(reversed(list(public.items()))), indent=2))
        c, secret, random = verify_exports(reordered, private)
        deck = recreate_deck(c, secret, random, 12)
        self.assertEqual(deck[:14], self.fixture['expected_player_cards'][0])

    def test_both_normal_players_receive_five_disjoint_deals(self):
        deals = build_hand_deals(list(range(52)), [None, None])
        self.assertEqual([len(d) for d in deals[0]], [5, 3, 3, 3, 3])
        self.assertEqual(deals[0][0], [0, 1, 2, 3, 4])
        self.assertEqual(deals[1][-1], [31, 32, 33])
        self.assertEqual([c for d in deals[0] for c in d], list(range(17)))
        self.assertEqual([c for d in deals[1] for c in d], list(range(17, 34)))

    def test_both_fantasyland_players_receive_one_deal(self):
        deals = build_hand_deals(list(range(52)), [14, 17])
        self.assertEqual(deals, [[list(range(14))], [list(range(17, 34))]])

    def test_mixed_modes_keep_each_players_lane_fixed(self):
        deck = list(range(52))
        normal = build_hand_deals(deck, [None, None])
        for counts, normal_player in [([14, None], 1), ([None, 15], 0)]:
            deals = build_hand_deals(deck, counts)
            self.assertEqual(deals[normal_player], normal[normal_player])
            self.assertEqual(len(deals[1 - normal_player]), 1)
        for counts in [[12, None], [None, 18], [True, None], [14]]:
            with self.assertRaises(ValueError):
                build_hand_deals(deck, counts)

    def test_one_secret_derives_any_practical_hand_number(self):
        c, secret, random = verify_exports(*self.exports())
        self.assertNotEqual(recreate_deck(c, secret, random, 1),
                            recreate_deck(c, secret, random, 2))
        self.assertEqual(len(recreate_deck(c, secret, random, 2**32 - 1)), 52)
        with self.assertRaises(ValueError):
            recreate_deck(c, secret, random, 0)

    def run_program(self, public, private, answers):
        return subprocess.run([sys.executable, str(ROOT / 'verify_deals.py')],
            input=json.dumps(public) + '\n' + json.dumps(private) + '\n' + answers,
            text=True, capture_output=True, cwd=ROOT, timeout=30)

    def test_program_prompts_and_prints_every_deal_for_multiple_hands(self):
        public, private = self.exports(pending=True)
        # Hand 12: alice in FL14, bob normal, bob dealt first.
        # Hand 1: both in FL (13 and 17), alice dealt first.
        result = self.run_program(public, private, '12\ny\n14\nn\n2\n1\ny\n13\ny\n17\n1\nq\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Public commitment hash verified.', result.stdout)
        self.assertIn('drand signature and public randomness verified.', result.stdout)
        self.assertEqual(result.stdout.count('Card indices:'), 8)
        self.assertIn(str(self.fixture['expected_player_cards'][0]), result.stdout)
        self.assertIn('Hand 12\nPlayer 2 (bob): Normal Pineapple\nPlayer 1 (alice)', result.stdout)
        self.assertEqual(result.stdout.count('\nDeal 5\n'), 1)

    def test_first_dealt_changes_output_order_not_cards(self):
        deals = build_hand_deals(list(range(52)), [14, None])
        outputs = []
        for first in [0, 1]:
            lines = []
            show_hand(1, ['alice', 'bob'], deals, [14, None], first, write=lines.append)
            outputs.append(lines)
        self.assertEqual(sorted(outputs[0]), sorted(outputs[1]))
        self.assertTrue(outputs[0][1].startswith('Player 1'))
        self.assertTrue(outputs[1][1].startswith('Player 2'))
        self.assertEqual(outputs[0][outputs[0].index('\nDeal 1') + 1].split(':')[0], '  alice')
        self.assertEqual(outputs[1][outputs[1].index('\nDeal 1') + 1].split(':')[0], '  bob')

    def test_invalid_answers_are_reprompted(self):
        output = []
        answers = iter(['0', 'not a number', '12'])
        self.assertEqual(ask_hand_number(read=lambda _: next(answers), write=output.append), 12)
        answers = iter(['maybe', 'yes', '18', 'oops', '15', 'no'])
        self.assertEqual(ask_fantasyland(['alice', 'bob'], read=lambda _: next(answers), write=output.append), [15, None])
        answers = iter(['0', '2'])
        self.assertEqual(ask_first_player(['alice', 'bob'], read=lambda _: next(answers), write=output.append), 1)

    def test_json_prompt_also_accepts_saved_files(self):
        public, _ = self.exports()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'public.json'
            path.write_text(json.dumps(public, indent=2), encoding='utf-8')
            answers = iter(['{bad json}', str(path)])
            self.assertEqual(ask_for_json('Public JSON', read=lambda _: next(answers), write=lambda _: None), public)

    def test_invalid_commitment_stops_before_hand_questions(self):
        public, private = self.exports()
        public['commitment_hash'] = 'ff' * 32
        result = self.run_program(public, private, '')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Verification failed', result.stderr)
        self.assertNotIn('Hand number', result.stdout)

    def test_public_json_saved_before_beacon_is_usable(self):
        c, _, random = verify_exports(*self.exports(pending=True))
        self.assertEqual(c['drand_round'], 123)
        self.assertEqual(c['players'], ['alice', 'bob'])
        self.assertEqual(len(random), 32)

    def test_separate_public_anchor_cannot_be_substituted(self):
        for target, key, value in [('private', 'game_id', 'other-game'),
                                   ('private', 'drand_randomness', '00' * 32),
                                   ('public', 'drand_randomness', '00' * 32),
                                   ('public', 'commitment_hash', 'ff' * 32)]:
            public, private = self.exports()
            (public if target == 'public' else private)[key] = value
            with self.assertRaises(ValueError):
                verify_exports(public, private)

    def test_game_ended_before_beacon(self):
        public, private = self.exports(pending=True)
        private['drand_signature'] = None
        private['drand_randomness'] = None
        result = self.run_program(public, private, '')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('no cards were dealt', result.stdout)
        self.assertNotIn('Hand number', result.stdout)



if __name__ == '__main__':
    unittest.main()
