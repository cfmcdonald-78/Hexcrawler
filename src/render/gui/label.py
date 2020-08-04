import component
import render.text as text

class Label(component.Component):
    
    def __init__(self, position_rect, label, font=None, image_label=False, tool_tip_text = None):
        super(Label, self).__init__(position_rect, tool_tip_text = tool_tip_text)
        self.image_label = image_label
        self.label = label
        self.font = font
        self.text_color = text.DARK
    
    def set_label(self, label, text_color=text.DARK, tool_tip_text = None):
        self.label = label
        self.text_color = text_color
        if tool_tip_text != None:
            self.tool_tip_text = tool_tip_text
    
    def get_label(self):
        return self.label
        
    def render(self, surface, images):
        if self.label == None:
            return
        
        if self.image_label:
            surface.blit(self.label, (self.rect.x, self.rect.y))
        else:
            font = text.sm_font if self.font == None else self.font
            images.text.draw_text(self.label, font, self.rect.x + self.rect.width / 2,
                                  self.rect.y + self.rect.height / 2, surface, color=self.text_color)
        