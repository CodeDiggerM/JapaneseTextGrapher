

class Word(object):
    def __init__(self,
                 word,
                 hinsi,
                 bunrui
                 ):
        self.word = word
        self.hinsi = hinsi
        self.bunrui = bunrui

    def __eq__(self, obj):
        return isinstance(obj, Word) and obj.word == self.word