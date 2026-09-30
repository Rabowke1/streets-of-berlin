"""Figuren-Definitionen und Animationen (Posen) fuer Streets of Berlin.

Alle Figuren schauen im Sprite nach rechts; das Spiel spiegelt sie.
Animationsnamen sind fuer alle Figuren gleich, damit das Spiel sie
einheitlich ansprechen kann (siehe ANIM in web/js/data.js).
"""
import math

from puppet import Character, blend, pose

# ---------------------------------------------------------------------------
# Figuren
# ---------------------------------------------------------------------------
RED = (214, 64, 42, 255)


def make_characters():
    chars = {}

    chars["Kai"] = dict(
        char=Character(
            "Kai",
            top=RED, top_inner=(34, 32, 38, 255), sleeve_upper=RED, sleeve_lower=RED,
            glove=(40, 36, 40, 255), pants=(46, 70, 124, 255), shoe=(244, 244, 240, 255),
            hair=(52, 34, 26, 255), hair_style="short",
        ),
        style="player", scale=1.0,
    )

    # Zweite Spielfigur: Leyla – schnelle Kickboxerin/Streetdancerin
    LILAC = (126, 70, 196, 255)
    chars["Leyla"] = dict(
        char=Character(
            "Leyla",
            head_r=17, torso=57, chest_w=42, waist_w=30, arm_w=(8.0, 8.5, 6.5), fore_w=(7.0, 7.5, 5.5), fist_r=8.5,
            thigh=47, shin=45, thigh_w=(11.5, 11.5, 8.0), shin_w=(8.5, 8.5, 6.5), shoe_len=27, shoe_h=12,
            top=LILAC, top_inner=(40, 200, 190, 255), sleeve_upper=LILAC, sleeve_lower=(40, 200, 190, 255),
            glove=(250, 210, 60, 255), pants=(34, 30, 44, 255), stripe=(250, 210, 60, 255),
            shoe=(250, 250, 246, 255), sole=(250, 210, 60, 255), hair=(150, 40, 36, 255), hair_style="ponytail",
            skin=(200, 140, 104, 255), earring=True,
        ),
        style="player2", scale=0.98,
    )

    punk = dict(
        top=(70, 96, 140, 255), top_inner=(226, 170, 132, 255), pants=(34, 32, 36, 255),
        shoe=(60, 40, 34, 255), sole=(24, 22, 22, 255), hair_style="mohawk", earring=True,
        chest_w=46, waist_w=32, skin=(226, 168, 130, 255),
    )
    chars["Kalle"] = dict(char=Character("Kalle", hair=(80, 200, 70, 255), **punk), style="punk", scale=1.0)
    punk2 = dict(punk, top=(44, 40, 46, 255), pants=(96, 30, 40, 255))
    chars["Ronny"] = dict(char=Character("Ronny", hair=(240, 80, 170, 255), **punk2), style="punk", scale=1.0)

    skater = dict(
        pants=(160, 140, 96, 255), shorts=True, shoe=(250, 250, 250, 255), sole=(200, 40, 40, 255),
        hair_style="cap", chest_w=44, waist_w=32, torso=58,
        arm_w=(8.5, 9.0, 7.0), fore_w=(7.5, 8.0, 6.0), thigh_w=(11.0, 11.0, 8.0), shin_w=(8.0, 8.0, 6.5),
    )
    chars["Jojo"] = dict(char=Character(
        "Jojo", top=(240, 196, 40, 255), sleeve_upper=(240, 196, 40, 255), sleeve_lower=(240, 196, 40, 255),
        cap_color=(30, 60, 150, 255), skin=(160, 106, 70, 255), hair=(22, 18, 18, 255), **skater),
        style="skater", scale=0.96)
    chars["Deniz"] = dict(char=Character(
        "Deniz", top=(90, 180, 110, 255), sleeve_upper=(90, 180, 110, 255), sleeve_lower=(90, 180, 110, 255),
        cap_color=(200, 40, 50, 255), skin=(210, 150, 110, 255), hair=(30, 22, 18, 255), **skater),
        style="skater", scale=0.96)

    heavy = dict(
        head_r=19, torso=66, chest_w=74, waist_w=64, belly=12,
        arm_w=(13.0, 14.5, 11.0), fore_w=(11.5, 12.0, 9.5), fist_r=12.5,
        thigh_w=(16.0, 16.0, 12.0), shin_w=(12.0, 12.0, 9.5), thigh=44, shin=40, shoe_len=32, shoe_h=13,
    )
    chars["Brecher"] = dict(char=Character(
        "Brecher", top=(236, 236, 228, 255), pants=(30, 30, 38, 255), stripe=(240, 240, 240, 255),
        shoe=(40, 40, 46, 255), sole=(240, 240, 240, 255), hair_style="bald", beard=True,
        hair=(120, 70, 40, 255), skin=(236, 180, 150, 255), **heavy), style="heavy", scale=1.1)
    boss = dict(heavy, chest_w=80, waist_w=66, belly=8)
    chars["Rolf"] = dict(char=Character(
        "Rolf", top=(28, 28, 32, 255), sleeve_upper=(28, 28, 32, 255), pants=(24, 24, 30, 255),
        shoe=(20, 20, 20, 255), sole=(60, 60, 60, 255), hair_style="bald", beard=True, shades=True,
        hair=(40, 30, 28, 255), skin=(200, 146, 110, 255), logo_color=(230, 200, 60, 255), **boss),
        style="heavy", scale=1.22)

    # --- Neue Gegner (Stage 2/3) ---------------------------------------------
    kicker = dict(
        head_r=17, torso=56, chest_w=40, waist_w=28, arm_w=(7.5, 8.0, 6.0), fore_w=(6.5, 7.0, 5.5), fist_r=8.0,
        thigh=46, shin=44, thigh_w=(11.0, 11.0, 7.5), shin_w=(8.0, 8.0, 6.0), shoe_len=26, shoe_h=11,
        hair_style="ponytail", sole=(240, 240, 240, 255),
    )
    chars["Zoe"] = dict(char=Character(
        "Zoe", top=(40, 200, 200, 255), pants=(40, 36, 60, 255), shoe=(250, 110, 150, 255), hair=(30, 24, 22, 255),
        skin=(214, 158, 118, 255), glove=(200, 40, 60, 255), **kicker), style="kicker", scale=0.98)
    chars["Nina"] = dict(char=Character(
        "Nina", top=(240, 120, 40, 255), pants=(20, 20, 26, 255), shoe=(250, 250, 250, 255), hair=(236, 200, 120, 255),
        skin=(240, 196, 166, 255), glove=(30, 30, 36, 255), **kicker), style="kicker", scale=0.98)

    chars["Micha"] = dict(char=Character(
        "Micha", hair=(250, 230, 70, 255), **dict(punk, top=(110, 40, 40, 255), pants=(40, 50, 70, 255))),
        style="punk", scale=1.0)

    chars["Sven"] = dict(char=Character(
        "Sven", top=(26, 30, 26, 255), sleeve_upper=(26, 30, 26, 255), sleeve_lower=(26, 30, 26, 255),
        pants=(80, 86, 70, 255), shoe=(30, 26, 22, 255), sole=(20, 18, 16, 255), hair_style="buzz",
        hair=(150, 110, 70, 255), skin=(234, 184, 150, 255), logo_color=(230, 120, 30, 255),
        **dict(heavy, chest_w=72, waist_w=58, belly=6)), style="heavy", scale=1.16)

    chars["Harald"] = dict(char=Character(
        "Harald", top=(120, 124, 136, 255), top_inner=(240, 240, 236, 255), sleeve_upper=(120, 124, 136, 255),
        sleeve_lower=(120, 124, 136, 255), pants=(96, 100, 112, 255), shoe=(60, 36, 24, 255),
        sole=(30, 20, 16, 255), hair_style="slick", hair=(170, 170, 176, 255), skin=(236, 190, 160, 255),
        tie=(180, 30, 40, 255), chest_w=52, waist_w=40, cap_color=(236, 190, 60, 255)), style="boss_harald",
        scale=1.12)
    # Bauhelm in Gold statt Frisur: der Baulöwe auf seiner eigenen Baustelle
    chars["Harald"]["char"].hair_style = "hardhat"

    # --- Endgegner mit Berlin-Bezug ----------------------------------------------
    # Stage 1: Fahrkartenkontrolleur im U-Bahnhof
    chars["Klaus"] = dict(char=Character(
        "Klaus", top=(38, 44, 62, 255), sleeve_upper=(38, 44, 62, 255), sleeve_lower=(38, 44, 62, 255),
        pants=(34, 38, 52, 255), shoe=(22, 20, 20, 255), sole=(50, 50, 50, 255), hair_style="uniform",
        cap_color=(34, 40, 58, 255), mustache=True, hair=(90, 70, 60, 255), skin=(226, 168, 132, 255),
        vest=(250, 214, 40, 255), glove=(30, 30, 34, 255),
        **dict(heavy, chest_w=70, waist_w=64, belly=16)), style="boss_klaus", scale=1.18)
    # Kontrolleure, die Klaus per Pfiff ruft
    chars["Kontrolli"] = dict(char=Character(
        "Kontrolli", **dict(punk, hair_style="uniform", cap_color=(34, 40, 58, 255), vest=(250, 214, 40, 255),
                            top=(38, 44, 62, 255), pants=(34, 38, 52, 255), earring=False, hair=(60, 44, 36, 255),
                            shoe=(22, 20, 20, 255))), style="punk", scale=1.0)
    # Stage 2: Tuersteher vor dem Club im Hinterhof ("Heute nicht.")
    chars["Tuer"] = dict(char=Character(
        "Tuer", top=(22, 22, 26, 255), sleeve_upper=(22, 22, 26, 255), sleeve_lower=(22, 22, 26, 255),
        pants=(18, 18, 22, 255), shoe=(14, 14, 16, 255), sole=(40, 40, 44, 255), hair_style="bald",
        beard=True, beard_color=(58, 56, 60, 255), face_tattoo=(30, 44, 96, 255), piercings=True,
        coat=(16, 16, 20, 255), chain=(210, 214, 222, 255), shades=False, skin=(214, 170, 146, 255),
        hair=(60, 60, 64, 255), **dict(heavy, chest_w=66, waist_w=54, belly=4)), style="boss_tuer", scale=1.24)
    return chars


