import numpy as np


def white_unbalance(x, y):
    # Adjust white balance.
    min_channel_high_end = 0.25
    max_channel_low_end = 0.25
    rmin = random.random()*min_channel_high_end
    gmin = random.random()*min_channel_high_end
    bmin = random.random()*min_channel_high_end
    rmax = random.random()*max_channel_low_end + 1 - max_channel_low_end
    gmax = random.random()*max_channel_low_end + 1 - max_channel_low_end
    bmax = random.random()*max_channel_low_end + 1 - max_channel_low_end
    new_image = np.empty((source.height, source.width, 3), dtype=np.float32)
    image = np.multiply(np.array(source), 1/255.)

    # Make exposure ocasionally brighter
    image = np.clip(np.multiply(image, random.random()*0.3+1.0), 0.0, 1.0)

    new_image[:, :, 0] = np.add(np.multiply(image[:, :, 0], (rmax-rmin)), rmin)
    new_image[:, :, 1] = np.add(np.multiply(image[:, :, 1], (gmax-gmin)), gmin)
    new_image[:, :, 2] = np.add(np.multiply(image[:, :, 2], (bmax-bmin)), bmin)
    new_image = np.multiply(new_image, 255)
    image = Image.fromarray(np.uint8(new_image))
    return image


