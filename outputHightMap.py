#! /usr/bin/env python3
#command line arguments:
#    --help, -h, outputs usage of the program
#    -x, -y, outputs width and hight of the output image
#    --output, -o, name of output file. if there are multiple input files, there will be a number prepended to this.
#    after all comamnd line arguments, file or files(space seperated) to process.

import os.path
import numpy as np
import sys, argparse, laspy, logging
import seaborn as sns; sns.set_theme()
import matplotlib.pyplot as plt
from PIL import Image

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

def sort(array):
    #sort by zDim column, first to last.
    logging.debug(f'zDim sliced points is\n{array[:,zDim]}')
    #the [::-1] reverses the resulting array, so that sortedPoints will be from biggest to smallest.
    ind = np.argsort(array[:,zDim])[::-1]
    sortedPoints = array[ind]
    logging.debug(f'sortedPoints is\n{sortedPoints}')
    return sortedPoints

def scale(array, xRange, yRange, maxX, maxY):
    logging.debug(f'xRange is {xRange} and yRange is {yRange}')
    xScale = maxX/xRange
    yScale = maxY/yRange

    scaledArray = sortedPoints[:, 0:3]
    scaledArray[:,xDim]=scaledArray[:,xDim]-mins[xDim]
    scaledArray[:,xDim]=scaledArray[:,xDim]*xScale
    logging.debug(f'xmin in scaledArray is {scaledArray[:,xDim].min()}')
    logging.debug(f'xmin in scaledArray is {scaledArray[:,xDim].max()}')

    scaledArray[:,yDim]=scaledArray[:,yDim]-mins[yDim]
    scaledArray[:,yDim]=scaledArray[:,yDim]*yScale
    logging.debug(f'ymin in scaledArray is {scaledArray[:,yDim].min()}')
    logging.debug(f'ymin in scaledArray is {scaledArray[:,yDim].max()}')
    logging.debug(f'scaledArray is\n{scaledArray}')
    return scaledArray

def isInxyRange(xMin, xMax, yMin, yMax, xVal, yVal):
    return (xMin<=xVal) and (xVal<xMax) and (yMin<=yVal) and (yVal<yMax)

imgX=1000
imgY=1000

#TODO: make it iterate over multiple files.
inFile = os.path.realpath(sys.argv[1])
lasFile = laspy.file.File(inFile, mode = "r")

outFile = f'{os.path.dirname(inFile)}/{imgX}*{imgY}{os.path.basename(inFile)}.png'

print(f'outputing to {outFile}')

#import each dimention scaled.
x = lasFile.x
y = lasFile.y
z = lasFile.z
maxes = np.array(lasFile.header.max)*np.array(lasFile.header.scale)
mins = np.array(lasFile.header.min)*np.array(lasFile.header.scale)
logging.debug(f'max values is {maxes}')
logging.debug(f'min values is {mins}')
intensity = lasFile.intensity

#dimention that will be z(top down) dimention in final heatmap. TODO: auto detect this based on dimention with least variance.
zDim=0
xDim=1
yDim=2

points = np.stack((x,y,z,intensity), axis=-1)
#points should now look like
#[[x,y,z,intensity]
# [x,y,z,intensity]
# ...
# [x,y,z,intensity]
# [x,y,z,intensity]]

logging.debug(f'points is\n{points}')
print(f'{points.shape[0]} points in LIDAR file.')
#found experimentally.
print(f'estimated worst-case time is {points.shape[0]*7.77e-07*imgX*imgY} sec')

xRange = maxes[xDim]-mins[xDim]
yRange = maxes[yDim]-mins[yDim]
zRange = maxes[zDim]-mins[zDim]

sortedPoints = sort(points)

imageArray = np.zeros((imgX, imgY))

scaledArray = scale(points, xRange, yRange, imgX, imgY)

for x in range(imgX):
    for y in range(imgY):
        if x==imgX:
            xMax=x+2
        else:
            xMax=x+1

        if y==imgY:
            yMax=y+2
        else:
            yMax=y+1

        zVal=0
        logging.debug(f'yMax is {yMax} and xMax is {xMax}')
        for i in range(scaledArray.shape[0]):
            if isInxyRange(x, xMax, y, yMax, scaledArray[i,xDim], scaledArray[i,yDim]):
                zVal = scaledArray[i,zDim]
                break;
        imageArray[x,y]=zVal
        print(f'zVal at {x},{y} is {zVal}')

logging.debug(f'imageArray is {imageArray}')

heatMap = sns.heatmap(imageArray, center=((maxes[zDim]+mins[zDim])/2), square=True)
heatMapFig = heatMap.get_figure()
heatMapFig.savefig(outFile)
