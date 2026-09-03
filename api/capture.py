import hashlib
from pathlib import Path

import cv2

from database import add_sample


CAMERA_DEVICE = "/dev/video0"

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

ROI_X = 592
ROI_Y = 165
ROI_WIDTH = 105
ROI_HEIGHT = 280

IMAGE_DIR = Path(__file__).resolve().parent / "data" / "images"

ALGORITHM = "lava"
ALGORITHM_VERSION = "1.0"


def capture_frame() -> bytes:
    camera = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_V4L2)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

    if not camera.isOpened():
        raise RuntimeError(f"Unable to open camera: {CAMERA_DEVICE}")

    success, frame = camera.read()
    camera.release()

    if not success:
        raise RuntimeError("Unable to capture frame")

    roi = frame[
        ROI_Y:ROI_Y + ROI_HEIGHT,
        ROI_X:ROI_X + ROI_WIDTH,
    ]

    success, encoded = cv2.imencode(".jpg", roi)

    if not success:
        raise RuntimeError("Unable to encode image")

    return encoded.tobytes()


def generate_rng(image: bytes) -> tuple[int, str]:
    digest = hashlib.sha256(image).digest()
    sha256 = digest.hex()

    rng_value = int.from_bytes(
        digest[:4],
        byteorder="big",
        signed=False,
    )

    return rng_value, sha256


def create_sample() -> None:
    image = capture_frame()
    rng_value, sha256 = generate_rng(image)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Temporary filename based on the hash.
    filename = f"{sha256}.jpg"
    image_path = IMAGE_DIR / filename

    image_path.write_bytes(image)

    database_path = f"images/{filename}"

    sample_id = add_sample(
        rng_value=rng_value,
        image_path=database_path,
        algorithm=ALGORITHM,
        algorithm_version=ALGORITHM_VERSION,
    )

    print(f"Sample ID:      {sample_id}")
    print(f"RNG value:      {rng_value}")
    print(f"Image:          {database_path}")
    print(f"SHA-256:        {sha256}")


if __name__ == "__main__":
    create_sample()
