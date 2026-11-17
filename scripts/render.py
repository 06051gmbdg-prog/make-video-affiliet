"""Mesin render FFmpeg: foto dan klip menjadi video vertikal 9:16 (1080x1920)."""
import glob
import os
import re
import shutil
import subprocess
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import STYLES, probe  # noqa: E402

W, H = 1080, 1920
FPS = 30
BASE = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]


def find_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    hit = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"], capture_output=True, text=True).stdout
    if hit and os.path.exists(hit):
        return hit
    raise RuntimeError("Font tidak ditemukan. Pasang paket fonts-dejavu-core.")


def sh(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg gagal:\n" + r.stderr[-1800:])


def clean(t):
    t = re.sub(r"[\U00010000-\U0010FFFF]", "", t or "")
    t = re.sub(r"[☀-➿️‍]", "", t)
    return re.sub(r"\s+", " ", t).strip()


class Ctx:
    def __init__(self, work, settings):
        self.work = work
        self.settings = settings
        self.font = find_font()
        self.n = 0
        os.makedirs(work, exist_ok=True)

    def tfile(self, text):
        self.n += 1
        p = os.path.join(self.work, f"t{self.n}.txt")
        with open(p, "w", encoding="utf8") as f:
            f.write(text)
        return p


def dt(ctx, text, size, color, y, box=None, bw=20, x="(w-text_w)/2"):
    p = ctx.tfile(text)
    s = (f"drawtext=fontfile='{ctx.font}':textfile='{p}':expansion=none:fontsize={size}"
         f":fontcolor={color}:x={x}:y={y}")
    if box:
        s += f":box=1:boxcolor={box}:boxborderw={bw}"
    return s


def caption_filters(ctx, text, st):
    size = st["cap_size"]
    chars = max(14, int(900 / (size * 0.62)))
    lines = textwrap.wrap(clean(text), width=chars)[:3] or [" "]
    lh = int(size * 1.5)
    y0 = 1500 - len(lines) * lh
    return [dt(ctx, l, size, st["cap_color"], y0 + k * lh, st["cap_box"], 16) for k, l in enumerate(lines)]


def badge_filters(ctx, price, ai, st):
    y = 120 if st["bars"] else 80
    out = []
    if st["bars"]:
        out += ["drawbox=x=0:y=0:w=1080:h=90:color=black:t=fill",
                "drawbox=x=0:y=1830:w=1080:h=90:color=black:t=fill"]
    if price:
        out.append(dt(ctx, price, 46, "white", y, "0xee4d2d", 20, x="60"))
    if ai:
        out.append(dt(ctx, "AI", 34, "black", y, "white@0.88", 14, x="w-text_w-70"))
    return out


def normalize_photo(src, dst_base):
    """Putar sesuai EXIF, ubah ke RGB, kecilkan. Kembalikan (path, w, h)."""
    try:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        im.thumbnail((2400, 2400))
        dst = dst_base + ".jpg"
        im.save(dst, quality=92)
        return dst, im.size[0], im.size[1]
    except ImportError:
        dst = dst_base + os.path.splitext(src)[1].lower()
        shutil.copy(src, dst)
        i = probe(dst)
        return dst, i["width"], i["height"]


def prepare(ctx, items):
    """items: [{'path','kind'}] -> media dengan ukuran, durasi, dan gambar mini."""
    media = []
    for idx, it in enumerate(items):
        base = os.path.join(ctx.work, f"m{idx}")
        if it["kind"] == "photo":
            p, w, h = normalize_photo(it["path"], base)
            media.append({"kind": "photo", "path": p, "w": w, "h": h, "dur": 0.0, "thumb": p})
        else:
            info = probe(it["path"])
            if not info["width"] or not info["height"]:
                raise RuntimeError("Klip tidak bisa dibaca: " + os.path.basename(it["path"]))
            thumb = base + "_thumb.jpg"
            sh(BASE + ["-ss", "0.2", "-i", it["path"], "-frames:v", "1", "-q:v", "2", thumb])
            media.append({"kind": "clip", "path": it["path"], "w": info["width"], "h": info["height"],
                          "dur": info["duration"] or 4.0, "thumb": thumb})
    return media


def encode_args(out):
    return ["-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-an", out]


def build_scene(ctx, m, i, dur, cap, price, ai, st, out):
    over = caption_filters(ctx, cap, st) + badge_filters(ctx, price, ai, st)
    tail = ",".join(over)
    bg = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          "boxblur=30:3,eq=brightness=-0.25,format=yuv420p")
    if m["kind"] == "photo":
        frames = max(2, int(round(dur * FPS)))
        cw = 1000
        ch = min(1300, int(cw * m["h"] / m["w"]))
        ch = max(400, ch - ch % 2)
        zoom = st["zoom"]
        z = f"1+{zoom}*on/{frames}" if i % 2 == 0 else f"{1 + zoom}-{zoom}*on/{frames}"
        cy = int(760 - ch / 2)
        fg = (f"scale={2 * cw}:{2 * ch}:force_original_aspect_ratio=increase,crop={2 * cw}:{2 * ch},"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={cw}x{ch}:fps={FPS},"
              "format=yuv420p")
        graph = (f"[0:v]{bg}[bg];[1:v]{fg}[fg];[bg][fg]overlay=(W-w)/2:{cy}:shortest=1,{tail}[v]")
        cmd = BASE + ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", m["path"],
                      "-i", m["path"], "-filter_complex", graph, "-map", "[v]", "-t", f"{dur:.3f}"]
    else:
        vertical = abs(m["w"] / m["h"] - 9 / 16) < 0.06
        if vertical:
            graph = ("[0:v]fps=30,setsar=1,scale=1080:1920:force_original_aspect_ratio=increase,"
                     f"crop=1080:1920,format=yuv420p,{tail}[v]")
        else:
            graph = ("[0:v]fps=30,setsar=1,split=2[a][b];"
                     f"[a]{bg}[bg];[b]scale=1080:-2,format=yuv420p[fg];"
                     f"[bg][fg]overlay=0:(H-h)/2-200,{tail}[v]")
        cmd = BASE + ["-t", f"{dur:.3f}", "-i", m["path"], "-filter_complex", graph,
                      "-map", "[v]", "-t", f"{dur:.3f}"]
    sh(cmd + encode_args(out))
    return out


