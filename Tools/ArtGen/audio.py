"""Prozedurale Soundeffekte und ein kurzer Musik-Loop (16-bit WAV, mono)."""
import os
import wave

import numpy as np

RATE = 44100


def _write(path, data):
    data = np.clip(data, -1.0, 1.0)
    pcm = (data * 32000).astype(np.int16)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())


def _t(dur):
    return np.linspace(0, dur, int(RATE * dur), endpoint=False)


def _env(t, attack, decay):
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)


def _noise(n, rng):
    return rng.uniform(-1, 1, n)


def _lowpass(x, k):
    kernel = np.ones(k) / k
    return np.convolve(x, kernel, mode="same")


def hit(heavy, rng):
    dur = 0.35 if heavy else 0.2
    t = _t(dur)
    f0 = 110 if heavy else 180
    freq = f0 * np.exp(-t * 18) + 40
    body = np.sin(2 * np.pi * np.cumsum(freq) / RATE) * _env(t, 0.001, 0.09 if heavy else 0.05)
    snap = _lowpass(_noise(len(t), rng), 3) * _env(t, 0.0005, 0.02 if heavy else 0.012)
    return (body * 0.9 + snap * 0.7) * 0.9


def whoosh(rng, dur=0.22):
    t = _t(dur)
    n = _noise(len(t), rng)
    n = _lowpass(n, 6)
    env = np.sin(np.pi * t / dur) ** 2
    return n * env * 0.6


def thud(rng):
    t = _t(0.5)
    freq = 70 * np.exp(-t * 6) + 30
    body = np.sin(2 * np.pi * np.cumsum(freq) / RATE) * _env(t, 0.002, 0.15)
    n = _lowpass(_noise(len(t), rng), 20) * _env(t, 0.001, 0.08)
    return body + n * 0.8


def crash(rng):
    t = _t(0.6)
    n = _noise(len(t), rng)
    out = n * _env(t, 0.001, 0.12) * 0.7
    for f in (820, 1330, 2210, 3170):
        out += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * _env(t, 0.001, 0.18) * 0.12
    return out


def pickup():
    t = _t(0.35)
    out = np.zeros_like(t)
    for i, f in enumerate((880, 1175, 1568)):
        start = int(i * 0.07 * RATE)
        tt = t[: len(t) - start]
        out[start:] += np.sign(np.sin(2 * np.pi * f * tt)) * 0.18 * _env(tt, 0.002, 0.08)
    return out


def special(rng):
    t = _t(0.6)
    freq = 200 + 900 * t
    tone = np.sin(2 * np.pi * np.cumsum(freq) / RATE) * _env(t, 0.01, 0.3) * 0.4
    return tone + whoosh(rng, 0.6) * 0.8


def go_beep():
    t = _t(0.5)
    out = np.zeros_like(t)
    for i in range(2):
        s = int(i * 0.22 * RATE)
        tt = t[: int(0.15 * RATE)]
        out[s:s + len(tt)] += np.sign(np.sin(2 * np.pi * 988 * tt)) * 0.2 * _env(tt, 0.002, 0.1)
    return out


def ko_voice(rng):
    """Kurzer 'Uargh'-Schrei aus Formant-Rauschen."""
    t = _t(0.45)
    f = 180 * np.exp(-t * 1.5)
    src = np.sign(np.sin(2 * np.pi * np.cumsum(f) / RATE)) * 0.5
    out = _lowpass(src, 9) * _env(t, 0.02, 0.25)
    return out * 0.9


def music_loop():
    """16 Takte Synthwave-Beat in a-Moll, 120 BPM (32 s)."""
    bpm = 120
    beat = 60.0 / bpm
    bars = 16
    total = bars * 4 * beat
    n = int(total * RATE)
    out = np.zeros(n)
    rng = np.random.default_rng(7)

    def add(sig, at):
        s = int(at * RATE)
        e = min(n, s + len(sig))
        out[s:e] += sig[: e - s]

    kick_t = _t(0.3)
    kick = np.sin(2 * np.pi * np.cumsum(55 + 120 * np.exp(-kick_t * 30)) / RATE) * _env(kick_t, 0.001, 0.12)
    snare_t = _t(0.25)
    snare = _lowpass(rng.uniform(-1, 1, len(snare_t)), 2) * _env(snare_t, 0.001, 0.07) * 0.5
    hat_t = _t(0.06)
    hat = rng.uniform(-1, 1, len(hat_t)) * _env(hat_t, 0.001, 0.015) * 0.18
    # Akkordfolge: Am - F - C - G (Grundtoene)
    roots = [110.0, 87.31, 130.81, 98.0]
    for bar in range(bars):
        root = roots[(bar // 2) % 4]
        for b in range(4):
            tb = (bar * 4 + b) * beat
            add(kick, tb)
            if b in (1, 3):
                add(snare, tb)
            for h in range(2):
                add(hat, tb + h * beat / 2)
            # Bass: Achtel
            for e in range(2):
                bt = _t(beat / 2 * 0.9)
                f = root * (2 if (e == 1 and b % 2 == 1) else 1)
                saw = 2 * ((bt * f) % 1.0) - 1
                add(_lowpass(saw, 12) * _env(bt, 0.005, 0.15) * 0.35, tb + e * beat / 2)
        # Lead-Melodie auf der zweiten Haelfte
        if bar >= 8:
            scale = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0]
            for s16 in range(0, 16, 2):
                if rng.random() < 0.55:
                    f = scale[rng.integers(0, len(scale))]
                    lt = _t(beat / 2)
                    sq = np.sign(np.sin(2 * np.pi * f * lt)) * _env(lt, 0.005, 0.12) * 0.09
                    add(sq, (bar * 4) * beat + s16 * beat / 4)
        # Pad
        pt = _t(4 * beat)
        pad = sum(np.sin(2 * np.pi * root * m * pt) for m in (2, 2.5, 3)) * 0.035
        pad *= np.minimum(1, pt / 0.3) * np.minimum(1, (4 * beat - pt) / 0.3)
        add(pad, bar * 4 * beat)
    return out * 0.8


def generate(out_dir):
    rng = np.random.default_rng(1)
    sounds = {
        "SFX_HitLight": hit(False, rng),
        "SFX_HitHeavy": hit(True, rng),
        "SFX_Whoosh": whoosh(rng),
        "SFX_Thud": thud(rng),
        "SFX_Break": crash(rng),
        "SFX_Pickup": pickup(),
        "SFX_Special": special(rng),
        "SFX_Go": go_beep(),
        "SFX_KO": ko_voice(rng),
        "MUS_Stage1": music_loop(),
    }
    paths = []
    for name, data in sounds.items():
        p = os.path.join(out_dir, name + ".wav")
        _write(p, data)
        paths.append((name, p))
    return paths
