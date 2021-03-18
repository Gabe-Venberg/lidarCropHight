#! /usr/bin/env python3
#command line arguments:
#   -x, -y, width and hight of the output image
#   --output, -o, name of output file. if there are multiple input files, there will be a number prepended to this.
#   after all comamnd line arguments, file or files(space seperated) to process.

import os.path
import numpy as np
import sys, argparse, laspy, logging
import seaborn as sns; sns.set_theme()
import matplotlib.pyplot as plt

logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
#logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.DEBUG)

def parse_arguments():
    parser = argparse.ArgumentParser(description='create a top down hightmap from a LIDAR point file.')
    parser.add_argument('file', help='.las file to process.')
    parser.add_argument('-x', default=100, type=int, help='horizontal size (in cells) of the output image. Defaults to 100')
    parser.add_argument('-y', default=100, type=int, help='vertical size (in cells) if the output image. Defaults to 100')
    parser.add_argument('-o', '--output', help='name of output file. will default to [name of input file].png if not given.')
    args=parser.parse_args()

    imgX=args.x
    imgY=args.y

    inFile=args.file

    if args.output==None:
        outFile = f'{os.path.dirname(inFile)}/{os.path.basename(inFile)}.png'
    else:
        outFile=args.output
    
    print(f'outputing to {outFile}')

def scale(array, desiredmaxX, desiredmaxY):
    logging.debug(f'xMax is {np.max(array[:,xDim])} and xMin is {np.min(array[:,xDim])}')
    logging.debug(f'yMax is {np.max(array[:,yDim])} and yMin is {np.min(array[:,yDim])}')
    ax=desiredmaxX/(np.max(array[:,xDim])-np.min(array[:,xDim]))
    bx=-ax*np.min(array[:,xDim])
    ay=desiredmaxY/(np.max(array[:,yDim])-np.min(array[:,yDim]))
    by=-ay*np.min(array[:,yDim])


    #slice indexes 0-2 from the second dimention
    array[:,xDim]=ax*array[:,xDim]+bx
    array[:,yDim]=ay*array[:,yDim]+by

    logging.debug(f'array is\n{array}')
    logging.debug(f'xMax is {np.max(array[:,xDim])} and xMin is {np.min(array[:,xDim])}')
    logging.debug(f'yMax is {np.max(array[:,yDim])} and yMin is {np.min(array[:,yDim])}')

    return array

#TODO: make it iterate over multiple files.
parse_arguments()

#import each dimention scaled.
lasFile=laspy.file.File(inFile, mode = 'r')
z = lasFile.z
x = lasFile.x
y = lasFile.y
intensity = lasFile.intensity

points = np.stack((z,x,y), axis=-1)

#dimention that will be z(top down) dimention in final heatmap. TODO: auto detect this based on dimention with least variance, while being overridable on the command line.
zDim=1
xDim=2
yDim=0

#points should now look like
#[[z,x,y]
# [z,x,y]
# ...
# [z,x,y]
# [z,x,y]]

logging.debug(f'points is\n{points}')
length=points.shape[0]
print(f'{length} points in LIDAR file.')

imageArray = np.zeros((imgX, imgY))

points = scale(points, imgX, imgY)

#sys.exit()
#for each entry in points, figure out what pixel it will go into, and assign that pixel the zval, unless the zval already in that pixel is higher.
for i in range(len(points)):
    print(f'{i} points processed of {length} total points')
    #the if statements are reqired for edge cases relateing to the bottom row and the far right column, to make sure points dont get left out.
    xPixel=np.floor(points[i,xDim]).astype(int)
    if xPixel==imgX:
        xPixel-=1
    yPixel=np.floor(points[i,yDim]).astype(int)
    if yPixel==imgY:
        yPixel-=1
    imageArray[xPixel,yPixel]=np.maximum(imageArray[xPixel,yPixel], points[i,zDim])

logging.debug(f'imageArray is {imageArray}')

print('processed all points. generating heatmap.')
heatMap = sns.heatmap(imageArray, center=(np.max(imageArray)+np.min(imageArray))/2, robust=True, square=True)
heatMapFig = heatMap.get_figure()
heatMapFig.savefig(outFile)
