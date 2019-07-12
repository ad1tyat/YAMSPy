'''
This program used SAD filter for filter the not usable data_
The vertical movement is depending on the amount of x-axis vector
Fitler send back
self.dx | self.dy -> Mean of the x-y direction movement
self.dz -> UP (1) Down(-1) Hove(-1)
>> 12 July 2019
'''

import numpy as np
import matplotlib
import math
import time
from matplotlib import pyplot as plt
from scipy import stats

class Filter():
    def __init__(self):
        # @ MIN_DATA is the minimum amount of data captured by optical flow
        self.MIN_NUM_DATA = 20
        # @ the minimum precentage of the up and down vector different
        self.VTL_THRESHOLD = 0.6
        # @ the minimum precentage of the pos and neg vector different
        self.DIFF_THRESHOLD = 0.3
        # @ the minimum number of the usable data
        self.DATA_THRESHOLD = 150
        # @ PIXEL SIZE of Pi camera
        self.PIXEL_SIZE_CM = (16*1.4) / 10000 # 1.4um 4x4 binning
        # @ Focal Length of Pi camera
        self.FOCAL_LENGTH_CM = 0.36 # 3.6mm
        # @ The movement of the frame
        self.dx = self.dy = 0
        # @ The ground truth
        self.gnd_x = self.gnd_y = 0
        # @ The altitude of the frame
        self.altitude = 110 # cm


    def import_data(self, data):
        # /////////////////////////
        # >>> Import Data
        # >>> data.[a:b] a = row, b = columns
        # /////////////////////////
        self.x = np.copy(data['x']) # using 640x480 resolution
        self.y = np.copy(data['y']) # 30 row, 41 columns
        self.sad = np.copy(data['sad']) # Sum of Absolute Difference >> hows the data reliable

    def update(self, j):
        # /////////////////////////
        # >>> Refresh the data, only act when using data base
        # /////////////////////////
        self.x = self.x[j]
        self.y = self.y[j]
        self.sad = self.sad[j]

    def ten_cut_off(self, data):
        # /////////////////////////
        # >>> remove 20% of the data from the begining and the end for remove outlier
        # /////////////////////////
        return data[ int((len(data))*0.1):int((len(data))*(0.9))]

    def sort(self, data): # Rearrange of order of the sample
        # /////////////////////////
        # >>> Sort the data set
        # /////////////////////////
        return np.sort(data)

    def mode(self, data):
        # /////////////////////////
        # >>> Find the most frequenly data
        # /////////////////////////
        return stats.mode(data)[0][0]

    def twoD2oneD(self, data): # This function only work on each frame. In real time, delect all the frame argument
        # /////////////////////////
        # >>> Creating 1D array for x and y instead of 2D
        # /////////////////////////
        return data.ravel()

    def plot(self, j):
        # /////////////////////////
        # >>> Plot the data
        # /////////////////////////
        plt.subplot(311)
        plt.plot(self.dx, '.b', label = 'x')
        plt.legend(loc='lower right')
        plt.title("Frame %d " %(j))
        plt.subplot(312)
        plt.plot(self.dy, '.g', label = 'y')
        plt.legend(loc='lower right')
        plt.subplot(313)
        X = range(41)
        Y = range(30)
        U = -self.x + 0.0001
        V = -self.y + 0.0001
        Q = plt.quiver(X, Y, U, V, pivot='tail', angles='xy',  scale_units='xy', scale=20)
        plt.show()


    def sad_filter (self, k = 1.5): # This function only work on each frame. In real time, delect all the frame argument
        # /////////////////////////
        # >>> Setting SAD Filter # Using the average sad value of each set
        # /////////////////////////
        sad_threshold = np.mean(self.sad) * k # smaller the sad value, the better of data. k is use to reduce the limit
        sad_filter = np.where(self.sad>sad_threshold) # sad_filter is mean the data not reliable
        self.x[sad_filter] = 0                        # therefore, set those data to zero.
        self.y[sad_filter] = 0

    def vtl_filter(self):
        # /////////////////////////
        # >>> Finding the different of abs x and abs y
        # /////////////////////////
        x_1 = len(self.x[np.where(self.x < 0)[0]])
        x0 = len(self.x[np.where(self.x == 0)[0]])
        x1 = len(self.x[np.where(self.x > 0)[0]])
        y_1 = len(self.y[np.where(self.y < 0)[0]])
        y0 = len(self.y[np.where(self.y == 0)[0]])
        y1 = len(self.y[np.where(self.y > 0)[0]])
        px = py = 0
        if x_1 > 0 or x1 > 0 : px = (1-(abs(x_1 - x1)/(x_1+x1)))
        if y_1 > 0 or y1 > 0 : py = (1-(abs(y_1 - y1)/(y_1+y1)))
        if ((px > self.VTL_THRESHOLD) and ((x_1+x1) > self.DATA_THRESHOLD)) or ((py > self.VTL_THRESHOLD) and ((y_1+y1) > self.DATA_THRESHOLD)):
            return False
        else:
            return True

    def zero_filter(self, data):
        # /////////////////////////
        # >>> Filter out too zero vector
        # /////////////////////////
        return (data[(np.where(data!= 0)[0])]) # return nonzero data

    def px2gnd(self):
        # /////////////////////////
        # >>> px displacement to ground displacement
        # >>> GND_DIS = PIXEL_SIZE * PX_DIS * altitude / FOCAL_LENGTH
        # /////////////////////////
        if self.dx == -1 :
            self.gnd_x = 0
        else:
            self.gnd_x = ((self.PIXEL_SIZE_CM * self.dx * self.altitude)/self.FOCAL_LENGTH_CM)
        if self.dy == -1 :
            self.gnd_y = 0
        else:
            self.gnd_y = ((self.PIXEL_SIZE_CM * self.dy * self.altitude)/self.FOCAL_LENGTH_CM)

    def vtl_dir(self):
        # /////////////////////////
        # >>> Dectect the left side of the frame
        # >>> Return -1 = Down , Return 1 = Up
        # /////////////////////////
        self.dx = self.dy = 0
        data = ((self.x[:,:int(((len(self.x[0,:]))/2))]))
        x_1 = len(data[np.where(data < 0)[0]])
        x1 = len(data[np.where(data > 0)[0]])
        data_ = ((self.x[:,int(((len(self.x[0,:]))/2)):]))
        x_1_ = len(data_[np.where(data_ < 0)[0]])
        x1_ = len(data_[np.where(data_ > 0)[0]])
        if ((abs(x_1 - x1)/(x_1 + x1)) > self.DIFF_THRESHOLD and (abs(x_1_ - x1_)/(x_1_ + x1_)) > self.DIFF_THRESHOLD):
            if ((abs(x_1 - x1)/(x_1 + x1)) > (abs(x_1_ - x1_)/(x_1_ + x1_))):
                if (x_1 - x1) < 0 :
                    self.dz = -1
                else:
                    self.dz = 1
            else:
                if (x_1_ - x1_) < 0 :
                    self.dz = 1
                else:
                    self.dz = -1
        else:
            self.dz = 0

    def hrz_dir(self):
        # /////////////////////////
        # >>> Calc the detla x and y
        # /////////////////////////
        # Covert and sort the data to 1D, remove the outlier and take mean
        self.dx = (self.ten_cut_off((self.zero_filter(self.sort(self.twoD2oneD(self.x))))))
        self.dy = (self.ten_cut_off((self.zero_filter(self.sort(self.twoD2oneD(self.y))))))
        self.dz = 0
        if len(self.dx)>self.DATA_THRESHOLD :
            self.dx = self.dx.mean()
        else:
            self.dx = -1
        if len(self.dy)>self.DATA_THRESHOLD :
            self.dy = self.dy.mean()
        else:
            self.dy =-1

    def run(self, data):
        # /////////////////////////
        # >>> Main Flow for filtering
        # /////////////////////////
        self.import_data(data)
        # self.update(j) # Renew the data
        self.sad_filter() # using k = 1.8 gain to lower the SAD limit. Default is 1.5
        if (self.vtl_filter()): # Return True if not vertical movement
            self.hrz_dir()
            self.px2gnd()
        else:
            self.vtl_dir()
        print ("Up(1)/Donw(-1): %3f  |  dx = %3f  |  dy = %3f" % (self.dz, self.dx, self.dy))
        print (self.gnd_x, self.gnd_y)
        # self.plot(j)

# /////////////////////////
# >>> Main
# /////////////////////////
    def main(self, data, j):
        self.run(data)
if __name__ == '__main__':
    for j in range (len(data)):
        Filter().main(data, j)
