class Player:

    def __init__(self, name, id_in):
        self.name = name
        self.score = 0
        self.keystrokes = ''
        self.confirm_key = False
        self.id = id_in
        self.connected = False
        self.play_again = False
