import os
import time
import core.scores as recscore

def readscores():
    while True:
        recscore.Scores.read_scores()
        time.sleep(30)

readscores()