# ---------------------------------------------------------------------------
# Animationen
# ---------------------------------------------------------------------------
def stance(style):
    style = {"boss_klaus": "heavy", "boss_tuer": "heavy", "boss_harald": "player"}.get(style, style)
    if style == "heavy":
        return pose(t=4, af=(26, 70), ab=(16, 60), lf=(14, 10, 0), lb=(-12, 10, 0), face="angry")
    if style == "punk":
        return pose(t=12, h=-4, af=(32, 95), ab=(16, 100), lf=(16, 16, 0), lb=(-14, 16, 0), face="angry")
    if style == "player2":
        return pose(t=6, af=(34, 112), ab=(20, 122), lf=(24, 14, 0), lb=(-20, 20, 0))
    if style == "kicker":
        return pose(t=4, af=(38, 110), ab=(24, 120), lf=(24, 14, 0), lb=(-20, 18, 0), face="angry")
    if style == "skater":
        return pose(t=8, af=(22, 70), ab=(12, 60), lf=(18, 20, 0), lb=(-16, 20, 0), face="angry")
    return pose(t=8, af=(40, 108), ab=(22, 125), lf=(20, 18, 0), lb=(-16, 20, 0))


def idle_anim(style):
    base = stance(style)
    out = []
    for i in range(4):
        k = (1 - math.cos(i / 4 * 2 * math.pi)) * 0.5
        p = dict(base)
        p["lf"] = (base["lf"][0], base["lf"][1] + 8 * k, 0)
        p["lb"] = (base["lb"][0], base["lb"][1] + 8 * k, 0)
        p["t"] = base["t"] + 2 * k
        p["af"] = (base["af"][0] - 3 * k, base["af"][1] + 4 * k)
        p["ab"] = (base["ab"][0] - 3 * k, base["ab"][1] + 4 * k)
        out.append(p)
    return out


