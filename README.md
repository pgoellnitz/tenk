# Ten-Thousand / Zehntausend

First try at reinforcement leaning with [Q-learning](https://en.wikipedia.org/wiki/Q-learning) for the dice game _Ten-Thousand_ ([Zehntausend](https://de.wikipedia.org/wiki/Zehntausend_(Spiel))).

## Examples

### Playing the game interactively

```shell
python ./tenk/game.py
```

### Train/Watch single model AI

Train and watch the ai play the game for an AI that processes all states and actions in a single dictionary.

```shell
python ./tenk/ai/single.py
```


### Train/Watch split model AI

Train and watch the ai play the game for an AI that processes all states and actions separately for choosing dices and choosing to re-roll.

```shell
python ./tenk/ai/split.py
```
