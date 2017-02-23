import json
import pymorse
import pytoml as toml
import os
import select
import socket
import sys
import time

# control if a file exists
def findFileInPath(filename, extension, paths):
    for path in paths:
        if os.path.exists(os.path.join(path, filename)):
            return os.path.join(path, filename)
        elif os.path.exists(os.path.join(path, filename + '.' + extension)):
            return os.path.join(path, filename + '.' + extension)
    raise FileNotFoundError('File ' + filename + ' not found')

# find the path of a simulation starting from the simulation name
def findSimuPath(simuName):
    with open(os.path.join(MORSECONFIGPATH, 'config'), 'r') as config:
        for line in config:
            if simuName in line:
                lineList = line.split(' = ')
                return lineList[1].strip('\n')
        return None

def checkStopMode(stopMode, scoreUntilZeroPoints, scoreUntilNoTime):
    stopMode = stopMode.lower()
    if stopMode == 'stopwhenzeropoints':
        scoreUntilZeroPoints = True
        scoreUntilNoTime = False
        return [scoreUntilZeroPoints, scoreUntilNoTime]
    elif stopMode == 'stopwhennotime':
        scoreUntilZeroPoints = False
        scoreUntilNoTime = True
        return [scoreUntilZeroPoints, scoreUntilNoTime]
    else:
        raise ValueError("Wrong value in 'simulationStopMode'")

def strToInt(s):
    try:
        i = int(s)
    except ValueError:
        print('Wrong input')
        raise
    return i

def receive(conn):
    data = b''
    word = b''
    while word != b'\x04':
        data += word
        word = conn.recv(1)
    message = data.decode('utf-8')
    message = json.loads(message)
    return message

def send_layer(robot, score, stop, socket):
    message = {robot : {"score" : score, "stop" : stop}}
    message = json.dumps(message)
    message = message + '\x04'
    socket.sendall(message.encode('utf-8'))

def send(msg, socket):
    message = json.dumps(msg)
    message = message + '\x04'
    socket.sendall(message.encode('utf-8'))

def messageInSocket(s):
    read_list, _, _ = select.select([s], [], [], 0)
    if read_list == []:
        return False
    else:
        return True

def stopRobot(simu, robot):
    components = simu.__dict__[robot]
    for c in components:
        deact = robot + "." + c
        try:
            simu.deactivate(deact)
        except pymorse.MorseServiceFailed:
            pass

MORSECONFIGPATH = os.path.join(os.environ['HOME'], '.morse/')
EDUMORSEPATH = os.environ.get("EDUMORSEPATH")
GAMESPATH = os.path.join(EDUMORSEPATH, "games")
HOST_COLLISION = os.environ.get("EDUMORSE_COLLISION_HOST")
PORT_COLLISION = int(os.environ.get("EDUMORSE_COLLISION_PORT"))
HOST_CONTROLLER = os.environ.get("EDUMORSE_CONTROLLER_HOST")
PORT_CONTROLLER = int(os.environ.get("EDUMORSE_CONTROLLER_PORT"))
HOST_SERVER = os.environ.get("EDUMORSE_SERVER_HOST")
PORT_SERVER = int(os.environ.get("EDUMORSE_SERVER_PORT"))

if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 4:
        raise Exception('Wrong number of parameters')

    SIMUPATH = findSimuPath(sys.argv[1])
    if SIMUPATH == None:
        raise Exception('Simulation name not found')

    # read configuration file of the simulation
    with open(os.path.join(SIMUPATH, "simulation.toml"), 'r') as simulation_file:
        simulation = toml.loads(simulation_file.read())

        # check if rules file exists and load it
        rules_name = simulation['simulation']['name']
        try:
            rules_name = findFileInPath(rules_name, 'toml', [SIMUPATH, GAMESPATH])
        except:
            raise

        with open(rules_name) as rules_file:
            rules = toml.loads(rules_file.read())
            # load objects that could be involved in collisions
            obj = rules['simulation'].get('score', [])

            # variables for time management and stopping mode
            totalTime = rules['simulation']['time']['totalTime']
            simulationStopMode = rules['simulation']['time']['simulationStopMode']
            scoreUntilZeroPoints = False
            scoreUntilNoTime = False
            try:
                stopMode = checkStopMode(simulationStopMode, scoreUntilZeroPoints, scoreUntilNoTime)
                scoreUntilZeroPoints = stopMode[0]
                scoreUntilNoTime = stopMode[1]
            except:
                raise

            if len(sys.argv) == 4:
                totalTime = strToInt(sys.argv[2])
                simulationStopMode = sys.argv[3]
                try:
                    stopMode = checkStopMode(simulationStopMode, scoreUntilZeroPoints, scoreUntilNoTime)
                    scoreUntilZeroPoints = stopMode[0]
                    scoreUntilNoTime = stopMode[1]
                except:
                    raise

            # variables to calculate scoring
            init = rules['simulation'].get('initScore', {})
            k = init.get('k', 0)
            initialScore = init.get('initialScore', 0)
            stopFlag = init.get('stopFlag', False)

            # connect to Morse
            with pymorse.Morse() as simu:
                robots = {}
                for x in simu.robots:
                    robots[x] = {}
                    robots[x]['score'] = maxScore
                    robots[x]['collision'] = 0
                    robots[x]['stop'] = False

                # connect to collision.py
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socketCollision:
                    socketCollision.connect((HOST_COLLISION, PORT_COLLISION))

                    # open a connection for viz.py
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socketController:
                        socketController.bind((HOST_CONTROLLER, PORT_CONTROLLER))
                        socketController.listen(1)
                        conn, addr = socketController.accept()

                        # connect to server.py
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socketServer:
                            socketServer.connect((HOST_SERVER, PORT_SERVER))
                            send('CONTROLLER', socketServer)

                            start = ''
                            while 'Start' not in start:
                                start = receive(socketServer)
                                print(start)

                            startTime = time.time()
                            maxScore = 100
                            timeLeft = 1
