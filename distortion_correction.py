import os
import numpy as np
import cv2 as cv

video_file = 'data/chessboard.avi'

K = np.array([
    [877.7296387720864, 0, 962.0783500253059],
    [0, 882.3978300005379, 534.7815410521965],
    [0, 0, 1]
], dtype=np.float32)

dist_coeff = np.array(
    [-0.01550393, 0.05839123, -0.00129875, 0.00045911, -0.04683481],
    dtype=np.float32
)

os.makedirs('images', exist_ok=True)

video = cv.VideoCapture(video_file)
assert video.isOpened(), "영상 못 읽음"

map1, map2 = None, None

while True:
    valid, img = video.read()
    if not valid:
        break

    original = img.copy()

    if map1 is None:
        map1, map2 = cv.initUndistortRectifyMap(
            K, dist_coeff, None, None,
            (img.shape[1], img.shape[0]),
            cv.CV_32FC1
        )

    rectified = cv.remap(original, map1, map2, interpolation=cv.INTER_LINEAR)

    combined = np.hstack((original, rectified))

    cv.putText(combined, "Original", (10, 30),
               cv.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0))
    cv.putText(combined, "Rectified", (img.shape[1] + 10, 30),
               cv.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0))

    cv.imshow("Distortion Correction", combined)

    key = cv.waitKey(10)
    if key == ord(' '):
        while True:
            cv.imshow("Distortion Correction", combined)
            key2 = cv.waitKey(0)

            if key2 == ord('s') or key2 == ord('S'):
                ok1 = cv.imwrite('images/original_capture.png', original)
                ok2 = cv.imwrite('images/rectified_capture.png', rectified)
                print(f"saved original: {ok1}")
                print(f"saved rectified: {ok2}")
                print("saved to images/original_capture.png")
                print("saved to images/rectified_capture.png")

            elif key2 == ord(' '):
                break

            elif key2 == 27:
                video.release()
                cv.destroyAllWindows()
                exit()

    elif key == 27:
        break

video.release()
cv.destroyAllWindows()