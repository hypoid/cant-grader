import subprocess
import sys
import time

while True:
    process = subprocess.Popen("../Input/INPUT", stdout=subprocess.PIPE)
    for line in iter(process.stdout.readline, ''):
        if line != "0xFE\n":
            process.terminate()
            break
    print("Turning Output On")
    subprocess.call("../Output/OUTPUT")
    print("Output Turned Off")
