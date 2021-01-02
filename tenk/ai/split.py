import random as r
from typing import Optional
from tenk.ai.base import BaseTenkAi, BaseTenkPlayer


class DiceAi(BaseTenkAi):
    """
    Ai learning which dices to pick.
    """

    def __init__(self, alpha=0.0, gamma=0.0, randomness=0.0, rewardFkn=None):
        super().__init__(alpha, gamma, randomness, rewardFkn=rewardFkn)

    def init(self):
        super().init()
        self.keep = None
        self.lastKeep = None

    def encodeAction(self):
        return "".join([str(k) for k in self.keep])

    def decodeAction(self, action):
        return [int(s) for s in action]

    def encodeState(self):
        return "".join([str(dice) for dice in self.dices])

    def calculateReward(self):
        assert (
            self.score - self.lastScore >= 0
        )  # we cannot have negative scores for choosing dices
        return self.score - self.lastScore

    def act(self):
        """Return array of indexes with dices to keep"""
        self.lastKeep = self.keep
        currentRewards = self.Q.setdefault(self.state, {})
        # choose random dices if _randomness_ is true or there are no other valid paths
        if (
            (not currentRewards)
            or (r.random() < self.RANDOMNESS)
            or (max(currentRewards.values()) <= 0)
        ):
            keep = []
            while not keep:  # we need to select at least one dice
                keep = [i for i in range(len(self.dices)) if (r.random() > 0.2)]
            self.keep = keep
            action = self.encodeAction()
        else:
            action = max(currentRewards, key=currentRewards.get)
            self.keep = self.decodeAction(action)
        return action


class RollAi(BaseTenkAi):
    """
    Ai learning how often to re-roll the dices.
    """

    def __init__(self, alpha=0.0, gamma=0.0, randomness=0.0, rewardFkn=None):
        super().__init__(alpha, gamma, randomness, rewardFkn=rewardFkn)

    def encodeState(self):
        d = len(self.dices) if self.dices else 0
        a = len(self.args) if self.args else 0
        return str(d - a) + str(self.score)

    def decodeAction(self, action):
        return action

    def encodeAction(self):
        return self.finish

    def calculateReward(self):
        return self.score

    def act(self):
        # choose random dices if _randomness_ is true or there are no other valid paths
        action = self.selectAction(self.state)
        currentRewards = self.Q.setdefault(self.state, {})
        if (
            (not currentRewards)
            or (r.random() < self.RANDOMNESS)
            or (max(currentRewards.values()) <= 0)
        ):
            self.finish = r.getrandbits(1)  # todo: try other rand value
        else:
            self.finish = self.decodeAction(action)

        return self.finish


class SplitAiPlayer(BaseTenkPlayer):
    """
    TenK player using the `DiceAi`and the `RollAi`.
    """

    def __init__(
        self,
        diceai: DiceAi,
        rollai: RollAi,
        tag: str = "",
        load: Optional[int] = None,
        save: Optional[int] = None,
        exit: Optional[int] = None,
        progress: int = 100000,
    ):
        self.diceai = diceai
        self.rollai = rollai
        super().__init__(
            [diceai, rollai],
            tag=tag,
            load=load,
            save=save,
            exit=exit,
            progress=progress,
        )

    def choose(self, dices):
        self.cur_rolls += 1
        self.diceai.processGameState(
            dices, self.rollai.score
        )  # use score provided on finish()
        return self.diceai.keep

    def finish(self, score):
        self.rollai.processGameState(self.diceai.lastDices, score, self.diceai.keep)
        return bool(self.rollai.finish)

    def write(self, score):
        self.diceai.processFinalGameState(self.rollai.score)
        self.rollai.processFinalGameState(score)

        super().write(score)

        self.diceai.init()
        self.rollai.init()


def debug(tag, game):
    return SplitAiPlayer(diceai=DiceAi(), rollai=RollAi(), tag=tag, load=game)


def check(tag, max_game=10000000, step=1000000, sample_size=100000):
    print(tag)
    for game in range(step, max_game + 1, step):
        print("%8i: " % game, end="")
        play(
            SplitAiPlayer(
                diceai=DiceAi(),
                rollai=RollAi(),
                tag=tag,
                load=game,
                exit=game + sample_size,
                progress=sample_size,
            )
        )


def train(
    name,
    alpha=0.05,
    gamma=0.6,
    exp=0.1,
    max_games=10000000,
    step=1000000,
    progress=100000,
    tag=None,
    load=None,
):
    if not tag:
        tag = "%s_%s_%s_%s" % (
            name,
            str(alpha).replace(".", ""),
            str(gamma).replace(".", ""),
            str(exp).replace(".", ""),
        )
    play(
        SplitAiPlayer(
            diceai=DiceAi(alpha, gamma, exp),
            rollai=RollAi(alpha, gamma, exp),
            tag=tag,
            save=step,
            exit=max_games,
            progress=progress,
            load=load,
        )
    )
    return tag


def watch(tag=None, delay=1, alpha=0.1, gamma=0.6, exp=0.1, load=10000000, games=1000):
    play(
        SplitAiPlayer(
            diceai=DiceAi(alpha, gamma, exp),
            rollai=RollAi(alpha, gamma, exp),
            tag=tag,
            load=load,
            exit=load + games,
        ),
        doshow=True,
        delay=delay,
    )


if __name__ == "__main__":
    from tenk.game import play

    # r.seed(0)
    tag = train(name="v1")
    check(tag)

    watch("v1_005_06_01", games=3)

    # Q = debug("v2_005_06_01", 1000000).ai.Q
    # print(Q['111111_0'])
