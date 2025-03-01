import pygame as pg

pg.init()


class BasicMarker:

    def __init__(self, rect,
                 colour=pg.Color('blue'),
                 text='default',
                 font=pg.font.SysFont("Arial", 16),
                 font_colour=pg.Color('white')):
        self.rect = pg.Rect(rect)
        self.image = pg.Surface(self.rect.size).convert()
        self.colour = colour
        self.font = font
        self.font_colour = font_colour
        self.text = self.font.render(text, True, self.font_colour)
        self.text_rect = self.text.get_rect(center=self.rect.center)

    def draw(self, surf):
        self.image.fill(self.colour)
        surf.blit(self.image, self.rect)
        surf.blit(self.text, self.text_rect)

    def move_ip(self, rel_movement):
        self.rect.move_ip(rel_movement)
        self.text_rect = self.text.get_rect(center=self.rect.center)