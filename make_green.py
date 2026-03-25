import pygame
pygame.init()
pygame.display.set_mode((1,1))

bleu = pygame.image.load("assets/spritepersobleu.png").convert_alpha()
vert = bleu.copy()
# Teinte VERT correcte
vert.fill((0, 255, 0), special_flags=pygame.BLEND_MULT)
pygame.image.save(vert, "assets/spritepersovert.png")
pygame.quit()
print("✅ spritepersovert.png créé !")
