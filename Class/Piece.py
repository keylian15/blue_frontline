import pygame

class Piece:
    def __init__(self):
        self.count = 0
        
    
    def add_one(self):
        self.count += 1
        
    def minus_one(self):
        if self.count <= 0:
            return
        else:
            self.count -= 1
    