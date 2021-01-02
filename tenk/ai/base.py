import pickle
from tenk.game import Player
from statistics import mean
from typing import Dict, List, Optional
import time


class BaseAi(object):
    """
    Base Q-learning ai implementation.
    """

    DEFAULT_REWARD_FKN = lambda x: max(x.values()) if x.values() else 0.0

    def __init__(self, alpha: float, gamma: float, rewardFkn=None):
        self.Q = {}
        self.ALPHA = alpha
        self.GAMMA = gamma
        self.REWARD_FKN = rewardFkn if rewardFkn else BaseAi.DEFAULT_REWARD_FKN

    def load(self, filename: str) -> None:
        """Load a pickeled Q dictionary."""
        with open(filename, "rb") as file:
            self.Q = pickle.load(file)

    def save(self, filename: str) -> None:
        """Save a pickeled Q dicktionary."""
        with open(filename, "wb") as file:
            pickle.dump(self.Q, file)

    def compress(self, single_value=True):
        """
        Compress the Q dictionary by removing all zero values.
        If `single_value` is `True` only keep the action with the highest reward.
        """
        compressed_Q = {}
        for q_key in self.Q:
            if single_value and self.Q[q_key]:
                v_key = max(self.Q[q_key], key=self.Q[q_key].get)
                compressed_Q.setdefault(q_key, {})[v_key] = 1
            else:
                for v_key in self.Q[q_key]:
                    if self.Q[q_key][v_key] != 0:
                        compressed_Q.setdefault(q_key, {})[v_key] = self.Q[q_key][v_key]
        self.Q = compressed_Q

    def estimateReward(self, state: any) -> float:
        """Estimate the reward for a state based on the defined reward function."""
        return self.REWARD_FKN(self.getRewards(state))

    def getRewards(self, state: any) -> Dict[any, float]:
        """Return all rewards for a state"""
        return self.Q.setdefault(state, {})

    def updateReward(
        self, cur_state: any, prev_state: any, prev_action: any, reward: float
    ) -> None:
        """
        Updates rewards of _previous state_ based on _current state_ values and reward.
        """
        prevRewards = self.getRewards(prev_state)
        prevRewards[prev_action] = (1 - self.ALPHA) * prevRewards.setdefault(
            prev_action, 0
        ) + self.ALPHA * (reward + self.GAMMA * self.estimateReward(cur_state))
        self.Q[prev_state] = prevRewards


class BaseTenkAi(BaseAi):
    """
    Base implementation of a ai playing TenK.
    """

    def __init__(self, alpha: float, gamma: float, randomness: float, rewardFkn=None):
        super().__init__(alpha, gamma, rewardFkn=rewardFkn)
        self.RANDOMNESS = randomness
        self.init()

    def init(self) -> None:
        """Reset AI to initial state"""
        self.lastState = "il"
        self.lastAction = None
        self.lastScore = 0
        self.lastArgs = None
        self.dices = None
        self.score = 0
        self.state = "is"
        self.args = None

    def encodeState(self) -> any:
        """Encode current state for storing in Q"""
        raise NotImplementedError

    def encodeAction(self) -> any:
        """Encode action for storing in Q"""
        raise NotImplementedError

    def calculateReward(self) -> float:
        """Calculate reward to store in Q"""
        raise NotImplementedError

    def selectAction(self, state: any) -> any:
        """Selects the action to take for a state stored in Q"""
        rewards = self.getRewards(state)
        # print("Choose %s: %s -> %s" % (state, str(rewards), str(max(rewards, key=rewards.get) if rewards else None)))
        return max(rewards, key=rewards.get) if rewards else None

    def updateReward(self) -> None:
        """Update reward from current ai values"""
        # _start_reward = dict(self.getRewards(self.lastState))
        super().updateReward(
            self.state, self.lastState, self.lastAction, self.calculateReward()
        )
        # print("    %s %s[%s]>%i: %.2f -> %.2f | %.2f" % (self.__class__.__name__, self.lastState,  self.lastAction,self.score, _start_reward[self.lastAction], self.getRewards(self.lastState)[self.lastAction], self.GAMMA * self.estimateReward(self.state)))

    def processGameState(self, dices: List[int], score: int, args: any = None) -> None:
        """
        Process a TenK game state while still playing the round. Not a final state
        ending the players turn (e.g. when no further moves are possible or the player
        decides to write down the score).
        """
        self.args = args
        self.dices = dices
        self.score = score
        self.state = self.encodeState()

        self.updateReward()
        self.lastAction = self.act()

        self.lastArgs = args
        self.lastDices = dices
        self.lastScore = score
        self.lastState = self.state

    def processFinalGameState(self, score) -> None:
        """
        Process a final TenK game state ending the players turn.
        """
        self.score = score
        gamma = self.GAMMA
        self.GAMMA = 0
        self.updateReward()
        self.GAMMA = gamma

    def act(self) -> any:
        """
        Take an game action. Returns the game action.
        """
        raise NotImplementedError


class BaseTenkPlayer(Player):
    """
    Base ai TenK player implementation.
    """

    def filename(self, ai: BaseTenkAi) -> str:
        return "./Q/%s_%s_%i.pickle" % (ai.__class__.__name__, self.TAG, self.games)

    def __init__(
        self,
        ais: List[BaseTenkAi],
        tag: str = "",
        load: Optional[int] = None,
        save: Optional[int] = None,
        exit: Optional[int] = None,
        progress: int = 100000,
    ):
        self.SAVE = save
        self.TAG = tag
        self.EXIT = exit
        self.PROGRESS = progress

        self.end = False
        self.games = load if load else 0

        self.scores = []
        self.maxscore = 0
        self.old_mean = 1
        self.rolls = []
        self.cur_rolls = 0
        self.start_time = time.time()

        self.ais = ais
        if load:
            for ai in ais:
                ai.load(self.filename(ai))

    def choose(self, score: int, dices: List[int]) -> List[int]:
        raise NotImplementedError

    def finish(self, score: int) -> bool:
        raise NotImplementedError

    def write(self, score):
        self.games += 1
        self.scores.append(score)
        self.rolls.append(self.cur_rolls)
        self.cur_rolls = 0
        if score > self.maxscore:
            self.maxscore = score
        if self.games % self.PROGRESS == 0:
            mymean = round(mean(self.scores))
            print(
                "%3i[%3i] - %2i/%.2f - %4i - %s | %.2f"
                % (
                    mymean,
                    mymean - self.old_mean,
                    max(self.rolls),
                    mean(self.rolls),
                    self.maxscore,
                    str("/".join([str(len(ai.Q)) for ai in self.ais])),
                    time.time() - self.start_time,
                )
            )
            self.old_mean = round(mean(self.scores))
            self.scores = []
            self.rolls = []
            self.maxscore = 0
            self.start_time = time.time()
        if self.SAVE and (self.games % self.SAVE == 0):
            for ai in self.ais:
                print("Saving %s" % self.filename(ai))
                ai.save(self.filename(ai))
        if self.EXIT and self.games >= self.EXIT:
            self.end = True
