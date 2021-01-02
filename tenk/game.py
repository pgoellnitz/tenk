import random as r
from collections import Counter
import time
from typing import List

console_output = False


def show(x="", delay=0):
    """Print something for human interaction if `console_output` is set `True`."""
    if console_output:
        print(x)
        time.sleep(delay)


def roll(num_dice=6):
    """Roll the dices."""
    return sorted([r.randint(1, 6) for dice in range(num_dice)])


def splitdices(dices, keep):
    return [
        [dices[i] for i in range(len(dices)) if i not in keep],
        [dices[i] for i in keep],
    ]


def calculate(dices, keep):
    """
    Calculate the score for the chosen dices.
    Returns: score, dices for next round
    """
    if not keep:
        raise ValueError("No keep")
    next_dices, kept_dices = splitdices(dices, keep)
    counters = Counter(kept_dices)
    score = 0
    for points in counters.keys():
        counter = counters[points]
        if points == 1:
            if counter < 3:
                score += counter * 100
            else:
                score += (counter - 2) * 1000
        elif points == 5:
            if counter < 3:
                score += counter * 50
            else:
                score += (counter - 2) * 500
        else:
            if counter < 3:
                raise ValueError(str("points: %i, counter: %i" % (points, counter)))
            else:
                score += (counter - 2) * 100 * points
    return score, next_dices


def valid_moves(dices):
    """Check if there are valid moves possible with the given dices."""
    counters = Counter(dices)
    return (
        counters[1] > 0
        or counters[5] > 0
        or counters[2] > 2
        or counters[3] > 2
        or counters[4] > 2
        or counters[6] > 2
    )


def play(player, num_dices=6, delay=0, doshow=False):
    """Play a game."""
    global console_output
    console_output = doshow
    while not player.end:  # game loop
        score = 0
        finish = False
        dices = []
        while not finish:
            # roll dices
            if not dices:
                dices = roll(num_dices)
            else:
                dices = roll(len(dices))
            d = dices
            show("Roll: %s" % dices, delay)
            if not valid_moves(dices):
                show("  no valid moves %s" % dices)
                player.write(0)
                show("Final score: 0", delay * 5)
                show()
                break

            # choose dices to keep
            keep = player.choose(dices)
            show("  Keep: %s" % ([dices[i] for i in keep]), delay)
            # calculate score
            try:
                result = calculate(dices, keep)
                score += result[0]
                dices = result[1]
                show("  Score +%i -> %i" % (result[0], score), delay)
                finish = player.finish(score)
                show("  Finish: %s" % finish, delay)
            except ValueError:
                player.write(0)
                show("  wrong move!!!")
                show("Final score: 0", delay * 5)
                show()
                break
            if finish:
                player.write(score)
                show("Final score: %i" % score, delay * 5)
                show()


class Player(object):
    """TenK player interface."""

    def __init__(self) -> None:
        self.end = False

    def choose(self, dices: List[int]):
        """
        Choose dices. Return array of indexes which dices to keep for scoring.
        """
        raise NotImplementedError

    def finish(self, score: int) -> bool:
        """
        Return `True` if the player wants to finish his round with the given score.
        """
        raise NotImplementedError

    def write(self, score: int):
        """
        (Write down) the final score achieved.
        """
        raise NotImplementedError


class HumanPlayer(Player):
    """Human TenK player implementation."""

    def choose(self, dices):
        return [int(i) - 1 for i in input("Choose dices: ").split(",")]

    def finish(self, score):
        return True if input("Finish [y/N]: ") == "y" else False

    def write(self, score):
        pass


if __name__ == "__main__":
    play(HumanPlayer(), doshow=True)
