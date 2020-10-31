class Player:

    def __init__(self, name):
        self.name = name
        self.score = 0
        self.keystrokes = ''
        self.confirm_key = False
        self.id = 0
        self.connected = False
        self.ready = False

    def __init__(self, name, id):
        self.name = name
        self.score = 0
        self.keystrokes = ''
        self.confirm_key = False
        self.id = id
        self.connected = False
        self.ready = False