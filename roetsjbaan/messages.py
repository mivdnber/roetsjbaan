class Message(object):
    pass

class Migrating(Message):
    def __init__(self, old, new, direction):
        self.old = old
        self.new = new
        self.direction = direction
