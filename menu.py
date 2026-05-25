import pygame 
import sys
import math
import cv2

pygame.init()
pygame.mixer.init()

click_snd = pygame.mixer.Sound("assets/click.wav")
back_snd = pygame.mixer.Sound("assets/back.wav")
click_snd.set_volume(0.4)
back_snd.set_volume(0.4)

def click():
    click_snd.play()

def back_click():
    back_snd.play()

pygame.display.init()
dw, dh = pygame.display.get_desktop_sizes()[0]
screen = pygame.display.set_mode((dw, dh), pygame.NOFRAME)
W, H = screen.get_size()
windowed = False

pygame.display.set_caption("What's Next ?")
clock = pygame.time.Clock()

class VideoBG:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise FileNotFoundError(f"Impossible d'ouvrir la vidéo: {path}")
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.delay_ms = int(1000 / fps) if fps and fps > 1 else 33
        self.last = 0
        self.frame_surface = None

    def get_frame(self):
        now = pygame.time.get_ticks()
        if now - self.last < self.delay_ms and self.frame_surface is not None:
            return self.frame_surface
        self.last = now
        ok, frame = self.cap.read()
        if not ok:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.cap.read()
            if not ok:
                return self.frame_surface
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        fh, fw = frame.shape[:2]
        scale = max(W / fw, H / fh) * 1.02
        nw, nh = int(fw * scale), int(fh * scale)
        frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        x = (nw - W) // 2
        y = (nh - H) // 2
        frame = frame[y:y + H, x:x + W]
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        self.frame_surface = surf
        return surf

video_play = VideoBG("assets/animate_the_chain_in_first_plan_to_make_it_gigle_seed4235003811.mp4")

bg_main_src = pygame.image.load("assets/fond.png").convert()