def walk_anim(style, n=8):
    base = stance(style)
    amp = 22 if style != "heavy" else 17
    out = []
    for i in range(n):
        th = i / n * 2 * math.pi
        s, c = math.sin(th), math.cos(th)
        p = dict(base)
        hf = 4 + amp * s
        hb = 4 - amp * s
        p["lf"] = (hf, 8 + 32 * max(0.0, c), -max(0.0, -hf) * 0.6)
        p["lb"] = (hb, 8 + 32 * max(0.0, -c), -max(0.0, -hb) * 0.6)
        p["af"] = (base["af"][0] - 10 * s, base["af"][1])
        p["ab"] = (base["ab"][0] + 10 * s, base["ab"][1])
        p["t"] = base["t"] + 2
        out.append(p)
    return out


def with_legs(p, base):
    q = dict(p)
    q["lf"], q["lb"] = base["lf"], base["lb"]
    return q


def common_anims(style):
    """Animationen, die jede Figur hat."""
    st = stance(style)
    face = "angry" if style not in ("player", "player2") else "normal"
    A = {}
    A["idle"] = idle_anim(style)
    A["walk"] = walk_anim(style)
    A["hurt"] = [
        pose(t=-18, h=20, face="hurt", af=(10, 60), ab=(-12, 50), lf=(12, 14, 0), lb=(-20, 20, 0)),
        pose(t=-8, h=6, face="hurt", af=(18, 80), ab=(0, 70), lf=(16, 16, 0), lb=(-18, 18, 0)),
    ]
    A["grabbed"] = [
        pose(t=24, h=-10, face="hurt", af=(12, 30), ab=(4, 30), lf=(10, 20, 0), lb=(-14, 24, 0)),
        pose(t=30, h=-16, face="hurt", af=(20, 30), ab=(10, 30), lf=(12, 26, 0), lb=(-12, 30, 0)),
    ]
    A["fall"] = [
        pose(rot=30, t=-12, h=14, face="hurt", af=(150, 20), ab=(170, 10), lf=(40, 30, 0), lb=(22, 20, 0)),
        pose(rot=62, t=-6, h=10, face="hurt", af=(160, 30), ab=(175, 20), lf=(30, 20, 0), lb=(14, 30, 0)),
    ]
    A["down"] = [
        pose(rot=90, t=0, h=0, face="ko", af=(12, 12), ab=(20, 30), lf=(10, 12, 0), lb=(0, 4, 0)),
    ]
    A["getup"] = [
        pose(t=-38, h=4, face=face, af=(-24, 20), ab=(-36, 20), lf=(88, 6, 0), lb=(80, 14, 0)),
        pose(t=24, face=face, af=(40, 70), ab=(20, 60), lf=(80, 96, 0), lb=(-50, 112, -30)),
        pose(t=14, face=face, af=st["af"], ab=st["ab"], lf=(30, 50, 0), lb=(-20, 50, 0)),
    ]
    A["attack1"] = [
        with_legs(pose(t=6, face=face, af=(45, 110), ab=st["ab"]), pose(lf=(22, 18, 0), lb=(-18, 16, 0))),
        pose(t=14, face=face, af=(90, 0), ab=(25, 125), lf=(26, 14, 0), lb=(-22, 10, 0)),
        pose(t=10, face=face, af=(66, 60), ab=(24, 120), lf=(24, 16, 0), lb=(-20, 14, 0)),
    ]
    return A


