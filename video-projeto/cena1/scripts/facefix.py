"""Face restoration (GFPGAN 1.4 / CodeFormer ONNX) on an aligned 512 crop, pasted back with a feathered mask.
Blended with the original so identity, proportions and expression stay the person's own."""
import numpy as np, cv2, onnxruntime as ort

M = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad/models"
FFHQ = np.array([[0.37691676, 0.46864664], [0.62285697, 0.46912813], [0.50123859, 0.61331904],
                 [0.39308822, 0.72541100], [0.61150205, 0.72490465]], np.float32) * 512


class Restorer:
    def __init__(self, model="gfpgan_1.4", threads=4):
        o = ort.SessionOptions(); o.intra_op_num_threads = threads
        self.s = ort.InferenceSession(f"{M}/{model}.onnx", o, providers=["CPUExecutionProvider"])
        self.inputs = [i.name for i in self.s.get_inputs()]
        self.model = model
        m = np.zeros((512, 512), np.float32)
        cv2.rectangle(m, (40, 30), (472, 492), 1, -1)
        self.feather = cv2.GaussianBlur(m, (0, 0), 22)

    def __call__(self, rgb, lm5, weight=0.65, fidelity=0.7):
        """rgb: full frame uint8, lm5: 5x2 landmarks in that frame. Returns the frame with the restored face blended in."""
        A, _ = cv2.estimateAffinePartial2D(lm5.astype(np.float32), FFHQ, method=cv2.LMEDS)
        crop = cv2.warpAffine(rgb, A, (512, 512), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        x = (crop.astype(np.float32) / 255 - 0.5) / 0.5
        feed = {self.inputs[0]: x.transpose(2, 0, 1)[None]}
        if len(self.inputs) > 1: feed[self.inputs[1]] = np.array([fidelity], np.float64)
        y = self.s.run(None, feed)[0][0].transpose(1, 2, 0)
        y = ((np.clip(y, -1, 1) + 1) / 2 * 255).astype(np.float32)
        # keep the person's own colour/tone: transfer crop's low-frequency colour onto the restored detail
        y = y - cv2.GaussianBlur(y, (0, 0), 6) + cv2.GaussianBlur(crop.astype(np.float32), (0, 0), 6)
        Ai = cv2.invertAffineTransform(A)
        h, w = rgb.shape[:2]
        back = cv2.warpAffine(y, Ai, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
        mask = cv2.warpAffine(self.feather, Ai, (w, h))[..., None] * weight
        return np.clip(rgb * (1 - mask) + back * mask, 0, 255).astype(np.uint8)


class StableRestorer(Restorer):
    """Per-frame restoration with temporal smoothing of the restored detail in aligned face space (no shimmer)."""
    def reset(self):
        self.prev_r = None; self.prev_lm = None

    def __call__(self, rgb, lm5, weight=0.7, fidelity=0.7, infer=True):
        if getattr(self, "prev_lm", None) is not None and np.abs(lm5 - self.prev_lm).mean() < 6:
            lm5 = 0.5 * lm5 + 0.5 * self.prev_lm             # steady alignment -> no wobble
        self.prev_lm = lm5.copy()
        A, _ = cv2.estimateAffinePartial2D(lm5.astype(np.float32), FFHQ, method=cv2.LMEDS)
        crop = cv2.warpAffine(rgb, A, (512, 512), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        if infer or getattr(self, "prev_r", None) is None:
            x = (crop / 255 - 0.5) / 0.5
            feed = {self.inputs[0]: x.transpose(2, 0, 1)[None]}
            if len(self.inputs) > 1: feed[self.inputs[1]] = np.array([fidelity], np.float64)
            y = self.s.run(None, feed)[0][0].transpose(1, 2, 0)
            y = (np.clip(y, -1, 1) + 1) / 2 * 255
            r = (y - cv2.GaussianBlur(y, (0, 0), 6)) - (crop - cv2.GaussianBlur(crop, (0, 0), 6))   # detail the model adds
            if getattr(self, "prev_r", None) is not None:
                r = 0.6 * r + 0.4 * self.prev_r
            self.prev_r = r
        else:
            r = self.prev_r                                     # in-between frame: reuse aligned, smoothed detail
        Ai = cv2.invertAffineTransform(A); h, w = rgb.shape[:2]
        back = cv2.warpAffine(r, Ai, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
        mask = cv2.warpAffine(self.feather, Ai, (w, h))[..., None] * weight
        return np.clip(rgb + back * mask, 0, 255).astype(np.uint8)
