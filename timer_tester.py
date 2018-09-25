import time
import visutil

timer = visutil.simple_timer(3.0)

print("Waiting")
while True:
    if timer.is_done():
        print("Time's up, resetting timer")
        timer.restart()