def player_anims():
    A = common_anims("player")
    st = stance("player")
    A["attack2"] = [
        pose(t=4, af=(40, 100), ab=(8, 120), lf=(22, 18, 0), lb=(-18, 16, 0)),
        pose(t=18, af=(34, 112), ab=(92, 0), lf=(30, 16, 0), lb=(-24, 6, 0), dx=6),
        pose(t=12, af=(40, 108), ab=(60, 60), lf=(26, 16, 0), lb=(-20, 12, 0), dx=3),
    ]
    A["attack3"] = [
        pose(t=20, af=(46, 110), ab=(-12, 90), lf=(36, 52, 0), lb=(-10, 46, 0)),
        pose(t=6, af=(40, 108), ab=(110, 45), lf=(26, 26, 0), lb=(-14, 20, 0)),
        pose(t=-6, h=16, af=(34, 104), ab=(152, 18), lf=(14, 4, 0), lb=(-12, 4, -20)),
        pose(t=4, af=(40, 108), ab=(70, 80), lf=(20, 16, 0), lb=(-16, 16, 0)),
    ]
    A["attack4"] = [
        pose(t=-8, af=(50, 100), ab=(20, 110), lf=(84, 112, 10), lb=(-4, 6, 0)),
        pose(t=-32, h=6, af=(62, 80), ab=(-40, 50), lf=(104, 4, 16), lb=(-8, 2, 0)),
        pose(t=-30, h=6, af=(58, 84), ab=(-36, 54), lf=(100, 8, 12), lb=(-8, 2, 0)),
        pose(t=-10, af=(50, 100), ab=(10, 110), lf=(70, 100, 0), lb=(-6, 6, 0)),
        pose(t=8, af=st["af"], ab=st["ab"], lf=(24, 22, 0), lb=(-16, 22, 0)),
    ]
    A["jump"] = [
        pose(t=0, af=(120, 40), ab=(80, 60), lf=(60, 92, 10), lb=(22, 100, -10)),
        pose(t=4, af=(80, 30), ab=(58, 34), lf=(30, 40, 0), lb=(-10, 40, -10)),
    ]
    A["jump_kick"] = [
        pose(t=-4, af=(60, 100), ab=(30, 110), lf=(70, 104, 10), lb=(10, 92, -10)),
        pose(t=-20, h=4, af=(40, 92), ab=(-30, 60), lf=(78, 0, 14), lb=(22, 100, -10)),
    ]
    A["special"] = [
        pose(t=22, af=(64, 140), ab=(72, 140), lf=(32, 50, 0), lb=(-24, 46, 0), face="shout"),
        pose(t=0, af=(95, 0), ab=(-95, 0), lf=(30, 10, 0), lb=(-30, 10, 0), face="shout"),
        pose(t=-2, af=(-95, 0), ab=(95, 0), lf=(-26, 10, 0), lb=(28, 10, 0), face="shout"),
        pose(t=0, af=(100, 0), ab=(-100, 0), lf=(30, 10, 0), lb=(-30, 10, 0), face="shout"),
        pose(t=-2, af=(-100, 0), ab=(100, 0), lf=(-26, 10, 0), lb=(28, 10, 0), face="shout"),
        pose(t=10, af=st["af"], ab=st["ab"], lf=(24, 28, 0), lb=(-18, 28, 0)),
    ]
    A["back_attack"] = [
        pose(t=2, h=4, af=(30, 110), ab=(-40, 120), lf=(18, 16, 0), lb=(-18, 16, 0)),
        pose(t=-14, h=6, af=(-50, 140), ab=(-96, 160), lf=(10, 12, 0), lb=(-26, 10, 0), dx=-6),
        pose(t=0, af=(20, 110), ab=(-30, 120), lf=(16, 16, 0), lb=(-18, 16, 0)),
    ]
    A["grab"] = [
        pose(t=12, af=(78, 30), ab=(70, 44), lf=(22, 16, 0), lb=(-18, 14, 0), hf="open", hb="open"),
    ]
    A["grab_knee"] = [
        pose(t=14, af=(70, 60), ab=(62, 60), lf=(18, 20, 0), lb=(-18, 16, 0), hf="open", hb="open"),
        pose(t=18, af=(52, 90), ab=(46, 90), lf=(96, 132, 0), lb=(-10, 6, 0), hf="open", hb="open"),
        pose(t=14, af=(70, 60), ab=(62, 60), lf=(22, 18, 0), lb=(-18, 16, 0), hf="open", hb="open"),
    ]
    A["throw"] = [
        pose(t=-10, af=(40, 60), ab=(30, 70), lf=(26, 20, 0), lb=(-20, 24, 0), hf="open", hb="open"),
        pose(t=-26, h=10, af=(160, 20), ab=(150, 30), lf=(16, 10, 0), lb=(-18, 10, 0), hf="open", hb="open"),
        pose(t=26, af=(100, 10), ab=(90, 10), lf=(36, 20, 0), lb=(-26, 0, -20), hf="open", hb="open",
             face="shout"),
        pose(t=12, af=st["af"], ab=st["ab"], lf=(26, 20, 0), lb=(-20, 18, 0)),
    ]
    A["pickup"] = [pose(t=42, af=(62, 10), ab=(30, 40), lf=(60, 100, 0), lb=(-24, 104, -20), hf="open")]
    A["victory"] = [
        pose(t=-4, h=10, af=(172, 8), ab=(20, 120), lf=(16, 8, 0), lb=(-14, 8, 0), face="shout"),
        pose(t=-6, h=14, af=(176, 4), ab=(24, 118), lf=(16, 6, 0), lb=(-14, 6, 0), face="shout"),
    ]
    return A


