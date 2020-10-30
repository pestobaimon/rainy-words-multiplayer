class Timer:

    time = 0
    start = False

    def __init__(self):
        pass

    def start(self):
        self.start = True

    def tick(self):
        self.time += 1

    def reset(self):
        self.time = 0
