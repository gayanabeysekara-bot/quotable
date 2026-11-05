"""YOLOX object detector via ONNX Runtime (CPU by default).

Model: YOLOX (Megvii), Apache-2.0 licence, COCO-80 classes, official ONNX release
weights (https://github.com/Megvii-BaseDetection/YOLOX/releases/tag/0.1.1rc0).
Used here for PERSON detection (COCO class 0). See docs/LICENSING.md.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import cv2
import numpy as np

from .base import Detection, DetectorInfo

COCO_CLASSES = (
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant",
    "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
    "teddy bear", "hair drier", "toothbrush",
)

# Known official release files. sha256 verified at load time when the name matches.
KNOWN_MODELS = {
    "yolox_nano.onnx": ("c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d", 416),
    "yolox_tiny.onnx": ("427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7", 416),
    "yolox_s.onnx": ("c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063", 640),
}


class ModelIntegrityError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _letterbox(img: np.ndarray, size: int) -> tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    r = min(size / h, size / w)
    resized = cv2.resize(img, (int(w * r), int(h * r)), interpolation=cv2.INTER_LINEAR)
    padded = np.full((size, size, 3), 114, dtype=np.uint8)
    padded[: resized.shape[0], : resized.shape[1]] = resized
    return padded, r


def _decode(outputs: np.ndarray, size: int) -> np.ndarray:
    grids, strides = [], []
    for stride in (8, 16, 32):
        hs = ws = size // stride
        xv, yv = np.meshgrid(np.arange(ws), np.arange(hs))
        grid = np.stack((xv, yv), 2).reshape(1, -1, 2)
        grids.append(grid)
        strides.append(np.full((*grid.shape[:2], 1), stride))
    grids = np.concatenate(grids, 1)
    strides = np.concatenate(strides, 1)
    outputs = outputs.copy()
    outputs[..., :2] = (outputs[..., :2] + grids) * strides
    outputs[..., 2:4] = np.exp(outputs[..., 2:4]) * strides
    return outputs


class YoloxOnnxDetector:
    def __init__(
        self,
        model_path: str | os.PathLike,
        conf_threshold: float = 0.35,
        nms_threshold: float = 0.45,
        classes: tuple[str, ...] = ("person",),
        verify_checksum: bool = True,
        num_threads: int | None = None,
        class_names: tuple[str, ...] = COCO_CLASSES,
    ) -> None:
        import onnxruntime as ort

        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"Model file not found: {path}. Run scripts/download_models.sh (see README)."
            )
        known = KNOWN_MODELS.get(path.name)
        if known and verify_checksum:
            digest = sha256_file(path)
            if digest != known[0]:
                raise ModelIntegrityError(f"sha256 mismatch for {path.name}: {digest}")
        opts = ort.SessionOptions()
        if num_threads:
            opts.intra_op_num_threads = num_threads
        self.session = ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])
        inp = self.session.get_inputs()[0]
        self.input_name = inp.name
        self.input_size = int(inp.shape[2]) if isinstance(inp.shape[2], int) else (known[1] if known else 416)
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.class_names = tuple(class_names)
        self.class_ids = [self.class_names.index(c) for c in classes]
        stem = path.stem
        self.info = DetectorInfo(
            name=stem,
            version=f"{stem}@0.1.1rc0",
            task="person",
            status="production-candidate (not independently validated)",
            licence="Apache-2.0 (YOLOX, Megvii); trained on COCO 2017",
            notes="Generic COCO detector used for the 'person' class only.",
        )

    def raw_detect(self, frame_bgr: np.ndarray, conf_threshold: float | None = None) -> list[tuple[int, float, tuple]]:
        """Return (class_id, score, normalised bbox) for configured classes."""
        thr = self.conf_threshold if conf_threshold is None else conf_threshold
        h, w = frame_bgr.shape[:2]
        img, ratio = _letterbox(frame_bgr, self.input_size)
        blob = img.transpose(2, 0, 1)[None].astype(np.float32)
        out = self.session.run(None, {self.input_name: blob})[0]
        preds = _decode(out, self.input_size)[0]
        boxes = preds[:, :4]
        scores_all = preds[:, 4:5] * preds[:, 5:]
        results: list[tuple[int, float, tuple]] = []
        for cid in self.class_ids:
            scores = scores_all[:, cid]
            keep = scores > thr
            if not np.any(keep):
                continue
            b = boxes[keep]
            s = scores[keep]
            xyxy = np.empty_like(b)
            xyxy[:, 0] = (b[:, 0] - b[:, 2] / 2) / ratio
            xyxy[:, 1] = (b[:, 1] - b[:, 3] / 2) / ratio
            xyxy[:, 2] = (b[:, 0] + b[:, 2] / 2) / ratio
            xyxy[:, 3] = (b[:, 1] + b[:, 3] / 2) / ratio
            rects = [[float(x1), float(y1), float(x2 - x1), float(y2 - y1)] for x1, y1, x2, y2 in xyxy]
            idx = cv2.dnn.NMSBoxes(rects, s.astype(float).tolist(), thr, self.nms_threshold)
            for i in np.array(idx).flatten().tolist():
                x1, y1, x2, y2 = xyxy[i]
                nb = (
                    float(np.clip(x1 / w, 0, 1)),
                    float(np.clip(y1 / h, 0, 1)),
                    float(np.clip(x2 / w, 0, 1)),
                    float(np.clip(y2 / h, 0, 1)),
                )
                if nb[2] - nb[0] <= 0 or nb[3] - nb[1] <= 0:
                    continue
                results.append((cid, float(s[i]), nb))
        return results

    def detect(self, frame_bgr: np.ndarray) -> list[Detection]:
        return [
            Detection(label=COCO_CLASSES[cid], confidence=score, bbox=bbox, category="person")
            for cid, score, bbox in self.raw_detect(frame_bgr)
            if cid == 0
        ]
