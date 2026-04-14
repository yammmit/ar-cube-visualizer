import cv2 as cv
import numpy as np
from PIL import Image, ImageSequence

def warp_sprite_to_quad(background, sprite_bgra, quad):
    """
    background: BGR
    sprite_bgra: BGRA
    quad: (4,2) float32, 순서 = 좌하, 우하, 우상, 좌상
    """
    h, w = sprite_bgra.shape[:2]

    src = np.array([
        [0, h - 1],      # 좌하
        [w - 1, h - 1],  # 우하
        [w - 1, 0],      # 우상
        [0, 0]           # 좌상
    ], dtype=np.float32)

    dst = quad.astype(np.float32)

    H = cv.getPerspectiveTransform(src, dst)
    warped = cv.warpPerspective(
        sprite_bgra,
        H,
        (background.shape[1], background.shape[0]),
        flags=cv.INTER_LINEAR,
        borderMode=cv.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0)
    )

    alpha = warped[:, :, 3:4] / 255.0
    fg = warped[:, :, :3].astype(np.float32)
    bg = background.astype(np.float32)

    out = alpha * fg + (1 - alpha) * bg
    return out.astype(np.uint8)


if __name__ == '__main__':
    with np.load('calibration.npz') as X:
        K = X['K']
        dist_coeff = X['dist_coeff']

    gif = Image.open('miku_transparent.gif')
    gif_frames = [
        cv.cvtColor(np.array(frame.convert('RGBA')), cv.COLOR_RGBA2BGRA)
        for frame in ImageSequence.Iterator(gif)
    ]
    gif_idx = 0

    board_pattern = (10, 7)
    board_cellsize = 0.025

    obj_pts = np.array(
        [[c, r, 0] for r in range(board_pattern[1]) for c in range(board_pattern[0])],
        dtype=np.float32
    ) * board_cellsize

    video = cv.VideoCapture('data/chessboard.avi')
    assert video.isOpened(), "영상 못 읽음"

    print("[INFO] Press ESC to quit")

    while True:
        valid, img = video.read()
        if not valid:
            break

        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        complete, corners = cv.findChessboardCorners(gray, board_pattern)

        if complete:
            criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

            success, rvec, tvec = cv.solvePnP(obj_pts, corners2, K, dist_coeff)

            if success:
                sprite = gif_frames[gif_idx]
                gif_idx = (gif_idx + 1) % len(gif_frames)

                # =========================
                # 미쿠 판넬의 3D 크기/위치
                # =========================
                # (x, y)는 체스보드 평면 위 위치
                x0 = 0.11
                y0 = 0.08

                # 실제 판넬 폭, 높이 (미터 단위 비슷한 의미)
                width = 0.045
                height = 0.12

                # 세워진 직사각형 평면의 4점
                # 순서: 좌하, 우하, 우상, 좌상
                quad_3d = np.array([
                    [x0 - width / 2, y0, 0.0],
                    [x0 + width / 2, y0, 0.0],
                    [x0 + width / 2, y0, -height],
                    [x0 - width / 2, y0, -height],
                ], dtype=np.float32)

                quad_2d, _ = cv.projectPoints(quad_3d, rvec, tvec, K, dist_coeff)
                quad_2d = quad_2d.reshape(-1, 2)

                img = warp_sprite_to_quad(img, sprite, quad_2d)

                # 확인용 꼭짓점 점
                for p in quad_2d.astype(int):
                    cv.circle(img, tuple(p), 4, (0, 0, 255), -1)

        cv.imshow('Standing Miku Panel AR', img)

        key = cv.waitKey(30)
        if key == 27:
            break

    video.release()
    cv.destroyAllWindows()