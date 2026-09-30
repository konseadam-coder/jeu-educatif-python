import pygame
import os
import sys
import random
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Union


# Initialisation
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Jeu Educatif")

clock = pygame.time.Clock()
FPS = 60

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_LIGHT = (245, 247, 250)
ORANGE = (255, 140, 0)
YELLOW = (255, 215, 0)
YELLOW_BG = (255, 243, 176)
YELLOW_TEXT = (161, 98, 7)

# Palette par matiere (inspiree du modele React fourni)
INDIGO = (79, 70, 229)
INDIGO_LIGHT = (224, 222, 250)
PINK = (219, 39, 119)
PINK_LIGHT = (252, 216, 233)
EMERALD = (5, 150, 105)
EMERALD_LIGHT = (209, 240, 226)
SLATE = (30, 41, 59)
SLATE_SOFT = (100, 116, 139)

# Tranches d'age (reprend les 3 groupes du modele : 1-3 / 4-6 / 7-10)
BLUE_TIER = (59, 130, 246)
BLUE_TIER_LIGHT = (219, 234, 254)
GREEN_TIER = (34, 197, 94)
GREEN_TIER_LIGHT = (220, 252, 231)
PURPLE_TIER = (147, 51, 234)
PURPLE_TIER_LIGHT = (237, 220, 253)

GREEN = (16, 185, 129)
RED = (220, 38, 38)
GREEN_BANNER_BG = (209, 250, 229)
RED_BANNER_BG = (254, 226, 226)

CONFETTI_COLORS = [
    (16, 185, 129), (52, 211, 153), (250, 204, 21),
    (244, 114, 182), (96, 165, 250), (167, 139, 250),
]

# Polices
font_huge = pygame.font.SysFont("Comic Sans MS", 65)
font_big = pygame.font.SysFont("Comic Sans MS", 50)
font_medium = pygame.font.SysFont("Arial", 30)
font = pygame.font.SysFont("Arial", 26)
font_small = pygame.font.SysFont("Arial", 20)
font_tiny = pygame.font.SysFont("Arial", 15)

# Sons (chiffres et lettres, joues comme renforcement pedagogique)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "Chiffreslettres2")


def charger_sons(cles, motif_nom_fichier):
    sounds = {}
    if not os.path.isdir(SOUNDS_DIR):
        return sounds
    for cle in cles:
        chemin = os.path.join(SOUNDS_DIR, motif_nom_fichier(cle))
        if os.path.exists(chemin):
            try:
                sounds[str(cle)] = pygame.mixer.Sound(chemin)
            except pygame.error:
                pass
    return sounds


def charger_sons_chiffres():
    return charger_sons(range(1, 16), lambda i: f"Chiffre({i}).mp3")


def charger_sons_lettres():
    return charger_sons("ABCDEFGHIJKLMNOPQRSTUVWXYZ", lambda lettre: f"{lettre}.mp3")


def jouer_son_si_disponible(sounds, cle):
    if not cle:
        return
    son = sounds.get(str(cle))
    if son is not None:
        son.play()


# Outils d'interface communs
def draw_back_button():
    back_rect = pygame.Rect(10, 10, 110, 45)
    pygame.draw.rect(screen, ORANGE, back_rect, border_radius=12)
    label = font_small.render("Retour", True, WHITE)
    screen.blit(label, label.get_rect(center=back_rect.center))
    return back_rect


def back_button_clicked(event, back_rect):
    return event.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(event.pos)


def draw_score_badge(score):
    label = font.render(f"Score : {score}", True, YELLOW_TEXT)
    badge_rect = pygame.Rect(0, 0, label.get_width() + 40, 44)
    badge_rect.topright = (WIDTH - 20, 18)
    pygame.draw.rect(screen, YELLOW_BG, badge_rect, border_radius=22)
    pygame.draw.rect(screen, YELLOW, badge_rect, width=2, border_radius=22)
    screen.blit(label, label.get_rect(center=badge_rect.center))