def leyla_anims():
    """Leyla: gleiche Grundbewegungen wie Kai, aber eigene Angriffe (Kicks statt Faeuste)."""
    A = player_anims()
    st = stance("player2")
    for k, v in common_anims("player2").items():
        if k in ("idle", "walk"):
            A[k] = v
    A["attack1"] = [
        pose(t=4, af=(40, 110), ab=st["ab"], lf=(26, 18, 0), lb=(-20, 18, 0)),
        pose(t=12, af=(92, 0), ab=(20, 120), lf=(28, 14, 0), lb=(-24, 10, 0)),
        pose(t=8, af=(60, 70), ab=(20, 120), lf=(26, 16, 0), lb=(-22, 14, 0)),
    ]
    A["attack2"] = [  # schneller Front-Kick
        pose(t=-4, af=st["af"], ab=st["ab"], lf=(70, 100, 10), lb=(-10, 10, 0)),
        pose(t=-14, af=(50, 100), ab=(10, 110), lf=(84, 4, 20), lb=(-8, 6, 0)),
        pose(t=-2, af=st["af"], ab=st["ab"], lf=(40, 60, 0), lb=(-14, 12, 0)),
    ]
    A["attack3"] = [  # steigendes Knie
        pose(t=10, af=(60, 90), ab=(50, 90), lf=(40, 60, 0), lb=(-16, 20, 0)),
        pose(t=-8, h=10, af=(120, 40), ab=(110, 50), lf=(104, 130, 0), lb=(-12, 4, -20)),
        pose(t=0, af=st["af"], ab=st["ab"], lf=(40, 50, 0), lb=(-14, 12, 0)),
    ]
    A["attack4"] = [  # Dreh-Roundhouse
        pose(t=-6, rot=-8, af=(60, 100), ab=(-20, 80), lf=(90, 120, 10), lb=(-6, 6, 0)),
        pose(t=-30, rot=-14, h=8, af=(80, 40), ab=(-70, 30), lf=(118, 2, 24), lb=(-6, 2, 0), face="shout"),
        pose(t=-26, rot=-10, h=8, af=(70, 50), ab=(-60, 40), lf=(112, 6, 20), lb=(-6, 2, 0), face="shout"),
        pose(t=-6, af=(50, 100), ab=(10, 110), lf=(60, 90, 0), lb=(-8, 8, 0)),
        pose(t=6, af=st["af"], ab=st["ab"], lf=(26, 22, 0), lb=(-18, 22, 0)),
    ]
    A["jump_kick"] = [  # Hechtsprung-Kick schraeg nach unten
        pose(t=-6, af=(80, 80), ab=(40, 100), lf=(80, 110, 10), lb=(20, 100, -10)),
        pose(t=-34, rot=-24, h=4, af=(20, 60), ab=(150, 30), lf=(62, 0, 10), lb=(30, 110, -10), face="shout"),
    ]
    A["special"] = [  # Helikopter-Kick: Beine gespreizt, Koerper dreht
        pose(t=30, af=(90, 120), ab=(90, 120), lf=(40, 80, 0), lb=(-30, 80, 0), face="shout"),
        pose(t=0, rot=-80, af=(170, 10), ab=(150, 20), lf=(90, 0, 0), lb=(-80, 0, 0), face="shout"),
        pose(t=0, rot=-130, af=(170, 10), ab=(150, 20), lf=(-80, 0, 0), lb=(90, 0, 0), face="shout"),
        pose(t=0, rot=-80, af=(170, 10), ab=(150, 20), lf=(90, 0, 0), lb=(-80, 0, 0), face="shout"),
        pose(t=0, rot=-130, af=(170, 10), ab=(150, 20), lf=(-80, 0, 0), lb=(90, 0, 0), face="shout"),
        pose(t=14, af=st["af"], ab=st["ab"], lf=(30, 40, 0), lb=(-22, 40, 0)),
    ]
    A["back_attack"] = [  # Rueck-Tritt (Esel-Kick)
        pose(t=24, h=-6, af=(40, 110), ab=(20, 110), lf=(20, 30, 0), lb=(-40, 90, 0)),
        pose(t=46, h=-14, af=(30, 80), ab=(10, 80), lf=(10, 20, 0), lb=(-104, 4, -30), face="shout"),
        pose(t=10, af=st["af"], ab=st["ab"], lf=(20, 20, 0), lb=(-20, 30, 0)),
    ]
    A["victory"] = [
        pose(t=-4, h=12, af=(160, 60), ab=(20, 120), lf=(20, 10, 0), lb=(-30, 20, 0), face="shout", hf="open"),
        pose(t=-8, h=16, af=(166, 50), ab=(24, 118), lf=(22, 8, 0), lb=(-34, 24, 0), face="shout", hf="open"),
    ]
    return A


