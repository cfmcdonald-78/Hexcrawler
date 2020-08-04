'''
Created on Jul 5, 2012

@author: Chris
'''
import pygame.font as font
import pygame


# Simple functions to easily render pre-wrapped text onto a single
# surface with a uniform background.
# Author: George Paci

# Results with various background color alphas:
#  no background given: ultimate blit will just change figure part of text,
#      not ground i.e. it will be interpreted as a transparent background
#  background alpha = 0: "
#  background alpha = 128, entire bounding rectangle will be equally blended
#      with background color, both within and outside text
#  background alpha = 255: entire bounding rectangle will be background color
#
# (At this point, we're not trying to respect foreground color alpha;
# we could by compositing the lines first onto a transparent surface, then
# blitting to the returned surface.)

#vsm_font = font.Font("freesansbold.ttf", 8)
#sm_font =font.Font("freesansbold.ttf", 10) 
#lg_font = font.Font("freesansbold.ttf", 12)
#vlg_font = font.Font("freesansbold.ttf", 16)

vsm_font = None
sm_font = None
lg_font = None
vlg_font = None
        

def renderLines(lines, font, antialias, color, background=None):
    fontHeight = font.get_linesize()

    surfaces = [font.render(ln, antialias, color) for ln in lines]
    # can't pass background to font.render, because it doesn't respect the alpha

    maxwidth = max([s.get_width() for s in surfaces])
    result = pygame.Surface((maxwidth, len(lines)*fontHeight), pygame.SRCALPHA)
    if background == None:
        result.fill((90,90,90,0))
    else:
        result.fill(background)

    for i in range(len(lines)):
        result.blit(surfaces[i], (0,i*fontHeight))
    return result

def block_size(text, font):
    brokenText = text.replace("\r\n","\n").replace("\r","\n").split("\n")
    height = len(brokenText) * font.get_linesize()
    width = 0
    for line in brokenText:
        line_width, line_height = font.size(line)
        width = max(width, line_width)
    
    return width, height

def renderTextBlock(text, font, antialias, color, background=None):
    "This is renderTextBlock"
    brokenText = text.replace("\r\n","\n").replace("\r","\n")
    return renderLines(brokenText.split("\n"), font, antialias, color, background)

LIGHT= (220, 220, 200) 
DARK = (20, 20, 20)
RED = (200, 20, 20)

class TextDrawer(object):
    '''
    classdocs
    '''

    def __init__(self, font_file):
        global vsm_font, sm_font, lg_font, vlg_font
        '''
        Constructor
        '''
        vsm_font = font.Font(font_file, 8)
        sm_font =font.Font(font_file, 10) 
        lg_font = font.Font(font_file, 12)
        vlg_font = font.Font(font_file, 16)
        
        
    def draw_text_block(self,  text_block, font, x, y, surface, color=DARK):
        
        rendered_text = renderTextBlock(text_block, font, True, color)
        surface.blit(rendered_text, (x, y))
        
    def draw_text(self, text, font, x, y, surface, color=DARK, centered=True):
        rendered_text = font.render(text, True, color)
        textRect = rendered_text.get_rect()
        
        if centered:
            textRect.centerx = x
            textRect.centery = y
        else:
            textRect.x = x
            textRect.y = y
        rendered_text = surface.blit(rendered_text, textRect)