import os
import numpy as np
from skimage import io

fixedlocation="/location/"
movedlocation="/location/"
savelocation= "/location/"

dirs = os.listdir( fixedlocation )

# This would print all the files and directories
for image in dirs:
    #assuming files end in _H.png
    alist=image.split("_")
    if alist[1] == "H.png":
        print(alist[0])
        #create H+H
        region=alist[0]
        fh=fixedlocation+image
        fimage=io.imread(fh)
        #find the H from the moving protein
        mh=movedlocation+"Ecad"+region+"_H_T.png"
        mimage=io.imread(mh)

        #image should be the shape of the reference
        fshape=fimage.shape
        threechanshape=(fshape[0],fshape[1],3)

        stage=np.zeros(threechanshape,dtype="uint8")

        #make the appropriate channels of the appropriate colors
        #red
        stage[:,:,0]=fimage
        #green
        stage[:,:,1]=mimage

        #save image2
        io.imsave(savelocation+region+".png",stage)
