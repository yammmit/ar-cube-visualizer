from PIL import Image, ImageSequence
import numpy as np

INPUT_GIF = "9881.gif"
OUTPUT_GIF = "miku_transparent.gif"

# 배경 판정 민감도
THRESHOLD = 35

def remove_bg_from_frame(frame, threshold=35):
    frame = frame.convert("RGBA")
    arr = np.array(frame)

    # 모서리 평균색을 배경색으로 추정
    corners = np.array([
        arr[0, 0, :3],
        arr[0, -1, :3],
        arr[-1, 0, :3],
        arr[-1, -1, :3],
    ], dtype=np.float32)
    bg = corners.mean(axis=0)

    rgb = arr[:, :, :3].astype(np.float32)

    # 배경색과의 거리 계산
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))

    # 배경으로 판단되면 alpha=0
    alpha = np.where(dist < threshold, 0, 255).astype(np.uint8)

    # 가장자리 톱니 완화용 반투명 구간
    soft = (dist >= threshold) & (dist < threshold + 20)
    alpha[soft] = ((dist[soft] - threshold) / 20.0 * 255).astype(np.uint8)

    arr[:, :, 3] = alpha
    return Image.fromarray(arr, "RGBA")

gif = Image.open(INPUT_GIF)

frames = []
durations = []

for frame in ImageSequence.Iterator(gif):
    out = remove_bg_from_frame(frame, THRESHOLD)
    frames.append(out)
    durations.append(frame.info.get("duration", 40))

frames[0].save(
    OUTPUT_GIF,
    save_all=True,
    append_images=frames[1:],
    duration=durations,
    loop=0,
    disposal=2,
    transparency=0
)

print(f"saved: {OUTPUT_GIF}")