def draw_rounded_panel(rect, color, border_color=None, border_width=0, radius=24):
    pygame.draw.rect(screen, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(screen, border_color, rect, width=border_width, border_radius=radius)


def fit_text(text, max_width, *font_tiers):
    """Essaie chaque police (du plus grand au plus petit) et renvoie la
    premiere qui tient dans max_width ; a defaut, renvoie la plus petite
    (les options d'Histoire peuvent etre des phrases plus longues)."""
    surf = None
    for font_obj in font_tiers:
        surf = font_obj.render(text, True, BLACK)
        if surf.get_width() <= max_width:
            return surf
    return surf


def wrap_text_lines(text, max_width, font_obj):
    """Decoupe un texte en plusieurs lignes pour qu'il tienne dans max_width."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if font_obj.size(test)[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_question_text(text, rect):
    """Affiche le texte d'une question en choisissant une taille de police
    adaptee a sa longueur, avec retour a la ligne pour les phrases longues
    (ex: questions d'Histoire) afin d'eviter tout debordement visuel."""
    max_width = rect.width - 40
    if len(text) <= 4:
        chosen_font = font_huge
    elif len(text) <= 14:
        chosen_font = font_big
    else:
        chosen_font = font_medium

    lines = wrap_text_lines(text, max_width, chosen_font)
    line_surfaces = [chosen_font.render(line, True, BLACK) for line in lines]
    total_height = sum(s.get_height() for s in line_surfaces) + (len(line_surfaces) - 1) * 4
    y = rect.centery - total_height // 2
    for surf in line_surfaces:
        screen.blit(surf, (rect.centerx - surf.get_width() // 2, y))
        y += surf.get_height() + 4



# Icones dessinees en vectoriel (pas d'emoji : rendu fiable partout)
def _new_icon_surface(size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    return surf


def icon_dog(size):
    s = _new_icon_surface(size)
    c = size // 2
    pygame.draw.circle(s, (181, 136, 99), (c, c), size * 0.38)
    pygame.draw.polygon(s, (140, 100, 70), [(c - size*0.3, c - size*0.25), (c - size*0.42, c - size*0.02), (c - size*0.12, c - size*0.12)])
    pygame.draw.polygon(s, (140, 100, 70), [(c + size*0.3, c - size*0.25), (c + size*0.42, c - size*0.02), (c + size*0.12, c - size*0.12)])
    pygame.draw.circle(s, BLACK, (int(c - size*0.12), int(c - size*0.05)), max(2, int(size*0.04)))
    pygame.draw.circle(s, BLACK, (int(c + size*0.12), int(c - size*0.05)), max(2, int(size*0.04)))
    pygame.draw.circle(s, (60, 40, 30), (c, int(c + size*0.12)), max(3, int(size*0.05)))
    return s


def icon_cat(size):
    s = _new_icon_surface(size)
    c = size // 2
    pygame.draw.circle(s, (240, 200, 150), (c, c), size * 0.36)
    pygame.draw.polygon(s, (240, 200, 150), [(c - size*0.28, c - size*0.22), (c - size*0.4, c - size*0.42), (c - size*0.1, c - size*0.28)])
    pygame.draw.polygon(s, (240, 200, 150), [(c + size*0.28, c - size*0.22), (c + size*0.4, c - size*0.42), (c + size*0.1, c - size*0.28)])
    pygame.draw.circle(s, BLACK, (int(c - size*0.11), int(c - size*0.02)), max(2, int(size*0.035)))
    pygame.draw.circle(s, BLACK, (int(c + size*0.11), int(c - size*0.02)), max(2, int(size*0.035)))
    for dx in (-1, 1):
        for dy in (-0.05, 0.05, 0.15):
            pygame.draw.line(s, (120, 90, 70),
                              (c + dx*size*0.08, c + size*dy),
                              (c + dx*size*0.32, c + size*(dy - 0.03)), 2)
    return s


def icon_apple(size):
    s = _new_icon_surface(size)
    c = size // 2
    pygame.draw.circle(s, (220, 40, 40), (c - int(size*0.1), c + int(size*0.05)), size*0.28)
    pygame.draw.circle(s, (220, 40, 40), (c + int(size*0.1), c + int(size*0.05)), size*0.28)
    pygame.draw.line(s, (100, 65, 30), (c, c - size*0.22), (c, c - size*0.35), 3)
    pygame.draw.polygon(s, (60, 160, 70), [(c, c - size*0.28), (c + size*0.2, c - size*0.35), (c + size*0.08, c - size*0.15)])
    return s


def icon_sun(size):
    s = _new_icon_surface(size)
    c = size // 2
    r = size * 0.22
    for i in range(8):
        angle = i * math.pi / 4
        x1, y1 = c + math.cos(angle) * r * 1.3, c + math.sin(angle) * r * 1.3
        x2, y2 = c + math.cos(angle) * r * 1.9, c + math.sin(angle) * r * 1.9
        pygame.draw.line(s, (250, 180, 40), (x1, y1), (x2, y2), 4)
    pygame.draw.circle(s, (255, 205, 60), (c, c), r)
    return s


def icon_star(size):
    s = _new_icon_surface(size)
    c = size // 2
    points = []
    for i in range(10):
        angle = -math.pi/2 + i * math.pi / 5
        r = size*0.42 if i % 2 == 0 else size*0.18
        points.append((c + math.cos(angle)*r, c + math.sin(angle)*r))
    pygame.draw.polygon(s, (250, 204, 21), points)
    return s


def icon_balloon(size):
    s = _new_icon_surface(size)
    c = size // 2
    pygame.draw.circle(s, (236, 72, 153), (c, c - int(size*0.08)), size*0.3)
    pygame.draw.polygon(s, (236, 72, 153), [(c - size*0.06, c + size*0.18), (c + size*0.06, c + size*0.18), (c, c + size*0.28)])
    pygame.draw.line(s, (100, 100, 100), (c, c + size*0.28), (c, c + size*0.45), 2)
    return s


def icon_fish(size):
    s = _new_icon_surface(size)
    c = size // 2
    pygame.draw.ellipse(s, (96, 165, 250), (c - size*0.3, c - size*0.18, size*0.5, size*0.36))
    pygame.draw.polygon(s, (96, 165, 250), [(c + size*0.18, c), (c + size*0.35, c - size*0.15), (c + size*0.35, c + size*0.15)])
    pygame.draw.circle(s, BLACK, (int(c - size*0.18), c), max(2, int(size*0.03)))
    return s


def icon_butterfly(size):
    s = _new_icon_surface(size)
    c = size // 2
    pygame.draw.ellipse(s, (167, 139, 250), (c - size*0.4, c - size*0.32, size*0.35, size*0.28))
    pygame.draw.ellipse(s, (167, 139, 250), (c + size*0.05, c - size*0.32, size*0.35, size*0.28))
    pygame.draw.ellipse(s, (196, 181, 253), (c - size*0.35, c + size*0.02, size*0.28, size*0.24))
    pygame.draw.ellipse(s, (196, 181, 253), (c + size*0.07, c + size*0.02, size*0.28, size*0.24))
    pygame.draw.line(s, (60, 60, 60), (c, c - size*0.3), (c, c + size*0.3), 3)
    return s


def icon_car(size):
    s = _new_icon_surface(size)
    c = size // 2
    body = pygame.Rect(c - size*0.38, c - size*0.05, size*0.76, size*0.22)
    pygame.draw.rect(s, (239, 68, 68), body, border_radius=int(size*0.06))
    roof = pygame.Rect(c - size*0.2, c - size*0.2, size*0.4, size*0.18)
    pygame.draw.rect(s, (239, 68, 68), roof, border_radius=int(size*0.05))
    pygame.draw.circle(s, (30, 30, 30), (int(c - size*0.22), int(c + size*0.2)), size*0.09)
    pygame.draw.circle(s, (30, 30, 30), (int(c + size*0.22), int(c + size*0.2)), size*0.09)
    return s


def icon_tree(size):
    s = _new_icon_surface(size)
    c = size // 2
    pygame.draw.rect(s, (120, 80, 45), (c - size*0.05, c + size*0.05, size*0.1, size*0.3))
    pygame.draw.circle(s, (46, 160, 67), (c, c - size*0.05), size*0.32)
    return s


def icon_heart(size):
    s = _new_icon_surface(size)
    c = size // 2
    r = size * 0.2
    pygame.draw.circle(s, (239, 68, 68), (c - int(r*0.9), c - int(r*0.4)), r)
    pygame.draw.circle(s, (239, 68, 68), (c + int(r*0.9), c - int(r*0.4)), r)
    pygame.draw.polygon(s, (239, 68, 68), [
        (c - r*1.8, c - r*0.2), (c + r*1.8, c - r*0.2), (c, c + r*1.8)
    ])
    return s


def icon_moon(size):
    s = _new_icon_surface(size)
    c = size // 2
    pygame.draw.circle(s, (250, 204, 21), (c, c), size*0.32)
    mask = _new_icon_surface(size)
    pygame.draw.circle(mask, (255, 255, 255, 255), (int(c + size*0.16), c), int(size*0.28))
    s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    return s


ICON_DRAWERS = {
    "chien": icon_dog, "chat": icon_cat, "pomme": icon_apple, "soleil": icon_sun,
    "etoile": icon_star, "ballon": icon_balloon, "poisson": icon_fish,
    "papillon": icon_butterfly, "voiture": icon_car, "arbre": icon_tree,
    "coeur": icon_heart, "lune": icon_moon,
}
_icon_cache = {}


def get_icon(key, size):
    cache_key = (key, size)
    if cache_key not in _icon_cache:
        drawer = ICON_DRAWERS.get(key, icon_star)
        _icon_cache[cache_key] = drawer(size)
    return _icon_cache[cache_key]

# Effet confettis (equivalent de canvas-confetti a la reussite)
class ConfettiParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-9, -4)
        self.gravity = 0.35
        self.size = random.randint(5, 9)
        self.color = random.choice(CONFETTI_COLORS)
        self.life = random.randint(40, 70)
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-8, 8)

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.angle += self.spin
        self.life -= 1

    def draw(self, surface):
        if self.life <= 0:
            return
        rect = pygame.Rect(0, 0, self.size, self.size)
        piece = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        piece.fill(self.color)
        rotated = pygame.transform.rotate(piece, self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        surface.blit(rotated, rect)


class ConfettiEffect:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, count=70):
        self.particles = [ConfettiParticle(x, y) for _ in range(count)]

    def active(self):
        return len(self.particles) > 0

    def update_and_draw(self, surface):
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
            else:
                p.draw(surface)

@dataclass
class Question:
    text: str
    answer: Union[int, str]
    options: List[Union[int, str]]
    visual_count: Optional[int] = None      # nombre de ronds a afficher (comptage)
    text_is_icon: bool = False              # le champ "text" est une cle d'icone
    icon_options: bool = False              # les options sont des cles d'icones
    audio_key: Optional[str] = None         # son a jouer en cas de bonne reponse


class GameEngine(ABC):
    """Classe abstraite commune a tous les jeux : gere l'age et le score."""

    SUCCESS_MESSAGES = ["Bravo !"]
    FAILURE_MESSAGE = "Essaie encore !"

    def __init__(self, age):
        self.age = age
        self.score = 0

    def increment_score(self):
        self.score += 1

    def get_score(self):
        return self.score

    def success_message(self):
        return random.choice(self.SUCCESS_MESSAGES)

    @staticmethod
    def check_answer(selected, correct):
        return selected == correct

    @abstractmethod
    def generate_question(self) -> Question:
        raise NotImplementedError


class MathGameEngine(GameEngine):
    SUCCESS_MESSAGES = ["Bravo !", "Bien joue !", "Parfait !"]

    def __init__(self, age, sounds=None):
        super().__init__(age)
        self.sounds = sounds or {}

    def generate_question(self) -> Question:
        if self.age <= 3:
            answer = random.randint(1, 3)
            options = {answer}
            while len(options) < 3:
                options.add(random.randint(1, 3))
            options = list(options)
            random.shuffle(options)
            return Question(text="Combien de ronds ?", answer=answer, options=options,
                             visual_count=answer, audio_key=str(answer))
        elif self.age <= 6:
            n1, n2 = random.randint(1, 5), random.randint(1, 5)
            answer = n1 + n2
            options = {answer}
            while len(options) < 3:
                r = random.randint(1, 10)
                if r != answer:
                    options.add(r)
            options = list(options)
            random.shuffle(options)
            return Question(text=f"{n1} + {n2} = ?", answer=answer, options=options)
        else:
            r = random.random()
            if r < 0.4:
                n1, n2 = random.randint(1, 10), random.randint(1, 10)
                answer, text = n1 + n2, f"{n1} + {n2} = ?"
            elif r < 0.7:
                n1, n2 = random.randint(5, 14), random.randint(1, 5)
                answer, text = n1 - n2, f"{n1} - {n2} = ?"
            else:
                n1, n2 = random.randint(1, 5), random.randint(1, 5)
                answer, text = n1 * n2, f"{n1} x {n2} = ?"
            options = {answer}
            while len(options) < 4:
                r2 = random.randint(0, 49)
                if r2 != answer:
                    options.add(r2)
            options = list(options)
            random.shuffle(options)
            return Question(text=text, answer=answer, options=options)


class AlphabetGameEngine(GameEngine):
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    SUCCESS_MESSAGES = ["Excellent !", "Super !", "Genial !"]

    def __init__(self, age, sounds=None):
        super().__init__(age)
        self.sounds = sounds or {}

    def generate_question(self) -> Question:
        if self.age <= 3:
            letter = random.choice(self.ALPHABET)
            options = {letter}
            while len(options) < 3:
                options.add(random.choice(self.ALPHABET))
            options = list(options)
            random.shuffle(options)
            return Question(text=letter, answer=letter, options=options, audio_key=letter)
        elif self.age <= 6:
            letter = random.choice(self.ALPHABET)
            target = letter.lower()
            options = {target}
            while len(options) < 3:
                r = random.choice(self.ALPHABET).lower()
                if r != target:
                    options.add(r)
            options = list(options)
            random.shuffle(options)
            return Question(text=letter, answer=target, options=options, audio_key=letter)
        else:
            idx = random.randint(0, 24)
            letter = self.ALPHABET[idx]
            target = self.ALPHABET[idx + 1]
            options = {target}
            while len(options) < 4:
                r = random.choice(self.ALPHABET)
                if r != target:
                    options.add(r)
            options = list(options)
            random.shuffle(options)
            return Question(text=f"{letter}  ->  ?", answer=target, options=options, audio_key=target)


class ImageGameEngine(GameEngine):
    SUCCESS_MESSAGES = ["Super !", "Bravo !", "Trouve !"]
    ITEMS = [
        ("Chien", "chien"), ("Chat", "chat"), ("Pomme", "pomme"), ("Soleil", "soleil"),
        ("Etoile", "etoile"), ("Ballon", "ballon"), ("Poisson", "poisson"),
        ("Papillon", "papillon"), ("Voiture", "voiture"), ("Arbre", "arbre"),
        ("Coeur", "coeur"), ("Lune", "lune"),
    ]

    def generate_question(self) -> Question:
        name, icon = random.choice(self.ITEMS)
        if self.age <= 3:
            options = {icon}
            while len(options) < 3:
                options.add(random.choice(self.ITEMS)[1])
            options = list(options)
            random.shuffle(options)
            return Question(text=icon, answer=icon, options=options,
                             text_is_icon=True, icon_options=True)
        elif self.age <= 6:
            options = {icon}
            while len(options) < 4:
                options.add(random.choice(self.ITEMS)[1])
            options = list(options)
            random.shuffle(options)
            return Question(text=name, answer=icon, options=options, icon_options=True)
        else:
            options = {name}
            while len(options) < 4:
                options.add(random.choice(self.ITEMS)[0])
            options = list(options)
            random.shuffle(options)
            return Question(text=icon, answer=name, options=options,
                             text_is_icon=True, icon_options=False)


QUESTIONS_HISTOIRE = [
    {"question": "Quelle est la capitale du Mali ?", "options": ["Kayes", "Segou", "Mopti", "Bamako"], "correct": 3},
    {"question": "Qui etait Soundiata Keita ?", "options": ["Un roi", "Un marchand", "Un musicien", "Un chasseur"], "correct": 0},
    {"question": "Quel fleuve traverse Bamako ?", "options": ["Senegal", "Niger", "Nil", "Congo"], "correct": 1},
    {"question": "Quelle est la capitale de la France ?", "options": ["Nice", "Lyon", "Marseille", "Paris"], "correct": 3},
    {"question": "Dans quel continent se trouve le Mali ?", "options": ["Europe", "Afrique", "Asie", "Amerique"], "correct": 1},
    {"question": "Quel empire a ete fonde par Soundiata Keita ?", "options": ["L'empire du Ghana", "L'empire du Mali", "L'empire Songhay", "L'empire Wolof"], "correct": 1},
    {"question": "Quelle est la ville des 333 saints au Mali ?", "options": ["Gao", "Mopti", "Tombouctou", "Sikasso"], "correct": 2},
    {"question": "Quelle est la couleur principale du monument de l'Independance ?", "options": ["Blanc", "Rouge", "Bleu", "Vert"], "correct": 0},
    {"question": "Qui est connu comme l'empereur le plus riche de l'histoire ?", "options": ["Kankou Moussa", "Sony Ali Ber", "Askia Mohamed", "Samory Toure"], "correct": 0},
    {"question": "Quelle langue nationale est la plus parlee au Mali ?", "options": ["Le francais", "Le bambara", "L'anglais", "Le fulfulde"], "correct": 1},
]


class HistoireGameEngine(GameEngine):
    SUCCESS_MESSAGES = ["Bravo !", "Tu connais bien !", "Exact !"]

    def __init__(self, age):
        super().__init__(age)
        self.deck = random.sample(QUESTIONS_HISTOIRE, len(QUESTIONS_HISTOIRE))
        self.idx = 0

    def generate_question(self) -> Question:
        if self.idx >= len(self.deck):
            self.idx = 0
            random.shuffle(self.deck)
        q = self.deck[self.idx]
        self.idx += 1
        answer = q["options"][q["correct"]]
        return Question(text=q["question"], answer=answer, options=list(q["options"]))


def run_quiz_screen(engine, title, theme_color, theme_light):
    confetti = ConfettiEffect()
    question = engine.generate_question()
    message = ""
    is_correct = None
    waiting_next = False
    next_time = 0

    while True:
        screen.fill(BG_LIGHT)
        back_rect = draw_back_button()

        # En-tete : titre de la matiere + score
        title_surf = font_big.render(title, True, SLATE)
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 20))
        draw_score_badge(engine.get_score())

        # Zone de question
        prompt_rect = pygame.Rect(WIDTH // 2 - 280, 100, 560, 150)
        draw_rounded_panel(prompt_rect, WHITE, theme_color, 3)

        if question.visual_count is not None:
            gap = 70
            start_x = WIDTH // 2 - (gap * (question.visual_count - 1)) // 2
            for i in range(question.visual_count):
                pygame.draw.circle(screen, theme_color, (start_x + i * gap, prompt_rect.centery), 22)
        elif question.text_is_icon:
            icon = get_icon(question.text, 110)
            screen.blit(icon, icon.get_rect(center=prompt_rect.center))
        else:
            draw_question_text(question.text, prompt_rect)

        # Options de reponse (grille 2 colonnes)
        cols = 2
        cell_w, cell_h, gap_cell = 280, 100, 20
        start_x = WIDTH // 2 - (cell_w * cols + gap_cell) // 2
        start_y = 290
        option_rects = []
        for i, option in enumerate(question.options):
            col, row = i % cols, i // cols
            rect = pygame.Rect(start_x + col * (cell_w + gap_cell), start_y + row * (cell_h + gap_cell), cell_w, cell_h)
            draw_rounded_panel(rect, WHITE, theme_light, 4, radius=18)
            if question.icon_options:
                icon = get_icon(option, 60)
                screen.blit(icon, icon.get_rect(center=rect.center))
            else:
                opt_surf = fit_text(str(option), rect.width - 20, font_big, font_medium, font_small, font_tiny)
                screen.blit(opt_surf, opt_surf.get_rect(center=rect.center))
            option_rects.append((option, rect))

        # Message de retour (succes / encouragement)
        if message:
            banner_rect = pygame.Rect(WIDTH // 2 - 220, 520, 440, 55)
            bg = GREEN_BANNER_BG if is_correct else RED_BANNER_BG
            fg = GREEN if is_correct else RED
            draw_rounded_panel(banner_rect, bg, radius=16)
            msg_surf = font_medium.render(message, True, fg)
            screen.blit(msg_surf, msg_surf.get_rect(center=banner_rect.center))

        confetti.update_and_draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

        if waiting_next and pygame.time.get_ticks() >= next_time:
            question = engine.generate_question()
            message = ""
            is_correct = None
            waiting_next = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif back_button_clicked(event, back_rect):
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and not waiting_next:
                pos = pygame.mouse.get_pos()
                for option, rect in option_rects:
                    if rect.collidepoint(pos):
                        if GameEngine.check_answer(option, question.answer):
                            engine.increment_score()
                            message = engine.success_message()
                            is_correct = True
                            confetti.burst(WIDTH // 2, HEIGHT // 2 - 60)
                            if question.audio_key and hasattr(engine, "sounds"):
                                jouer_son_si_disponible(engine.sounds, question.audio_key)
                            waiting_next = True
                            next_time = pygame.time.get_ticks() + 1300
                        else:
                            message = engine.FAILURE_MESSAGE
                            is_correct = False
                        break



AGE_GROUPS = [
    {"range": "1-3 ans", "label": "Tout-petits", "age": 2, "desc": "Decouverte des chiffres et lettres",
     "color": BLUE_TIER, "light": BLUE_TIER_LIGHT},
    {"range": "4-6 ans", "label": "Maternelle", "age": 5, "desc": "Calculs simples et associations",
     "color": GREEN_TIER, "light": GREEN_TIER_LIGHT},
    {"range": "7-10 ans", "label": "Primaire", "age": 8, "desc": "Defis plus complexes",
     "color": PURPLE_TIER, "light": PURPLE_TIER_LIGHT},
]


def draw_age_icon(label, color, center, radius):
    if label == "Tout-petits":
        pygame.draw.circle(screen, color, center, radius)
        pygame.draw.circle(screen, WHITE, (center[0] - radius*0.3, center[1] - radius*0.1), radius*0.15)
        pygame.draw.circle(screen, WHITE, (center[0] + radius*0.3, center[1] - radius*0.1), radius*0.15)
        pygame.draw.arc(screen, WHITE, (center[0]-radius*0.4, center[1], radius*0.8, radius*0.5), math.pi, 2*math.pi, 3)
    elif label == "Maternelle":
        rect = pygame.Rect(0, 0, radius*1.4, radius*1.1)
        rect.center = center
        pygame.draw.rect(screen, color, rect, border_radius=6)
        for i in range(3):
            y = rect.top + 15 + i * 12
            pygame.draw.line(screen, WHITE, (rect.left + 10, y), (rect.right - 10, y), 3)
    else:
        pts = [(center[0], center[1] - radius*0.6), (center[0] + radius, center[1]),
               (center[0], center[1] + radius*0.6), (center[0] - radius, center[1])]
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.line(screen, color, (center[0] + radius*0.6, center[1] + radius*0.2),
                          (center[0] + radius*0.6, center[1] + radius*0.9), 3)


def age_selection_screen():
    while True:
        screen.fill(BG_LIGHT)
        title = font_huge.render("Bienvenue !", True, SLATE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        subtitle = font_medium.render("Quel age as-tu ?", True, SLATE_SOFT)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 140))

        card_w, card_h, gap = 220, 260, 20
        start_x = WIDTH // 2 - (card_w * 3 + gap * 2) // 2
        y = 210
        cards = []
        for i, group in enumerate(AGE_GROUPS):
            rect = pygame.Rect(start_x + i * (card_w + gap), y, card_w, card_h)
            draw_rounded_panel(rect, WHITE, group["color"], 4)
            icon_center = (rect.centerx, rect.top + 60)
            draw_age_icon(group["label"], group["color"], icon_center, 32)
            range_surf = font_medium.render(group["range"], True, SLATE)
            screen.blit(range_surf, (rect.centerx - range_surf.get_width() // 2, rect.top + 105))
            label_surf = font.render(group["label"], True, SLATE_SOFT)
            screen.blit(label_surf, (rect.centerx - label_surf.get_width() // 2, rect.top + 140))
            desc_surf = font_tiny.render(group["desc"], True, SLATE_SOFT)
            screen.blit(desc_surf, (rect.centerx - desc_surf.get_width() // 2, rect.top + 190))
            cards.append((group["age"], rect))

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for age, rect in cards:
                    if rect.collidepoint(pos):
                        return age


# ============================================================
# Ecran d'accueil (choix de la matiere)
# ============================================================
GAMES = [
    {"key": "math", "label": "Maths", "desc": "Additions et calculs amusants", "color": INDIGO, "light": INDIGO_LIGHT},
    {"key": "alphabet", "label": "Alphabet", "desc": "Apprends tes lettres de A a Z", "color": PINK, "light": PINK_LIGHT},
    {"key": "image", "label": "Images", "desc": "Reconnais les objets", "color": EMERALD, "light": EMERALD_LIGHT},
    {"key": "histoire", "label": "Histoire", "desc": "Decouvre le Mali", "color": ORANGE, "light": (255, 231, 199)},
]


def draw_game_icon(key, color, center, radius):
    if key == "math":
        rect = pygame.Rect(0, 0, radius*1.2, radius*1.2)
        rect.center = center
        pygame.draw.line(screen, color, (rect.centerx, rect.top), (rect.centerx, rect.bottom), 4)
        pygame.draw.line(screen, color, (rect.left, rect.centery), (rect.right, rect.centery), 4)
    elif key == "alphabet":
        letter = font_medium.render("A", True, color)
        screen.blit(letter, letter.get_rect(center=center))
    elif key == "image":
        rect = pygame.Rect(0, 0, radius*1.6, radius*1.2)
        rect.center = center
        pygame.draw.rect(screen, color, rect, width=3, border_radius=6)
        pygame.draw.circle(screen, color, (rect.left + 15, rect.top + 15), 5)
        pygame.draw.polygon(screen, color, [(rect.left+10, rect.bottom-10), (rect.centerx, rect.top+15), (rect.right-10, rect.bottom-10)])
    else:
        rect = pygame.Rect(0, 0, radius*1.1, radius*1.3)
        rect.center = center
        pygame.draw.rect(screen, color, rect, border_radius=4)
        for i in range(3):
            y = rect.top + 12 + i * 10
            pygame.draw.line(screen, WHITE, (rect.left + 8, y), (rect.right - 8, y), 2)


def home_screen(age, engines_sounds):
    while True:
        screen.fill(BG_LIGHT)
        change_age_rect = pygame.Rect(20, 20, 170, 40)
        draw_rounded_panel(change_age_rect, WHITE, SLATE_SOFT, 1, radius=20)
        change_label = font_small.render("< Changer d'age", True, SLATE_SOFT)
        screen.blit(change_label, change_label.get_rect(center=change_age_rect.center))

        title = font_huge.render("Jeu Educatif", True, SLATE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 70))
        subtitle = font.render("Apprends en t'amusant !", True, SLATE_SOFT)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 140))

        card_w, card_h, gap = 170, 190, 20
        start_x = WIDTH // 2 - (card_w * 4 + gap * 3) // 2
        y = 210
        cards = []
        for i, game in enumerate(GAMES):
            rect = pygame.Rect(start_x + i * (card_w + gap), y, card_w, card_h)
            draw_rounded_panel(rect, WHITE, game["color"], 3)
            icon_center = (rect.centerx, rect.top + 55)
            draw_game_icon(game["key"], game["color"], icon_center, 26)
            label_surf = font_medium.render(game["label"], True, SLATE)
            screen.blit(label_surf, (rect.centerx - label_surf.get_width() // 2, rect.top + 100))
            desc_surf = font_tiny.render(game["desc"], True, SLATE_SOFT)
            screen.blit(desc_surf, (rect.centerx - desc_surf.get_width() // 2, rect.top + 135))
            cards.append((game["key"], rect))

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if change_age_rect.collidepoint(pos):
                    return None
                for key, rect in cards:
                    if rect.collidepoint(pos):
                        lancer_jeu(key, age, engines_sounds)


def lancer_jeu(key, age, sounds):
    chiffres_sounds, lettres_sounds = sounds
    if key == "math":
        engine = MathGameEngine(age, sounds=chiffres_sounds)
        run_quiz_screen(engine, "Mathematiques", INDIGO, INDIGO_LIGHT)
    elif key == "alphabet":
        engine = AlphabetGameEngine(age, sounds=lettres_sounds)
        run_quiz_screen(engine, "Alphabet", PINK, PINK_LIGHT)
    elif key == "image":
        engine = ImageGameEngine(age)
        run_quiz_screen(engine, "Images", EMERALD, EMERALD_LIGHT)
    elif key == "histoire":
        engine = HistoireGameEngine(age)
        run_quiz_screen(engine, "Histoire du Mali", ORANGE, (255, 231, 199))



def main():
    chiffres_sounds = charger_sons_chiffres()
    lettres_sounds = charger_sons_lettres()
    if not os.path.isdir(SOUNDS_DIR):
        print(f"Attention : dossier de sons introuvable ({SOUNDS_DIR}). Le jeu fonctionnera sans audio.")

    while True:
        age = age_selection_screen()
        home_screen(age, (chiffres_sounds, lettres_sounds))


if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()