def punk_anims():
    A = common_anims("punk")
    st = stance("punk")
    A["attack2"] = [
        pose(t=-6, face="angry", af=(30, 90), ab=(-64, 60), lf=(22, 18, 0), lb=(-18, 16, 0)),
        pose(t=6, face="shout", af=(20, 80), ab=(40, 50), lf=(26, 16, 0), lb=(-20, 12, 0)),
        pose(t=22, face="shout", af=(10, 60), ab=(96, 4), lf=(32, 16, 0), lb=(-26, 6, 0), dx=6),
        pose(t=14, face="angry", af=st["af"], ab=(50, 70), lf=(26, 16, 0), lb=(-20, 14, 0)),
    ]
    return A


def skater_anims():
    A = common_anims("skater")
    st = stance("skater")
    A["attack2"] = [
        pose(t=24, face="angry", af=(40, 60), ab=(20, 60), lf=(40, 60, 0), lb=(-20, 60, 0)),
        pose(t=-52, face="shout", af=(-20, 16), ab=(60, 70), lf=(86, 0, 10), lb=(40, 96, 0), hf="open"),
        pose(t=-48, face="shout", af=(-24, 16), ab=(56, 70), lf=(84, 2, 10), lb=(38, 96, 0), hf="open"),
        pose(t=20, face="angry", af=st["af"], ab=st["ab"], lf=(30, 44, 0), lb=(-20, 44, 0)),
    ]
    return A


