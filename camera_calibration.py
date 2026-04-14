import numpy as np
import cv2 as cv

def select_img_from_video(video_file, board_pattern, select_all=False, wait_msec=10, wnd_name='Camera Calibration'):
    video = cv.VideoCapture(video_file)
    assert video.isOpened(), "영상 못 읽음"

    img_select = []
    while True:
        valid, img = video.read()
        if not valid:
            break

        display = img.copy()
        cv.putText(display, f'NSelect: {len(img_select)}', (10, 25),
                   cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0))
        cv.imshow(wnd_name, display)

        key = cv.waitKey(wait_msec)

        if key == ord(' '):  # Space
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            complete, pts = cv.findChessboardCorners(gray, board_pattern)

            if complete:
                cv.drawChessboardCorners(display, board_pattern, pts, complete)
                cv.imshow(wnd_name, display)
                key = cv.waitKey()

                if key == ord('\r'):  # Enter
                    img_select.append(img)
                    print(f"[INFO] Selected {len(img_select)} images")
            else:
                print("[WARN] 코너 검출 실패")

        if key == 27:  # ESC
            break

    cv.destroyAllWindows()
    return img_select


def calib_camera_from_chessboard(images, board_pattern, board_cellsize):
    img_points = []

    for img in images:
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        complete, pts = cv.findChessboardCorners(gray, board_pattern)
        if complete:
            img_points.append(pts)

    assert len(img_points) > 0, "선택된 이미지 없음"

    obj_pts = [[c, r, 0] for r in range(board_pattern[1]) for c in range(board_pattern[0])]
    obj_points = [np.array(obj_pts, dtype=np.float32) * board_cellsize] * len(img_points)

    return cv.calibrateCamera(obj_points, img_points, gray.shape[::-1], None, None)


if __name__ == '__main__':
    video_file = 'data/chessboard.avi'
    board_pattern = (10, 7)
    board_cellsize = 0.025

    img_select = select_img_from_video(video_file, board_pattern)

    rms, K, dist_coeff, rvecs, tvecs = calib_camera_from_chessboard(
        img_select, board_pattern, board_cellsize)
    np.savez('calibration.npz', K=K, dist_coeff=dist_coeff)
    print('[INFO] saved calibration.npz')

    print('\n## Camera Calibration Results')
    print(f'* Number of images = {len(img_select)}')
    print(f'* RMS error = {rms}')
    print(f'* fx = {K[0,0]}')
    print(f'* fy = {K[1,1]}')
    print(f'* cx = {K[0,2]}')
    print(f'* cy = {K[1,2]}')
    print(f'* K = \n{K}')
    print(f'* Distortion = {dist_coeff.flatten()}')