# Verify Fantasy Land deals

We want players to be able to check the deals for themselves. You shouldn’t have
to just take our word for it.

This is the independent Python script for
[Fantasy Land’s verifiable deals](https://github.com/fantasy-land-poker/verified-deals).
You run it on your own computer. It works with two JSON copies from the game:
one public copy you can save before playing, and a separate revealed-secret
copy that only becomes available when the whole game ends.

## How it works

Once enabled…

1. When a new game is created, our server generates a secret random seed for
   the game. It publishes a public cryptographic hash of that seed which
   players can save. Cards are not dealt yet…
2. At game creation, we also publish a future drand round we will use for
   randomness (drand is an independent, publicly verifiable source of
   randomness).
3. Once that drand round publishes (typically a few seconds), then we begin
   the game.
4. A published algorithm combines the secret seed, the drand value, and each
   hand’s number to determine its deck and card allocations. Because we
   committed beforehand, we cannot choose the seed afterward to produce
   favorable deals.
5. Once the entire game ends, we reveal the secret seed. You can use the secret
   seed and the published algorithm to verify that all deals are truly fair.
6. To check a deal, save the public JSON before playing. After the game, copy
   the revealed-secret JSON separately. Run this script, paste each at its own
   prompt. Enter the hand number, say whether each player was in Fantasyland,
   and choose who was dealt to first. It will show every deal for both players
   so you can compare them with what you received.

Notes:

- Off by default because it adds a short wait when creating a game. The
  implementation leaves a publication margin of around 3–6 seconds, plus the
  time to retrieve the drand value. Later hands use that same value.
- Applies only to new online games, including Pro/Ultra bots and multiplayer
  games. Easy bots run locally and are out of scope.
- We don’t store an extra verification history for every hand and deal. Players
  can save their own records if they want. The two JSON copies are enough to
  recreate the decks, including hands that weren’t finished.
- This is new and may have bugs, please report any issues. If you are
  unsatisfied or see issues with this verification scheme, we are happy to make
  changes.

## Run it

You need Python 3.10 or newer. Download this folder, open a terminal in it,
then install the one cryptography dependency in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python verify_deals.py
```

On Windows, use `.venv\Scripts\python` in place of `.venv/bin/python`, and
`.venv\Scripts\pip` in place of `.venv/bin/pip`.

The script asks for two separate inputs:

1. **Public JSON:** use **Verify deals → Copy Cryptographic Commitment** in the game
   menu. The waiting hand also has a **Copy public hash** button. Save this
   before play if you want to retain the original commitment.
2. **Revealed-secret JSON:** after the entire game ends, use **Copy Revealed
   Secret**. Paste that at the second prompt.

The **Copy Public Randomness** action copies the raw drand value for inspection.
For the script’s first prompt, use **Copy Cryptographic Commitment**, which copies the
complete public JSON.

Paste each complete JSON on its own line and press Enter. The public document
contains the commitment, the selected drand round and its public randomness.
Before the server receives that value, `drand_randomness` and `drand_signature`
are `null`. You can keep
that early copy: the later signed beacon still has to match its committed
round. A public value that was already filled in must match exactly.

Once the checks pass, the program asks about one hand at a time:

```text
Hand number (or q to quit): 12
Is player 1 (alice) in Fantasyland? [y/N]: y
How many cards did alice receive? (13–17) [14]: 14
Is player 2 (bob) in Fantasyland? [y/N]: n
Who was dealt to first? (1 = alice, 2 = bob): 2
```

It then prints **all deals for that hand**, with both player names, readable
cards (`A♠`, `7♥`, etc.) and raw card indices:

- Neither player in Fantasyland: five deals per player (5, 3, 3, 3, 3 cards).
- One player in Fantasyland: one full Fantasyland deal for that player, plus
  all five normal deals for the other player.
- Both players in Fantasyland: one full deal each, using each player’s own
  card count. The counts can differ.

For Chinese games, answer **yes for both players** and enter the card counts
you received. Fantasyland status and card count come from your own game record;
the script does not infer or verify eligibility from earlier scoring.

The first-dealt choice controls display order. The saved `players` array fixes
which seat owns each part of the shuffled deck, so changing this answer never
changes either player’s cards. The chosen player is simply shown first within
each deal. Fantasyland players appear only in their initial deal.

You can keep entering hand numbers, or enter `q` at the hand prompt to finish.
Press Ctrl+C to stop at any prompt. Invalid hand numbers, yes/no answers and
card counts are prompted again.

No source editing is needed. Input is collected when the program runs. At
either JSON prompt, you can also enter a path to a saved JSON file; that file
can be pretty-printed over multiple lines. The app’s copied JSON can be pasted
directly as one line. No game login is needed and verification makes no network
requests.

## What the script checks

- The revealed seed matches the hash from your separate public copy.
- The same hash also binds the game ID, seats, rules and selected drand round.
- The drand signature is valid under the pinned Quicknet public key.
- The script recreates the deterministic shuffle for the hand number you enter,
  then shows the cards from that player’s fixed part of the deck.

Compare those expected cards with what you observed or saved. The exports
contain no hand history, boards or discard transcripts. The script can’t
confirm what you actually saw on screen without your own record.

A proof copied only after a game cannot establish when the original hash was
published. Keeping the public JSON before the deal lets you witness that
commitment; an independent timestamp would provide stronger evidence. The
server’s own timestamps alone cannot prove this.

The cryptographic checks establish which decks follow from the commitment.
Equal hand strength, scoring, Fantasy Land eligibility, bots’ access to hidden
information, and a complete audit of cancelled games need separate checks.
Sharing the revealed secret exposes all decks from that finished game,
including discards and unused cards.

## For anyone reviewing the code

Start with **`verify_deals.py`**. Its main function deliberately reads as the
verification process, with run instructions at the top:

1. Read the public and revealed-secret JSON separately.
2. Check the game identity and format.
3. Verify the public commitment hash against the revealed seed.
4. Verify the drand signature and copied public randomness.
5. Ask about a hand, recreate its deck, allocate all deals, and print them.

The details are separated into small modules:

```text
verify_deals.py             Readable entry point and verification sequence
verification/protocol.py   Exact encoding, game identity and commitment hash
verification/drand.py      Pinned Quicknet key and BLS signature checks
verification/deals.py      Deterministic shuffle and all card allocations
verification/console.py    User prompts and card display
tests/                     Optional security and interactive-program tests
```

Python’s standard library handles SHA-256 and HMAC. The single direct dependency,
`py-ecc==8.0.0`, verifies the drand BLS signature. The chain hash and public key
are pinned in the helper modules. The script never downloads or executes code
from the game server. No tests or sample data are loaded by the entry point.

The public JSON is flat, with one name for each value:

```json
{
  "format_version": 1,
  "game_id": "...",
  "players": ["alice", "bob"],
  "rules": "standard",
  "deck_size": 52,
  "commitment_hash": "...",
  "drand_chain_hash": "52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971",
  "drand_round": 123,
  "drand_randomness": null,
  "drand_signature": null
}
```

`commitment_hash` is the promise for this game. `drand_chain_hash` identifies
which drand network we use; the verifier checks it against its pinned Quicknet
identity. `rules` is the variant name, or a canonical custom-rules slug for a
custom game. `deck_size` includes any jokers. The format version also fixes the
shuffle and fixed-lane allocation algorithm.

Only the final two fields become populated when drand publishes. No duplicate
hash, escaped JSON string, separate schema name or calculated timestamp is
needed. The revealed-secret JSON is also flat: `format_version`, `game_id`,
`revealed_secret`, `drand_randomness` and `drand_signature`.

JSON field order, spacing and indentation do not affect the hashes. We define
an exact binary encoding instead. Let `P` be `fantasy-land/verified-deals/v1/`,
`S` the 32-byte secret, `G` the UTF-8 game ID, `R` the drand round, and `N` the
hand number. Every integer is unsigned and big-endian. Encode each string as
its UTF-8 byte length (u32), followed by its UTF-8 bytes. Then:

```text
D          = string(player_1) || string(player_2) || string(rules) || u32(deck_size)
commitment = SHA256(P || "commitment\0" || S || SHA256(G) || SHA256(D) || u64(R))
hand_key   = HMAC-SHA256(S, P || "hand\0" || u32(N))
randomness = SHA256(validated drand signature bytes)
seed       = SHA256(P || "seed\0" || hand_key || randomness || SHA256(G) || SHA256(D) || u32(N))
block[k]   = HMAC-SHA256(seed, P || "shuffle\0" || u64(k)), starting at k = 0
```

Each block supplies eight big-endian 32-bit words. Fisher–Yates shuffles the
ordered deck by swapping from its end. For a bound `b`, words at or above
`floor(2^32 / b) * b` are rejected; accepted words select `word % b`. This avoids
modulo bias. Player 1 receives cards 0–16 of the shuffled deck, player 2 cards
17–33, each consuming their own portion in order. Card indices 0–51 are clubs,
diamonds, hearts, spades, with ranks 2 through ace. Indices 52–54 are jokers.

Run the included known-vector and tampering tests:

```sh
.venv/bin/python -m unittest discover -v
```

There is no separate fixtures folder. A small known example in
`tests/sample_game.py` uses a historical drand round for repeatable signature
and shuffle tests. It does not claim that its test commitment was published
before that round. These values match the Rust protocol’s reference vector.

References: [drand documentation](https://docs.drand.love/developer/),
[drand signature verification](https://github.com/drand/drand-client/blob/master/lib/beacon-verification.ts),
[py-ecc](https://github.com/ethereum/py_ecc).
