'''
Module for Canny edge detection
Requirements: 1.scipy.(numpy is also mandatory, but it is assumed to be
                      installed with scipy)
              2. Python Image Library(only for viewing the final image.)
Author: Vishwanath
contact: vishwa.hyd@gmail.com
Editor: Andrew Powers
'''
try:
    from PIL import Image
except ImportError:
    print 'PIL not found. You cannot view the image'
import os
import numpy
import scipy
from scipy import *
from scipy.ndimage import *
from scipy.signal import convolve2d as conv
 
class Canny:
    '''
        Create instances of this class to apply the Canny edge
        detection algorithm to an image.
 
        input: imagename(string),sigma for gaussian blur
        optional args: thresHigh,thresLow
 
        output: numpy ndarray.
 
        P.S: use canny.grad to access the image array        
 
        Note:
        1. Large images take a lot of time to process, Not yet optimised
        2. thresHigh sets the lower limit for strong edges.
        3. thresLow sets the lower image for weak edges, which when connected
           strong edge pixels, become strong edges.
 
        usage example:
        >>>canny = Canny('image.jpg',1.4,50,10)
        >>>im = canny.grad
        >>>Image.fromarray(im).show()
    '''
    def __init__(self,imname,thresHigh,thresLow,angle,length,latitude,zoom):
        r_earth = 6378100
        m_scale = abs(156543.04 * math.cos(latitude) / math.pow(2,zoom))
        #g_res = (math.cos(latitude*math.pi/180)*2*math.pi*r_earth)/(256*math.pow(2,zoom)) #ground resolution
        #m_scale = (g_res*72)
        print m_scale
        
        sigma = 1.4
        self.angle = angle
        self.length = length/m_scale
        self.imin = imread(imname,flatten = True)
 
        # Create the gauss kernel for blurring the input image
        # It will be convolved with the image
        gausskernel = self.gaussFilter(sigma,5)
        # fx is the filter for vertical gradient
        # fy is the filter for horizontal gradient
        # Please not the vertical direction is positive X
         
        fx = self.createFilter([1, 1, 1,
                                0, 0, 0,
                               -1,-1,-1])
        fy = self.createFilter([-1,0,1,
                                -1,0,1,
                                -1,0,1])
 
        imout = conv(self.imin,gausskernel)[1:-1,1:-1]
        gradx = conv(imout,fx)[1:-1,1:-1]
        grady = conv(imout,fy)[1:-1,1:-1]
 
        # Net gradient is the square root of sum of square of the horizontal
        # and vertical gradients
 
        grad = hypot(gradx,grady)
        grad *= 255.0/numpy.max(grad)
        theta = arctan2(grady,gradx)
        theta = 180 + (180/pi)*theta
        # Only significant magnitudes are considered. All others are removed
        x,y = where(grad < thresLow)
        theta[x,y] = 0
        grad[x,y] = 0
 
        # The angles are quantized. This is the first step in non-maximum
        # supression. Since, any pixel will have only 4 approach directions.
        x0,y0 = where(((theta<22.5)+(theta>157.5)*(theta<202.5)
                       +(theta>337.5)) == True)
        x45,y45 = where( ((theta>22.5)*(theta<67.5)
                          +(theta>202.5)*(theta<247.5)) == True)
        x90,y90 = where( ((theta>67.5)*(theta<112.5)
                          +(theta>247.5)*(theta<292.5)) == True)
        x135,y135 = where( ((theta>112.5)*(theta<157.5)
                            +(theta>292.5)*(theta<337.5)) == True)
 
        self.theta = theta
        #Image.fromarray(self.theta).convert('L').save('Angle map.jpg')
        self.theta[x0,y0] = 0
        self.theta[x45,y45] = 45
        self.theta[x90,y90] = 90
        self.theta[x135,y135] = 135
        x,y = self.theta.shape        
        temp = Image.new('RGB',(y,x),(255,255,255))
        for i in range(x):
            for j in range(y):
                if self.theta[i,j] == 0:
                    temp.putpixel((j,i),(0,0,255))
                elif self.theta[i,j] == 45:
                    temp.putpixel((j,i),(255,0,0))
                elif self.theta[i,j] == 90:
                    temp.putpixel((j,i),(255,255,0))
                elif self.theta[i,j] == 45:
                    temp.putpixel((j,i),(0,255,0))
        self.grad = grad.copy()[1:-1,1:-1]
        x,y = self.grad.shape
 
        for i in range(x):
            for j in range(y):
                if self.theta[i,j] == 0:
                    test = self.nms_check(grad,i,j,1,0,-1,0)
                    if not test:
                        self.grad[i,j] = 0
 
                elif self.theta[i,j] == 45:
                    test = self.nms_check(grad,i,j,1,-1,-1,1)
                    if not test:
                        self.grad[i,j] = 0
 
                elif self.theta[i,j] == 90:
                    test = self.nms_check(grad,i,j,0,1,0,-1)
                    if not test:
                        self.grad[i,j] = 0
                elif self.theta[i,j] == 135:
                    test = self.nms_check(grad,i,j,1,1,-1,-1)
                    if not test:
                        self.grad[i,j] = 0
        self.theta = theta            
        init_point = self.stop(self.grad, thresHigh)
        # Hysteresis tracking. Since we know that significant edges are
        # continuous contours, we will exploit the same.
        # thresHigh is used to track the starting point of edges and
        # thresLow is used to track the whole edge till end of the edge.

        while (init_point != -1):
            #Image.fromarray(self.grad).show()
            #print 'next segment at',init_point
            edge = [init_point]
            avg = [self.theta[init_point[0],init_point[1]]]
            self.grad[init_point[0],init_point[1]] = -1
            #p2 = init_point
            #p1 = init_point
            p0 = init_point
            p0 = self.nextNbd(self.grad,p0,thresLow,edge,avg), edge, avg
            count = 0
            
             
            #while (p0 != -1):
            for p0 in edge:
                count += 1
                #print p0
                #p2 = p1
                #p1 = p0
                self.grad[p0[0],p0[1]] = -1
                p0 = self.nextNbd(self.grad,p0,thresLow,edge,avg),edge, avg
                 
            if len(edge) >= self.length and numpy.std(avg)<self.angle:
                #print len(edge)
                pass
            else:
                for i in edge:
                    count +=1
                    self.grad[i[0],i[1]] = 0
                    
            init_point = self.stop(self.grad,thresHigh)

 
        # Finally, convert the image into a binary image
        x,y = where(self.grad == -1)
        self.grad[:,:] = 0
        self.grad[x,y] = 255
 
    def createFilter(self,rawfilter):
        '''
            This method is used to create an NxN matrix to be used as a filter,
            given a N*N list
        '''
        order = pow(len(rawfilter),0.5)
        order = int(order)
        filt_array = array(rawfilter)
        outfilter = filt_array.reshape((order,order))
        return outfilter
     
    def gaussFilter(self,sigma,window = 3):
        '''
            This method is used to create a gaussian kernel to be used
            for the blurring purpose. inputs are sigma and the window size
        '''
        kernel = zeros((window,window))
        c0 = window // 2
 
        for x in range(window):
            for y in range(window):
                r = hypot((x-c0),(y-c0))
                val = (1.0/2*pi*sigma*sigma)*exp(-(r*r)/(2*sigma*sigma))
                kernel[x,y] = val
        return kernel / kernel.sum()
 
    def nms_check(self,grad,i,j,x1,y1,x2,y2):
        '''
            Method for non maximum supression check. A gradient point is an
            edge only if the gradient magnitude and the slope agree
 
            for example, consider a horizontal edge. if the angle of gradient
            is 0 degress, it is an edge point only if the value of gradient
            at that point is greater than its top and bottom neighbours.
        '''
        try:
            if (grad[i,j] > grad[i+x1,j+y1]) and (grad[i,j] > grad[i+x2,j+y2]):
                return 1
            else:
                return 0
        except IndexError:
            return -1
     
    def stop(self,im,thres):
        '''
            This method is used to find the starting point of an edge.
        '''
        X,Y = where(im > thres)
        try:
            y = Y.min()
        except:
            return -1
        X = X.tolist()
        Y = Y.tolist()
        index = Y.index(y)
        x = X[index]
        return [x,y]
   
    def nextNbd(self,im,p0,thres,edge,avg):
        '''
            This method is used to return the next point on the edge.
        '''
        kit = [-1,0,1]
        X,Y = im.shape
        for i in kit:
            for j in kit:
                if i==0 and j==0:
                   continue
                x = p0[0]+i
                y = p0[1]+j
                 
                if (x<0) or (y<0) or (x>=X) or (y>=Y):
                    continue
##                if ([x,y] == p1) or ([x,y] == p2):
##                    continue
                if (im[x,y] > thres):
                    if [x,y] not in edge:
                        return [x,y], edge.append([x,y]), avg.append(self.theta[x,y])
        return -1
# End of module Canny