def scale_cover_img(img, w, h):
    iw, ih = img.get_size()
    s = max(w / iw, h / ih)
    nw, nh = max(int(iw * s), w), max(int(ih * s), h)
    scaled = pygame.transform.smoothscale(img, (nw, nh))
    x = max(0, min((nw - w) // 2, nw - w))
    y = max(0, min((nh - h) // 2, nh - h))
    return scaled.subsurface((x, y, w, h)).copy()

background = scale_cover_img(bg_main_src, W, H)

UI_FONT = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", int(H * 0.06))
SMALL_FONT = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", int(H * 0.045))
GEAR_FONT = pygame.font.SysFont("Segoe UI Emoji", int(H * 0.07))

WHITE = (240, 240, 240)
GREEN = (140, 255, 140)

brightness = 1.0

gear_size = max(48, int(min(W, H) * 0.06))
gear_margin = max(16, int(min(W, H) * 0.02))
gear_rect = pygame.Rect(W - gear_margin - gear_size, gear_margin, gear_size, gear_size)

def apply_brightness(surface, factor):
    s = surface.copy()
    dark = pygame.Surface(s.get_size())
    dark.fill((0, 0, 0))
    dark.set_alpha(int((1 - factor) * 200))
    s.blit(dark, (0, 0))
    return s

def draw_button_custom(text, rect, mouse_pos, font):
    hovered = rect.collidepoint(mouse_pos)
    scale = 1.06 if hovered else 1.0
    new_w = int(rect.width * scale)
    new_h = int(rect.height * scale)
    draw_rect = pygame.Rect(0, 0, new_w, new_h)
    draw_rect.center = rect.center
    base_color = (100, 220, 100)
    normal_color = (60, 160, 60)
    color = base_color if hovered else normal_color
    if hovered:
        glow_surf = pygame.Surface((draw_rect.width + 20, draw_rect.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (120, 255, 120, 120), glow_surf.get_rect(), border_radius=max(14, draw_rect.height // 4))
        screen.blit(glow_surf, glow_surf.get_rect(center=draw_rect.center))
    pygame.draw.rect(screen, color, draw_rect, border_radius=max(12, draw_rect.height // 4))
    pygame.draw.rect(screen, (0, 0, 0), draw_rect, 3, border_radius=max(12, draw_rect.height // 4))
    label = font.render(text, True, (0, 0, 0))
    lw = label.get_width()
    if lw > draw_rect.width - 20:
        shrink = (draw_rect.width - 20) / lw
        new_size = max(10, int(font.size * shrink)) if hasattr(font, 'size') else max(10, int(H * 0.03))
        small = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", new_size)
        label = small.render(text, True, (0, 0, 0))
    screen.blit(label, label.get_rect(center=draw_rect.center))

def draw_button(text, rect, mouse_pos):
    draw_button_custom(text, rect, mouse_pos, UI_FONT)

def toggle_fullscreen():
    global screen, windowed
    windowed = not windowed
    if windowed:
        screen = pygame.display.set_mode((int(dw * 0.8), int(dh * 0.8)))
    else:
        screen = pygame.display.set_mode((dw, dh), pygame.NOFRAME)

def draw_input_box(rect, text, active, font):
    color = (100, 255, 100) if active else (180, 180, 180)
    pygame.draw.rect(screen, (20, 20, 20), rect, border_radius=12)
    pygame.draw.rect(screen, color, rect, 3, border_radius=12)
    label = font.render(text or "Adresse IP de l'hote", True, WHITE if text else (150, 150, 150))
    screen.blit(label, label.get_rect(midleft=(rect.left + 18, rect.centery)))

def draw_gear():
    pygame.draw.rect(screen, (200, 200, 200), gear_rect, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), gear_rect, 2, border_radius=10)
    gear = GEAR_FONT.render("⚙", True, (0, 0, 0))
    screen.blit(gear, gear.get_rect(center=gear_rect.center))

TITLE_TEXT = "What's Next ?"
TITLE_Y = int(H * 0.22)

title_font = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", int(H * 0.16))
title_base = title_font.render(TITLE_TEXT, True, GREEN).convert_alpha()

pad = 40
glow_base = pygame.Surface((title_base.get_width() + pad * 2, title_base.get_height() + pad * 2), pygame.SRCALPHA)
cx = glow_base.get_width() // 2
cy = glow_base.get_height() // 2
for dx in [-4, -3, -2, -1, 1, 2, 3, 4]:
    for dy in [-4, -3, -2, -1, 1, 2, 3, 4]:
        g = title_font.render(TITLE_TEXT, True, (30, 110, 30)).convert_alpha()
        glow_base.blit(g, g.get_rect(center=(cx + dx, cy + dy)))

def draw_title_pulse(t):
    s = 1.0 + 0.04 * math.sin(t * 1.8)
    alpha = 80 + int(160 * (0.5 + 0.5 * math.sin(t * 2.2)))
    gw = max(1, int(glow_base.get_width() * s))
    gh = max(1, int(glow_base.get_height() * s))
    glow = pygame.transform.smoothscale(glow_base, (gw, gh))
    glow.set_alpha(alpha)
    glow_rect = glow.get_rect(center=(W // 2, TITLE_Y))
    tw = max(1, int(title_base.get_width() * s))
    th = max(1, int(title_base.get_height() * s))
    title = pygame.transform.smoothscale(title_base, (tw, th))
    title_rect = title.get_rect(center=(W // 2, TITLE_Y))
    screen.blit(glow, glow_rect)
    screen.blit(title, title_rect)

def options_menu():
    global brightness
    back_btn = pygame.Rect(W // 2 - int(W * 0.12), H - int(H * 0.14), int(W * 0.24), int(H * 0.09))
    slider_w = int(W * 0.42)
    slider_rect = pygame.Rect(W // 2 - slider_w // 2, int(H * 0.52), slider_w, max(8, int(H * 0.012)))
    knob_x = int(slider_rect.x + brightness * slider_rect.width)
    box = pygame.Rect(W // 2 - int(W * 0.28), int(H * 0.34), int(W * 0.56), int(H * 0.32))
    dragging = False
    title_big = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", int(H * 0.085))

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    back_click()
                    return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.collidepoint(mouse_pos):
                    back_click()
                    return
                if abs(mouse_pos[0] - knob_x) < 18 and abs(mouse_pos[1] - slider_rect.centery) < 18:
                    dragging = True
            if event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            if event.type == pygame.MOUSEMOTION and dragging:
                knob_x = max(slider_rect.left, min(slider_rect.right, mouse_pos[0]))
                brightness = (knob_x - slider_rect.left) / slider_rect.width

        bg = apply_brightness(background, brightness)
        screen.blit(bg, (0, 0))
        title = title_big.render("PARAMETRES", True, GREEN)
        screen.blit(title, title.get_rect(center=(W // 2, int(H * 0.14))))
        tint = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
        tint.fill((80, 80, 80, 140))
        screen.blit(tint, box.topleft)
        pygame.draw.rect(screen, (0, 0, 0), box, 5, border_radius=14)
        txt = SMALL_FONT.render("Luminosité", True, WHITE)
        screen.blit(txt, txt.get_rect(center=(W // 2, box.top + int(box.height * 0.30))))
        pygame.draw.rect(screen, (220, 220, 220), slider_rect)
        pygame.draw.circle(screen, (100, 255, 100), (knob_x, slider_rect.centery), 14)
        draw_button("Retour", back_btn, mouse_pos)
        pygame.display.flip()
        clock.tick(60)

def play_menu():
    play_font = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", int(H * 0.038))
    title_mid = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", int(H * 0.075))
    btn_w = int(W * 0.34)
    btn_h = int(H * 0.11)
    btn_new = pygame.Rect(0, 0, btn_w, btn_h)
    btn_multi = pygame.Rect(0, 0, btn_w, btn_h)
    btn_back = pygame.Rect(0, 0, int(W * 0.25), int(H * 0.09))
    btn_new.center = (W // 2, int(H * 0.44))
    btn_multi.center = (W // 2, int(H * 0.60))
    btn_back.center = (W // 2, int(H * 0.80))

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    back_click()
                    return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_new.collidepoint(mouse_pos):
                    click()
                    return {"mode": "local", "save": "new"}
                if btn_multi.collidepoint(mouse_pos):
                    click()
                    choice = multiplayer_menu()
                    if choice:
                        return choice
                if btn_back.collidepoint(mouse_pos):
                    back_click()
                    return None

        frame = video_play.get_frame()
        if frame is not None:
            bg = apply_brightness(frame, brightness)
            screen.blit(bg, (0, 0))
        else:
            screen.fill((0, 0, 0))

        title = title_mid.render("JOUER", True, GREEN)
        screen.blit(title, title.get_rect(center=(W // 2, int(H * 0.24))))
        draw_button_custom("Nouvelle partie", btn_new, mouse_pos, play_font)
        draw_button_custom("Multijoueur en ligne", btn_multi, mouse_pos, play_font)
        draw_button_custom("Retour", btn_back, mouse_pos, play_font)
        pygame.display.flip()
        clock.tick(60)

def multiplayer_menu():
    play_font = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", int(H * 0.04))
    title_mid = pygame.font.Font("assets/CinzelDecorative-Bold.ttf", int(H * 0.065))
    btn_w = int(W * 0.36)
    btn_h = int(H * 0.095)
    btn_host = pygame.Rect(0, 0, btn_w, btn_h)
    btn_join = pygame.Rect(0, 0, btn_w, btn_h)
    btn_back = pygame.Rect(0, 0, int(W * 0.25), int(H * 0.09))
    input_rect = pygame.Rect(0, 0, int(W * 0.36), int(H * 0.08))
    btn_host.center = (W // 2, int(H * 0.40))
    input_rect.center = (W // 2, int(H * 0.55))
    btn_join.center = (W // 2, int(H * 0.67))
    btn_back.center = (W // 2, int(H * 0.88))
    ip_text = "127.0.0.1"
    input_active = False

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    back_click()
                    return None
                if input_active:
                    if event.key == pygame.K_BACKSPACE:
                        ip_text = ip_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        click()
                        return {"mode": "join", "host": ip_text.strip() or "127.0.0.1"}
                    elif event.unicode and len(ip_text) < 32:
                        if event.unicode.isalnum() or event.unicode in ".:-":
                            ip_text += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                input_active = input_rect.collidepoint(mouse_pos)
                if btn_host.collidepoint(mouse_pos):
                    click()
                    import socket as _socket
                    def _get_local_ip():
                        try:
                            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
                            s.connect(("8.8.8.8", 80))
                            ip = s.getsockname()[0]
                            s.close()
                            return ip
                        except Exception:
                            return "127.0.0.1"
                    return {"mode": "host", "host": _get_local_ip()}
                if btn_join.collidepoint(mouse_pos):
                    click()
                    return {"mode": "join", "host": ip_text.strip() or "127.0.0.1"}
                if btn_back.collidepoint(mouse_pos):
                    back_click()
                    return None

        frame = video_play.get_frame()
        if frame is not None:
            bg = apply_brightness(frame, brightness)
            screen.blit(bg, (0, 0))
        else:
            screen.fill((0, 0, 0))

        title = title_mid.render("MULTIJOUEUR", True, GREEN)
        screen.blit(title, title.get_rect(center=(W // 2, int(H * 0.20))))
        draw_button_custom("Creer une partie", btn_host, mouse_pos, play_font)
        draw_input_box(input_rect, ip_text, input_active, play_font)
        draw_button_custom("Rejoindre une partie", btn_join, mouse_pos, play_font)
        draw_button_custom("Retour", btn_back, mouse_pos, play_font)
        pygame.display.flip()
        clock.tick(60)

def main_menu():
    btn_w = int(W * 0.25)
    btn_h = int(H * 0.09)
    btn_play = pygame.Rect(0, 0, btn_w, btn_h)
    btn_quit = pygame.Rect(0, 0, btn_w, btn_h)
    btn_play.center = (W // 2, int(H * 0.58))
    btn_quit.center = (W // 2, int(H * 0.72))

    while True:
        t = pygame.time.get_ticks() / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_play.collidepoint(mouse_pos):
                    click()
                    choice = play_menu()
                    if choice:
                        return choice
                if btn_quit.collidepoint(mouse_pos):
                    click()
                    pygame.quit(); sys.exit()
                if gear_rect.collidepoint(mouse_pos):
                    click()
                    options_menu()

        bg = apply_brightness(background, brightness)
        screen.blit(bg, (0, 0))
        draw_title_pulse(t)
        draw_button("Play", btn_play, mouse_pos)
        draw_button("Quit", btn_quit, mouse_pos)
        draw_gear()
        pygame.display.flip()
        clock.tick(60)