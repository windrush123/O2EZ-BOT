import os

class Formula():
    def scorev2(cool, good, bad, miss, notecount):
        score = 1000000*(cool+0.1*good-bad-3*miss)/notecount
        if score > 0: return score
        else: return 0

    def notecount_to_accuracy(cool, good, bad, miss, notecount):
        # hitcount = int(cool) + int(good) + int(bad) + int(miss)
        return ((200*cool)+(150*good)+(50*bad))/(200*notecount)*100

    def hitcount_to_accuracy(cool, good, bad, miss):
        hitcount = int(cool) + int(good) + int(bad) + int(miss)
        return ((200*cool)+(150*good)+(50*bad))/(200*hitcount)*100   
    
# Formula by Schoolgirl