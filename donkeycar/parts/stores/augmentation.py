import numpy as np
import math
import random
from PIL import Image, ImageDraw
import cv2


def identical(data):
    return data


def reflection(data):
    data['cam/image_array'] = cv2.flip(data['cam/image_array'], 1)
    angle = data['user/angle']
    if angle > 0:
        angle /= -0.775862
        angle = math.max(angle, -1)
    else:
        angle *= -0.775862
    data['user/angle'] = angle

    return data


def brightness(data):
    img_in = data['cam/image_array']
    image1 = cv2.cvtColor(img_in,cv2.COLOR_RGB2HSV)
    image1 = np.array(image1, dtype = np.float64)
    random_bright = .3+np.random.uniform()
    image1[:,:,2] = image1[:,:,2]*random_bright
    image1[:,:,2][image1[:,:,2]>255]  = 255
    image1 = np.array(image1, dtype = np.uint8)
    data['cam/image_array'] = cv2.cvtColor(image1,cv2.COLOR_HSV2RGB)
    return data


def white_unbalance(data):
    img_in = data['cam/image_array']
    # Adjust white balance.
    min_channel_high_end = 0.25
    max_channel_low_end = 0.25
    rmin = random.random()*min_channel_high_end
    gmin = random.random()*min_channel_high_end
    bmin = random.random()*min_channel_high_end
    rmax = random.random()*max_channel_low_end + 1 - max_channel_low_end
    gmax = random.random()*max_channel_low_end + 1 - max_channel_low_end
    bmax = random.random()*max_channel_low_end + 1 - max_channel_low_end
    new_image = np.empty(img_in.shape, dtype=np.float32)
    image = np.multiply(img_in, 1/255.)

    # Make exposure ocasionally brighter
    image = np.clip(np.multiply(image, random.random()*0.3+1.0), 0.0, 1.0)

    new_image[:, :, 0] = np.add(np.multiply(image[:, :, 0], (rmax-rmin)), rmin)
    new_image[:, :, 1] = np.add(np.multiply(image[:, :, 1], (gmax-gmin)), gmin)
    new_image[:, :, 2] = np.add(np.multiply(image[:, :, 2], (bmax-bmin)), bmin)
    data['cam/image_array'] = np.multiply(new_image, 255).astype(np.uint8)
    return data

def random_rects(data):
    img_in = data['cam/image_array']
    # Draw random rectangles over the image so we don't overfit to one feature.
    w = img_in.shape[1]
    h = img_in.shape[0]
    img = Image.fromarray(img_in)
    draw = ImageDraw.Draw(img)
    for i in range(random.randint(0, 32)):
        rs = np.random.rand(4)
        rc = np.random.randn(3) * 0.3
        rc = np.clip(rc, -1.0, 1.0) * 127 + 127
        draw.rectangle([(rs[0]*1.4-0.2)*w, (rs[1]*1.4-0.2)*h, (rs[0]*1.4-0.2)*w + rs[2]*20, (rs[1]*1.4-0.2)*h + rs[3]*20], fill=(int(rc[0]), int(rc[1]), int(rc[2])))
    data['cam/image_array'] = np.asarray(img)
    return data


WEIGHTED_AUGMENTATIONS = [
        (identical, 10),
        (white_unbalance, 20),
        (reflection, 10),
        (random_rects, 20),
        (brightness, 5)
        ]

def augment(data):
    population = [val for val, cnt in WEIGHTED_AUGMENTATIONS for i in range(cnt)]
    aug = random.choice(population)
    out = aug(data)
    #cv2.imwrite("/data/dataset/pics/", out['cam/image_array'])
    return out

def augmented_factor():
    population = [val for val, cnt in WEIGHTED_AUGMENTATIONS for i in range(cnt)]
    return math.ceil( len(population) / WEIGHTED_AUGMENTATIONS[0][1] )  #WEIGHTED_AUGMENTATIONS[0][1] is weight of identical augment
