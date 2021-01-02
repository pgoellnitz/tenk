import random as r
from typing import Optional
from tenk.ai.base import BaseTenkAi, BaseTenkPlayer


class SingleAi(BaseTenkAi):
    """
    Ai that uses one single dictionary to learn the game.
    """

    def __init__(self, alpha=0.0, gamma=0.0, randomness=0.0, rewardFkn=None):
        super().__init__(alpha, gamma, randomness, rewardFkn=rewardFkn)

    def init(self) -> None:
        super().init()
        self.keep = "N"
        self.finish = "N"

    def encodeState(self) -> any:
        return "".join([str(dice) for dice in self.dices]) + "_" + str(self.score)

    def encodeAction(self) -> any:
        return str(self.finish) + "".join([str(k) for k in self.keep])

    def decodeAction(self, action):
        return int(action[0]), [int(s) for s in action[1:]]

    def calculateReward(self) -> float:
        return self.score  # - self.lastScore

    def act(self):
        # pick next dices & finish
        currentRewards = self.Q.setdefault(self.state, {})
        if (
            (not currentRewards)
            or (r.random() < self.RANDOMNESS)
            or (max(currentRewards.values()) <= 0)  # just speeds up learning
        ):
            keep = []
            while not keep:  # keep at least one
                keep = [i for i in range(len(self.dices)) if (r.random() > 0.2)]
            self.finish = r.getrandbits(1)
            self.keep = keep
            action = self.encodeAction()
        else:
            action = max(currentRewards, key=currentRewards.get)
            finish, keep = self.decodeAction(action)
            self.finish = finish
            self.keep = keep
        return action


class SingleAiPlayer(BaseTenkPlayer):
    """
    TenK player using the `SingleAi`.
    """

    def __init__(
        self,
        ai: SingleAi,
        tag: str = "",
        load: Optional[int] = None,
        save: Optional[int] = None,
        exit: Optional[int] = None,
        progress: int = 100000,
    ):
        super().__init__(
            [ai], tag=tag, load=load, save=save, exit=exit, progress=progress
        )
        self.ai = ai
        self.GAMMA = ai.GAMMA

    def choose(self, dices):
        self.cur_rolls += 1
        self.ai.processGameState(dices, self.ai.score)
        return self.ai.keep

    def finish(self, score):
        self.ai.score = score
        return self.ai.finish

    def write(self, score):
        self.ai.processFinalGameState(score)
        self.ai.init()
        super().write(score)


def debug(tag, game):
    return SingleAiPlayer(SingleAi(), tag=tag, load=game)


def check(tag, max_game=10000000, step=1000000, sample_size=100000):
    print(tag)
    for game in range(step, max_game + 1, step):
        print("%8i: " % game, end="")
        play(
            SingleAiPlayer(
                SingleAi(),
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
        SingleAiPlayer(
            SingleAi(alpha, gamma, exp),
            tag=tag,
            save=step,
            exit=max_games,
            progress=progress,
            load=load,
        )
    )
    return tag


def watch(
    tag=None, delay=1, alpha=0.1, gamma=0.6, exp=0.1, load=10000000, games=1000
):
    play(
        SingleAiPlayer(
            SingleAi(alpha, gamma, exp),
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
