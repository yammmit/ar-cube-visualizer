import numpy as np
import cv2 as cv

def draw_pyramid(img, imgpts):
    imgpts = np.int32(imgpts).reshape(-1, 2)

    # 바닥 사각형
    img = cv.drawContours(img, [imgpts[:4]], -1, (0, 255, 0), 2)

    # 꼭짓점까지 선 연결
    for i in range(4):
        img = cv.line(img, tuple(imgpts[i]), tuple(imgpts[4]), (255, 0, 0), 3)

    return img

if __name__ == '__main__':
    # calibration 결과 불러오기
    with np.load('calibration.npz') as X:
        K = X['K']
        dist_coeff = X['dist_coeff']

    # 체스보드 내부 코너 수
    board_pattern = (10, 7)
    board_cellsize = 0.025

    # 체스보드 3D 점 생성
    obj_pts = np.array(
        [[c, r, 0] for r in range(board_pattern[1]) for c in range(board_pattern[0])],
        dtype=np.float32
    ) * board_cellsize

    # AR 물체: 피라미드
    s = board_cellsize * 3
    axis = np.float32([
        [0, 0, 0],
        [s, 0, 0],
        [s, s, 0],
        [0, s, 0],
        [s/2, s/2, -s]
    ])

    video = cv.VideoCapture('data/chessboard.avi')
    assert video.isOpened(), "카메라를 열 수 없음"

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

            # pose estimation
            success, rvec, tvec = cv.solvePnP(obj_pts, corners2, K, dist_coeff)

            if success:
                imgpts, _ = cv.projectPoints(axis, rvec, tvec, K, dist_coeff)
                img = draw_pyramid(img, imgpts)

                cv.drawChessboardCorners(img, board_pattern, corners2, complete)

        cv.imshow('Pose Estimation AR', img)

        key = cv.waitKey(1)
        if key == 27:  # ESC
            break

    video.release()
    cv.destroyAllWindows()