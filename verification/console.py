"""Terminal prompts and display only. The cryptographic checks live elsewhere."""
import json
from pathlib import Path


def ask_for_json(label, read=input, write=print):
    """Accept the app's single-line JSON copy or a path to a saved JSON file."""
    while True:
        text = read(f'{label} (paste JSON or enter a file path): ').strip()
        try:
            if not text.startswith('{'):
                text = Path(text.strip('\"\'')).expanduser().read_text(encoding='utf-8')
            document = json.loads(text)
            if not isinstance(document, dict):
                raise ValueError('Expected a JSON object')
            return document
        except (OSError, ValueError) as error:
            write(f'Could not read the JSON: {error}. Please try again.')


def ask_hand_number(read=input, write=print):
    while True:
        text = read('\nHand number (or q to quit): ').strip()
        if text.lower() in ('q', 'quit', 'exit'):
            return None
        try:
            hand = int(text)
            if 1 <= hand < 2**32:
                return hand
        except ValueError:
            pass
        write('Enter a whole hand number from 1 to 4294967295.')


def ask_fantasyland(players, read=input, write=print):
    """Ask about each player separately; do not assume they share a mode/size."""
    counts = []
    for seat, name in enumerate(players, 1):
        while True:
            answer = read(f'Is player {seat} ({name}) in Fantasyland? [y/N]: ').strip().lower()
            if answer in ('y', 'yes', 'n', 'no', ''):
                break
            write('Please enter y or n.')
        if answer in ('n', 'no', ''):
            counts.append(None)
            continue
        while True:
            text = read(f'How many cards did {name} receive? (13–17) [14]: ').strip()
            try:
                count = int(text or '14')
                if 13 <= count <= 17:
                    counts.append(count)
                    break
            except ValueError:
                pass
            write('Enter a card count from 13 to 17.')
    return counts


def ask_first_player(players, read=input, write=print):
    while True:
        answer = read(f'Who was dealt to first? (1 = {players[0]}, 2 = {players[1]}): ').strip()
        if answer in ('1', '2'):
            return int(answer) - 1
        write('Please enter 1 or 2.')


def card_name(index):
    if 0 <= index < 52:
        rank = ('2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A')[index % 13]
        return rank + '♣♦♥♠'[index // 13]
    if 52 <= index <= 54:
        return f'Joker {index - 51}'
    return f'Card {index}'


def show_hand(hand, players, deals, fantasy_cards, first_player, write=print):
    """Display all deals, with the chosen starting player first in each deal.

    Starting order affects presentation only, never the canonical seat lanes.
    Fantasyland players appear once; normal players appear in all five deals.
    """
    write(f'\nHand {hand}')
    for player in (first_player, 1 - first_player):
        count = fantasy_cards[player]
        mode = 'Normal Pineapple' if count is None else f'Fantasyland/Chinese ({count} cards)'
        write(f'Player {player + 1} ({players[player]}): {mode}')
    for number in range(max(len(draws) for draws in deals)):
        write(f'\nDeal {number + 1}')
        for player in (first_player, 1 - first_player):
            if number < len(deals[player]):
                cards = deals[player][number]
                write(f"  {players[player]}: {' '.join(card_name(card) for card in cards)}")
                write(f'    Card indices: {cards}')
