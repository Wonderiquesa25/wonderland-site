# Animacao "boneco de papel" da imagem do podcast: maxilar segue a voz, piscar de olhos,
# cabeca a balancar. Coordenadas na imagem original 1200x896 (x2 na base de trabalho).
import cv2, numpy as np

K = 2  # escala da base de trabalho

def P(pts): return (np.array(pts, np.float32) * K).astype(np.int32)

LIP = [(612, 342), (630, 342), (650, 344), (668, 342), (681, 340)]  # linha entre os labios
JAW = [(608, 341), (630, 341), (650, 343), (668, 341), (682, 339), (690, 352), (692, 382), (680, 412),
       (656, 434), (626, 442), (600, 434), (588, 406), (590, 372), (598, 352)]
HEAD = [(430, 70), (700, 60), (712, 200), (700, 330), (700, 430), (650, 470), (600, 480), (520, 470),
        (450, 380), (420, 250)]
PIVOT = (560, 470)
EYES = [((598, 250), (21, 9)), ((677, 253), (9, 7))]

class Puppet:
    def __init__(self, img):
        self.base = cv2.resize(img, None, fx=K, fy=K, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
        H, W = self.base.shape[:2]
        jm = np.zeros((H, W), np.float32); cv2.fillPoly(jm, [P(JAW)], 1.0)
        self.jw = cv2.GaussianBlur(jm, (0, 0), 4 * K)
        # dentro da boca o maxilar move-se por inteiro (sem esbater junto aos labios)
        core = np.zeros((H, W), np.float32); cv2.fillPoly(core, [P(JAW[:5] + [(676, 360), (620, 362)])], 1.0)
        self.jw = np.maximum(self.jw, cv2.GaussianBlur(core, (0, 0), 1.5 * K))
        x0, y0, x1, y1 = 560 * K, 300 * K, 720 * K, 470 * K
        self.box = (x0, y0, x1, y1)
        lx = np.array([p[0] for p in LIP], np.float32) * K; ly = np.array([p[1] for p in LIP], np.float32) * K
        # abertura em forma de lente: maxima ao centro, quase fechada nos cantos
        xs = np.arange(x0, x1) / K
        u = np.clip((xs - 610) / (684 - 610), 0, 1)
        self.prof = (0.22 + 0.78 * np.sin(np.pi * u) ** 0.8).astype(np.float32)
        self.lipy = np.interp(np.arange(x0, x1), lx, ly, left=-1e9, right=-1e9)
        hm = np.zeros((H, W), np.float32); cv2.fillPoly(hm, [P(HEAD)], 1.0)
        self.hw = cv2.GaussianBlur(hm, (0, 0), 10 * K)[..., None]
        self.lid = [self.base[int((c[1] - r[1] - 6) * K), int(c[0] * K)].copy() for c, r in EYES]

    def frame(self, jaw, blink, ang, dx=0.0, dy=0.0):
        jaw, blink, ang, dx, dy = float(jaw), float(blink), float(ang), float(dx), float(dy)
        img = self.base.copy()
        x0, y0, x1, y1 = self.box
        # --- maxilar ---
        if jaw > 0.05:
            d = float(jaw) * K
            sub = img[y0:y1, x0:x1]
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            dyf = self.jw[y0:y1, x0:x1] * d * self.prof[None, :]
            warped = cv2.remap(self.base, xx, yy - dyf, cv2.INTER_LINEAR)
            lip = self.lipy[None, :]
            inside = (yy >= lip) & (yy - dyf < lip)
            # interior da boca: escuro, dentes em cima, lingua em baixo
            depth = (yy - lip) / np.maximum(dyf, 1e-3)
            mouth = np.zeros_like(warped)
            mouth[:] = (24, 18, 40)  # BGR
            mouth[(depth < 0.30) & (xx > 628 * K) & (xx < 674 * K)] = (200, 212, 222)
            mouth[(depth > 0.72)] = (64, 58, 128)
            mk = cv2.GaussianBlur(inside.astype(np.float32), (0, 0), 0.8)[..., None]
            warped = warped * (1 - mk) + mouth * mk
            sub[:] = warped
        # --- piscar ---
        if blink > 0.02:
            for (c, r), col in zip(EYES, self.lid):
                cx, cy = c[0] * K, c[1] * K; rx, ry = r[0] * K, r[1] * K
                top = cy - ry * 1.15; bot = top + 2.3 * ry * blink
                m = np.zeros(img.shape[:2], np.float32)
                cv2.ellipse(m, (int(cx), int(cy)), (int(rx * 1.15), int(ry * 1.35)), 0, 0, 360, 1.0, -1)
                m[:int(top)] = 0; m[int(bot):] = 0
                m = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
                img = img * (1 - m) + col * m
                yb = int(bot)
                cv2.ellipse(img, (int(cx), yb - 2), (int(rx), 3), 0, 0, 180, (40, 28, 26), 2)
        # --- cabeca (rotacao a volta do pescoco) ---
        if abs(ang) > 0.02 or abs(dx) > 0.05 or abs(dy) > 0.05:
            M = cv2.getRotationMatrix2D((PIVOT[0] * K, PIVOT[1] * K), ang, 1.0)
            M[0, 2] += dx * K; M[1, 2] += dy * K
            rot = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            img = img * (1 - self.hw) + rot * self.hw
        return img