def heavy_anims():
    A = common_anims("heavy")
    A["attack1"] = [
        pose(t=-12, face="shout", af=(170, 30), ab=(164, 30), lf=(16, 12, 0), lb=(-14, 12, 0)),
        pose(t=14, face="shout", af=(104, 20), ab=(98, 20), lf=(20, 16, 0), lb=(-16, 12, 0)),
        pose(t=34, face="angry", af=(62, 12), ab=(56, 12), lf=(24, 24, 0), lb=(-18, 16, 0), dx=4),
        pose(t=16, face="angry", af=(40, 50), ab=(30, 50), lf=(18, 16, 0), lb=(-14, 12, 0)),
    ]
    A["attack2"] = []
    for i in range(4):
        th = i / 4 * 2 * math.pi
        s, c = math.sin(th), math.cos(th)
        A["attack2"].append(pose(
            t=34, h=-6, face="shout", af=(56, 96), ab=(26, 100),
            lf=(10 + 34 * s, 12 + 40 * max(0.0, c), 0), lb=(10 - 34 * s, 12 + 40 * max(0.0, -c), 0)))
    return A


def weapon_anims(style):
    """Waffen-Animationen (Waffe selbst wird von der Engine am Hand-Anker gezeichnet)."""
    st = stance(style)
    face = "angry" if style not in ("player", "player2") else "normal"
    return {
        "weapon_swing": [
            pose(t=-12, face=face, af=(168, 40), ab=(30, 100), lf=(20, 18, 0), lb=(-18, 16, 0)),
            pose(t=4, face="shout", af=(120, 10), ab=(30, 100), lf=(26, 16, 0), lb=(-20, 12, 0)),
            pose(t=22, face="shout", af=(70, 4), ab=(20, 90), lf=(34, 20, 0), lb=(-26, 6, 0), dx=6),
            pose(t=12, face=face, af=(40, 30), ab=st["ab"], lf=(26, 18, 0), lb=(-20, 14, 0)),
        ],
        "weapon_throw": [
            pose(t=-14, face=face, af=(-50, 70), ab=(60, 80), lf=(22, 18, 0), lb=(-20, 18, 0)),
            pose(t=18, face="shout", af=(96, 0), ab=(-20, 60), lf=(34, 18, 0), lb=(-26, 4, -20), dx=4),
            pose(t=10, face=face, af=(60, 40), ab=st["ab"], lf=(26, 18, 0), lb=(-20, 14, 0)),
        ],
    }


