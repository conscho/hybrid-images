import sys
sys.path.append('/Users/kb/bin/opencv-3.1.0/build/lib/')

import cv2
import numpy as np
import math


def cross_correlation_2d(img, kernel):
    '''Given a kernel of arbitrary m x n dimensions, with both m and n being
    odd, compute the cross correlation of the given image with the given
    kernel, such that the output is of the same dimensions as the image and that
    you assume the pixels out of the bounds of the image to be zero. Note that
    you need to apply the kernel to each channel separately, if the given image
    is an RGB image.

    Inputs:
        img:    Either an RGB image (height x width x 3) or a grayscale image
                (height x width) as a numpy array.
        kernel: A 2D numpy array (m x n), with m and n both odd (but may not be
                equal).

    Output:
        Return an image of the same dimensions as the input image (same width,
        height and the number of color channels)
    '''
    if len(img.shape) == 3:
        # RGB
        img = cv2.merge([cross_correlation_2d_1channel(channel, kernel) for channel in cv2.split(img)])
    else:
        # Grayscale
        img = cross_correlation_2d_1channel(img, kernel)
    return img

def cross_correlation_2d_1channel(channel, kernel):
    '''Cross correlation for one image channel, e.g. only grayscale'''
    padding = max(kernel.shape)/2
    channel_padded = np.lib.pad(channel, padding, 'constant')
    channel_corr = np.zeros((channel.shape))
    for i in range(channel.shape[0]): # rows
        for j in range(channel.shape[1]): # columns
            channel_corr[i][j] = np.sum([kernel[m] * channel_padded[i + padding - kernel.shape[0]/2 + m][(j + padding - kernel.shape[1]/2):(j + padding + kernel.shape[1]/2 + 1)]
                                for m in range(kernel.shape[0])])
    return channel_corr

def convolve_2d(img, kernel):
    '''Use cross_correlation_2d() to carry out a 2D convolution.

    Inputs:
        img:    Either an RGB image (height x width x 3) or a grayscale image
                (height x width) as a numpy array.
        kernel: A 2D numpy array (m x n), with m and n both odd (but may not be
                equal).

    Output:
        Return an image of the same dimensions as the input image (same width,
        height and the number of color channels)
    '''
    kernel_trans = np.fliplr(np.flipud(kernel))
    return cross_correlation_2d(img, kernel_trans)

def gaus(sigma,x,y):
    return 1/(2*math.pi*np.power(sigma,2.)) * np.exp(-((np.power(x, 2.) + np.power(y, 2.)) / (2 * np.power(sigma, 2.))))

def gaussian_blur_kernel_2d(sigma, width, height):
    '''Return a Gaussian blur kernel of the given dimensions and with the given
    sigma. Note that width and height are different.

    Input:
        sigma:  The parameter that controls the radius of the Gaussian blur.
                Note that, in our case, it is a circular Gaussian (symmetric
                across height and width).
        width:  The width of the kernel.
        height: The height of the kernel.

    Output:
        Return a kernel of dimensions width x height such that convolving it
        with an image results in a Gaussian-blurred image.
    '''
    kernel = np.zeros((width, height))
    for i in range(width):
        for j in range(height):
            kernel[i][j] = gaus(sigma, np.linalg.norm(i-width/2), np.linalg.norm(j-height/2))
    return kernel/np.sum(kernel)

def low_pass(img, sigma, size):
    '''Filter the image as if its filtered with a low pass filter of the given
    sigma and a square kernel of the given size. A low pass filter supresses
    the higher frequency components (finer details) of the image.

    Output:
        Return an image of the same dimensions as the input image (same width,
        height and the number of color channels)
    '''
    kernel = gaussian_blur_kernel_2d(sigma, size, size)
    return convolve_2d(img, kernel)

def high_pass(img, sigma, size):
    '''Filter the image as if its filtered with a high pass filter of the given
    sigma and a square kernel of the given size. A high pass filter suppresses
    the lower frequency components (coarse details) of the image.

    Output:
        Return an image of the same dimensions as the input image (same width,
        height and the number of color channels)
    '''
    return (img - low_pass(img, sigma, size))

def create_hybrid_image(img1, img2, sigma1, size1, high_low1, sigma2, size2,
        high_low2, mixin_ratio):
    '''This function adds two images to create a hybrid image, based on
    parameters specified by the user.'''
    high_low1 = high_low1.lower()
    high_low2 = high_low2.lower()

    if img1.dtype == np.uint8:
        img1 = img1.astype(np.float32) / 255.0
        img2 = img2.astype(np.float32) / 255.0

    if high_low1 == 'low':
        img1 = low_pass(img1, sigma1, size1)
    else:
        img1 = high_pass(img1, sigma1, size1)

    if high_low2 == 'low':
        img2 = low_pass(img2, sigma2, size2)
    else:
        img2 = high_pass(img2, sigma2, size2)

    img1 *= 2 * (1 - mixin_ratio)
    img2 *= 2 * mixin_ratio
    hybrid_img = (img1 + img2)
    return (hybrid_img * 255).clip(0, 255).astype(np.uint8)
