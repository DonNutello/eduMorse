#!/usr/bin/python3

import os
import subprocess
import sys
import time

EDUMORSEPATH = os.environ.get("EDUMORSEPATH")
SERVERPATH = os.path.join(EDUMORSEPATH, "socket")
SCOREPATH = os.path.join(EDUMORSEPATH, "score")

if len(sys.argv) != 2:
    print("Wrong number of parameters")
    sys.exit(1)

server = subprocess.Popen("python3 {} {}".format(os.path.join(SERVERPATH, "server.py"), sys.argv[1]).split(" "))
print("server.py is running")
time.sleep(1)

collision = subprocess.Popen("python3 {}".format(os.path.join(SCOREPATH, "collision.py")).split(" "))
print("collision.py is running")
time.sleep(1)

start = input("Type 'start' to count the score and to begin game: ")
if start == 'start':
    controller = subprocess.Popen("python3 {} {}".format(os.path.join(SCOREPATH, "controller.py"), sys.argv[1]).split(" "))
    print("controller.py is running")
    time.sleep(1)

    viz = subprocess.Popen("python3 {}".format(os.path.join(SCOREPATH, "viz.py")).split(" "))
    print("viz.py is running")
    time.sleep(1)

    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        collision.terminate()
        time.sleep(1)

        controller.terminate()
        time.sleep(1)

        viz.terminate()
        time.sleep(1)

        server.terminate()
        time.sleep(1)
else:
    print('Wrong command')
    collision.terminate()
    time.sleep(1)

    server.terminate()
    time.sleep(1)