def kicker_anims():
    A = common_anims("kicker")
    st = stance("kicker")
    A["attack1"] = [
        pose(t=0, face="angry", af=st["af"], ab=st["ab"], lf=(70, 110, 10), lb=(-10, 8, 0)),
        pose(t=-12, face="shout", af=(50, 110), ab=(10, 100), lf=(94, 4, 10), lb=(-8, 4, 0)),
        pose(t=-2, face="angry", af=st["af"], ab=st["ab"], lf=(60, 100, 0), lb=(-12, 8, 0)),
    ]
    A["attack2"] = [
        pose(t=10, face="angry", af=(60, 100), ab=(30, 110), lf=(30, 60, 0), lb=(-20, 60, 0)),
        pose(t=-30, face="shout", af=(80, 60), ab=(-60, 40), lf=(110, 2, 20), lb=(20, 90, -20)),
        pose(t=-36, face="shout", af=(90, 40), ab=(-70, 30), lf=(118, 0, 20), lb=(24, 96, -20)),
        pose(t=6, face="angry", af=st["af"], ab=st["ab"], lf=(40, 60, 0), lb=(-20, 50, 0)),
    ]
    return A


def boss_klaus_anims():
    A = heavy_anims()
    st = stance("heavy")
    # Pfiff: Hand zum Mund, ruft Verstaerkung
    A["whistle"] = [
        pose(t=2, face="angry", af=(50, 130), ab=st["ab"], lf=(14, 10, 0), lb=(-12, 10, 0)),
        pose(t=-6, h=-10, face="shout", af=(58, 150), ab=(30, 40), lf=(14, 10, 0), lb=(-12, 10, 0)),
    ]
    # "Fahrschein, bitte!": fordernd zeigen
    A["point"] = [
        pose(t=8, face="shout", af=(96, 4), ab=(20, 60), lf=(22, 16, 0), lb=(-16, 12, 0)),
        pose(t=10, face="angry", af=(92, 10), ab=(20, 60), lf=(22, 16, 0), lb=(-16, 12, 0)),
    ]
    return A


def boss_tuer_anims():
    A = heavy_anims()
    st = stance("heavy")
    # Deckung: Arme vor der Brust verschraenkt
    A["guard"] = [
        pose(t=-4, face="angry", af=(70, 125), ab=(62, 128), lf=(18, 10, 0), lb=(-16, 10, 0)),
        pose(t=-2, face="angry", af=(72, 122), ab=(64, 126), lf=(18, 12, 0), lb=(-16, 12, 0)),
    ]
    # "Du kommst hier nicht rein!": beidhaendiger Stoss
    A["shove"] = [
        pose(t=-10, face="angry", af=(24, 120), ab=(16, 118), lf=(14, 12, 0), lb=(-14, 12, 0)),
        pose(t=20, face="shout", af=(88, 6), ab=(82, 8), lf=(30, 18, 0), lb=(-24, 8, 0), dx=8),
        pose(t=14, face="angry", af=(74, 30), ab=(66, 34), lf=(26, 16, 0), lb=(-20, 10, 0), dx=4),
    ]
    A["point"] = [
        pose(t=4, face="angry", af=(120, 6), ab=st["ab"], lf=(16, 10, 0), lb=(-14, 10, 0)),
        pose(t=6, face="shout", af=(116, 10), ab=st["ab"], lf=(16, 10, 0), lb=(-14, 10, 0)),
    ]
    return A


def boss_harald_anims():
    A = player_anims()
    # Ruft den Kran: Arm hoch
    A["point"] = [
        pose(t=4, face="shout", af=(150, 10), ab=(20, 60), lf=(20, 18, 0), lb=(-16, 20, 0)),
        pose(t=6, face="shout", af=(160, 4), ab=(20, 60), lf=(20, 18, 0), lb=(-16, 20, 0)),
    ]
    return A


def _with_weapons(fn, style):
    def make():
        A = fn()
        A.update(weapon_anims(style))
        return A
    return make


ANIMS_BY_STYLE = {
    "player": _with_weapons(player_anims, "player"),
    "player2": _with_weapons(leyla_anims, "player"),
    "punk": _with_weapons(punk_anims, "punk"),
    "skater": skater_anims,
    "heavy": _with_weapons(heavy_anims, "heavy"),
    "kicker": kicker_anims,
    "boss_klaus": _with_weapons(boss_klaus_anims, "heavy"),
    "boss_tuer": _with_weapons(boss_tuer_anims, "heavy"),
    "boss_harald": _with_weapons(boss_harald_anims, "player"),
}
