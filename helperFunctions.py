import numpy as np
import WSILibs.processing as wsip
import WSILibs.wsiregions as wsir
import imagelibs.DZICalculator as DZI
from matplotlib.path import Path
from skimage import io
import os

#some helper functions
def checkFor2DHarray(a,length=3):
    """Check that the array contains 2D Homogenous coordinates"""
    if a.shape[1]==1:
        print("The array doesn't have enough coordinate members,"+a.shape)
    if a.shape[1]==2 or a.shape[1]>3:
        arr=np.zeros((a.shape[0],3),dtype=float)
        arr[:,:2]=a[:,:2]
        arr[:,2]=1.0
        return arr
    elif a.shape[1]==3:
        return a
    
    raise TypeError("point array is not the right dimension")


def colorProjectorGen(loc, protein, stain1, stain2,ftype=".png"):
    cp=wsip.ColorProjector()
    s1loc=loc+protein+stain1+ftype
    s2loc=loc+protein+stain2+ftype
    s1=None; s2=None
    if(not os.path.isfile(s1loc)):
        print("There is no stain palette 1 for "+protein)
    else:
        s1=io.imread(s1loc)

    if(not os.path.isfile(s2loc)):
        print("There is no stain palette 2 for "+protein)
    else:
        s2=io.imread(s2loc)
    cp.absorbanceMatrix=cp.estimateAbsorbances(s1,s2)
    return cp

