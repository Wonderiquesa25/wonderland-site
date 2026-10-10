"""Cena 1 v3 render: EDL (silences tightened) -> RVM matte -> studio grade (576) -> crop/punch + upscale (1080x1920)
-> CodeFormer face restoration with temporal smoothing -> encode. One process per part (run 2 in parallel)."""
import sys, os, json, subprocess, time, numpy as np, cv2
C = sys.argv[1]; sys.path.insert(0, C)
from look2 import Matte, Face, grade
from facefix import StableRestorer
SW, SH, W, H, FPS = 576, 1024, 1080, 1920, 30
PUNCH = 1.08


def render(part, seg_index0):
    edl = [e for e in json.load(open(f"{C}/edl.json")) if e["part"] == part]
    keep = {}
    for k, e in enumerate(edl):
        for f in range(e["f0"], e["f1"]): keep[f] = k
    mt = Matte(); fc = Face(SW, SH); rs = StableRestorer("codeformer", threads=2); rs.reset()
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{C}/work/{part}_stab.mp4", "-vf", "hqdn3d=1.5:1.2:4:4",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                            "-vf", "unsharp=5:5:0.25:5:5:0,noise=alls=2:allf=t", "-c:v", "libx264", "-crf", "14", "-preset", "medium",
                            "-pix_fmt", "yuv420p", f"{C}/out/v3_{part}.mp4"], stdin=subprocess.PIPE)
    FS = SW * SH * 3; i = 0; cur_seg = -1; rect = None; first = True; lm_s = None; written = 0
    while True:
        buf = dec.stdout.read(FS)
        if len(buf) < FS: break
        fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
        if first:
            for _ in range(8): mt(fr)
            first = False
        fg, pha = mt(fr)
        if i in keep:
            box = fc(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            _, det = fc.d.detect(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            if det is not None and len(det):
                lm = det[np.argmax(det[:, 2] * det[:, 3])][4:14].reshape(5, 2).astype(np.float32)
                lm_s = lm if lm_s is None else 0.6 * lm + 0.4 * lm_s
            g = grade(fg, pha, box, 1.0)
            k = keep[i]
            if k != cur_seg:                                   # new segment: alternate framing to hide the jump cut
                cur_seg = k; rs.reset()
                z = PUNCH if (seg_index0 + k) % 2 else 1.0
                w, h = SW / z, SH / z
                cx = (box[0] + box[2] / 2) if box is not None else SW / 2
                cy = (box[1] + box[3] * 0.55) if box is not None else SH * 0.4
                x0 = float(np.clip(cx - w / 2, 0, SW - w)); y0 = float(np.clip(cy - h * 0.40, 0, SH - h))
                rect = (x0, y0, w, h)
            x0, y0, w, h = rect; s = W / w
            M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
            big = cv2.warpAffine(g, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
            if lm_s is not None and box is not None:
                big = rs(big, (lm_s - [x0, y0]) * s, weight=0.7, fidelity=0.7, infer=(written % 2 == 0))
            enc.stdin.write(big.tobytes()); written += 1
            if written % 150 == 0: print(part, written, flush=True)
            if written >= int(os.environ.get('MAXF', 10**9)): break
        i += 1
    enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.kill(); dec.wait(); print(part, "done", written, flush=True)


if __name__ == "__main__":
    edl = json.load(open(f"{C}/edl.json"))
    idx0 = {}
    for k, e in enumerate(edl): idx0.setdefault(e["part"], k)
    for part in sys.argv[2:]:
        render(part, idx0[part])
