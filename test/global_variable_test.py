from test import metadatadata
class Test:
    def __init__(self,):
        self.metadatadata = metadatadata
    def add_data(self,):
        names = ['a', 'b', 'c', 'd', 'e']
        for i in [0,1,2,3,4]:
            self.metadatadata[names[i]] = i

