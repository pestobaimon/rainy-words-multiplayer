class Player:
    def __init__(self, name, player_id, game_id):
        self.name = name
        self.score = 0
        self.word_submit = ''
        self.status = 0
        self.id = player_id
        self.game_id = game_id
        self.action_index = 0
        self.ready = False
        self.play_again = False
        self.debuff = 0
        self.ability = 0
        self.connected = True