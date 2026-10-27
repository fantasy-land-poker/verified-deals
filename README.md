# Verify Upper Hand Deals

Allows you to verify any deal across an [Upper Hand](https://www.playupperhand.com) game once the "Verified Deals" features is enabled.

Once enabled, all deals are determined through a published algorithm that takes 
both a pre-commited cryptgraphic hash and a future public source of randomness (DRand).

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
