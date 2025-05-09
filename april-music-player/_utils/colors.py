RESET = '\033[0m'
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
ORANGE = '\033[33m'
BLUE = '\033[34m'
PURPLE = '\033[35m'
CYAN = '\033[36m'
LIGHTGRAY = '\033[37m'
DARKGRAY = '\033[90m'
LIGHTRED = '\033[91m'
LIGHTGREEN = '\033[92m'
YELLOW = '\033[93m'
LIGHTBLUE = '\033[94m'
PINK = '\033[95m'
LIGHTCYAN = '\033[96m'

def printOrange(text):
    print(f"{ORANGE}{text}{RESET}")

def printGreen(text):
    print(f"{GREEN}{text}{RESET}")

def printRed(text):
    print(f"{RED}{text}{RESET}")

def printCyan(text):
    print(f"{CYAN}{text}{RESET}")

def printYellow(text):
    print(f"{YELLOW}{text}{RESET}")
