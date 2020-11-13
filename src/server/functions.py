def get_opponent(self_id):
    if self_id == 1:
        return 0
    elif self_id == 0:
        return 1
    else:
        return 'error'