import numpy as np
import os
import glob
import sys
import cv2


DIM=(1600, 1200)
K=np.array([[781.3524863867165, 0.0, 794.7118000552183], [0.0, 779.5071163774452, 561.3314451453386], [0.0, 0.0, 1.0]])
D=np.array([[-0.042595202508066574], [0.031307765215775184], [-0.04104704724832258], [0.015343014605793324]])

def undistort(img_path, balance=0.0):

    img = cv2.imread(img_path)
    h,w = img.shape[:2]

    assert w/h == DIM[0]/DIM[1], "Image to undistort needs to have same aspect ratio as the ones used in calibration"

    scaled_K = K * w / DIM[0]
    scaled_K[2][2] = 1 # K[2][2] is always 1
    newmtx = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(scaled_K, D, (w,h), np.eye(3), balance=balance)
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(scaled_K, D, np.eye(3), newmtx, (w,h), cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return undistorted_img


if __name__ == '__main__':
    for p in sys.argv[1:]:
        undistort(p)