def build_end(ctx, m_last, name, price, cta, ai, st, out, dur=3.0):
    nl = textwrap.wrap(clean(name), width=26)[:3] or [" "]
    f = [("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:3,"
          "eq=brightness=-0.45,format=yuv420p")]
    for k, l in enumerate(nl):
        f.append(dt(ctx, l, 64, "white", 470 + k * 86))
    if price:
        f.append(dt(ctx, price, 104, "white", 900, "0xee4d2d", 40))
    f.append(dt(ctx, cta, 56, "black", 1220, "0xffe600", 36))
    if ai:
        f.append(dt(ctx, "AI", 34, "black", 80, "white@0.88", 14, x="w-text_w-70"))
    graph = "[0:v]" + ",".join(f) + "[v]"
    sh(BASE + ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", m_last["thumb"],
               "-filter_complex", graph, "-map", "[v]", "-t", f"{dur:.3f}"] + encode_args(out))
    return out


def assemble(scene_paths, trans, tdur, music, volume, out, voices=None):
    durs = [probe(p)["duration"] for p in scene_paths]
    n = len(scene_paths)
    cmd = list(BASE)
    for p in scene_paths:
        cmd += ["-i", p]
    voices = [v for v in (voices or []) if v and v[0] and os.path.exists(v[0])]
    if music:
        cmd += ["-stream_loop", "-1", "-i", music]
    vbase = n + (1 if music else 0)
    for v in voices:
        cmd += ["-i", v[0]]
    parts = [f"[{i}:v]fps={FPS},settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[s{i}]" for i in range(n)]
    cur, acc = "[s0]", durs[0]
    for i in range(1, n):
        parts.append(f"{cur}[s{i}]xfade=transition={trans}:duration={tdur}:offset={acc - tdur:.3f}[x{i}]")
        cur = f"[x{i}]"
        acc = acc + durs[i] - tdur
    total = acc
    parts.append(f"{cur}format=yuv420p[v]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[v]"]
    fa = []
    if voices:
        # Narasi: pembuka di awal, penutup selaras kartu akhir. Musik direndahkan di bawah suara.
        end_t, labels = 0.0, []
        for k, (vp, anchor) in enumerate(voices):
            vd = probe(vp)["duration"] or 3.0
            st = 0.3 if anchor == "start" else max(end_t + 0.3, total - vd - 0.4)
            end_t = st + vd
            ms = int(st * 1000)
            fa.append(f"[{vbase + k}:a]aresample=44100,aformat=channel_layouts=stereo,volume=1.4,"
                       f"adelay={ms}|{ms}[v{k}]")
            labels.append(f"[v{k}]")
        fa.append("".join(labels) + f"amix=inputs={len(voices)}:normalize=0:dropout_transition=0,"
                  f"apad,atrim=0:{total:.3f}[vo]")
    if music:
        mv = volume * (0.3 if voices else 1.0)
        fa.append(f"[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
                  f"afade=t=out:st={max(0.0, total - 1.2):.3f}:d=1.2,volume={mv}[mu]")
    if voices and music:
        fa.append("[vo][mu]amix=inputs=2:normalize=0:duration=first[a]")
    elif voices:
        fa.append(f"[vo]afade=t=out:st={max(0.0, total - 0.6):.3f}:d=0.6[a]")
    elif music:
        fa[-1] = fa[-1].replace("[mu]", "[a]")
    if fa:
        cmd[cmd.index("-filter_complex") + 1] += ";" + ";".join(fa)
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "128k"]
    else:
        cmd += ["-an"]
    cmd += ["-t", f"{total:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-maxrate", "8M", "-bufsize", "16M",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    sh(cmd)
    return total


def render_variant(ctx, media, var, prod, music, out, voices=None):
    """media: daftar sudah diprepare dan diputar urutannya. prod: name, price, lines."""
    st = STYLES[var["style"]]
    s = ctx.settings
    ai = bool(s.get("penanda_ai", True))
    lines = [x for x in [var["hook"]] + prod["benefits"] if x] or [prod["name"]]
    scenes, tmp = [], []
    tag = var["label"].replace(" ", "_")
    for i, m in enumerate(media):
        dur = min(float(s["klip_maks"]), max(2.0, m["dur"])) if m["kind"] == "clip" else float(var["per"])
        p = os.path.join(ctx.work, f"{tag}_s{i}.mp4")
        build_scene(ctx, m, i, dur, lines[i % len(lines)], prod["price"], ai, st, p)
        scenes.append(p)
        tmp.append(p)
    endp = os.path.join(ctx.work, f"{tag}_end.mp4")
    build_end(ctx, media[-1], prod["name"], prod["price"], var["cta"], ai, st, endp)
    scenes.append(endp)
    total = assemble(scenes, st["trans"], st["tdur"], music, s.get("musik_volume", 0.6), out, voices)
    for p in scenes:
        try:
            os.remove(p)
        except OSError:
            pass
    return total


def list_media(folder):
    """Isi folder bahan diurutkan nama. Kembalikan [{'path','kind'}]."""
    from common import CLIP_EXT, PHOTO_EXT
    out = []
    for p in sorted(glob.glob(os.path.join(folder, "*"))):
        e = os.path.splitext(p)[1].lower()
        if e in PHOTO_EXT:
            out.append({"path": p, "kind": "photo"})
        elif e in CLIP_EXT:
            out.append({"path": p, "kind": "clip"})
    return out
