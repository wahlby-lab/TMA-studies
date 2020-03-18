import os
from numbers import Number
import numpy as np
from skimage import io, morphology, img_as_float, exposure
from skimage import filters as sf
from skimage.exposure import adjust_gamma
from scipy.odr import Model, Data, ODR
from scipy.stats import linregress

def costesColoc(img1,img2,exclude_zero_zero=True):
    #find all the points to find approx the line
    if(len(img1.shape) > 2 or  len(img2.shape) > 2):
        print("images have to be 2D one channel")
        return None
    
    width=min(img1.shape[1],img2.shape[1])
    height=min(img1.shape[0],img2.shape[0])

    img1=img1[:,:width]
    img2=img2[:,:width]

    img1=img1[:height,:]
    img2=img2[:height,:]

    #zerosat=(img1==0)*(img2==0)
    findat=None
    if(exclude_zero_zero):
        findat=True-(img1==0)*(img2==0)
    else:
        findat=np.ones_like(img1,dtype="bool")

    regmex=img1[findat]
    regmey=img2[findat]

    params=orthoregress(regmex,regmey)



def orthoregress(x, y):
    """Perform an Orthogonal Distance Regression on the given data,
    using the same interface as the standard scipy.stats.linregress function.
    Arguments:
    x: x data
    y: y data
    Returns:
    [m, c, nan, nan, nan]
    Uses standard ordinary least squares to estimate the starting parameters
    then uses the scipy.odr interface to the ODRPACK Fortran code to do the
    orthogonal distance calculations.
    """
    linreg = linregress(x, y)
    mod = Model(f)
    dat = Data(x, y)
    od = ODR(dat, mod, beta0=linreg[0:2])
    out = od.run()

    return list(out.beta) + [np.nan, np.nan, np.nan]


def f(p, x):
    """Basic linear regression 'model' for use with ODR"""
    return (p[0] * x) + p[1]



class TMAQuantifier:

    proteins=["CD44v6", "Ecad"]
    mainprotein=0 #meaning first of array
    secoprotein=1 #secondary protein
    # I am not sure yet how to code this for more proteins

    stains=["H","DAB","mask","Tumor","ilH","ilDAB","RGB"]
    morphology=0 #morphology shown by H
    expression=1 #protein expression by DAB
    mask=2
    tumor=3
    ilh=4
    ildab=5
    RGB=6

    imagelocations={} #locations of images per stain search by stain names

    block=""
    corename=""

    usetumor=False #tumor segmentation of ilastik
    usemask=False #use mask coming from tissuemaps
    usecellapprox=False #use cells  coming from H from ilastik
    usedabapprox=False #use DAB from Ilastik

    def __init__(self,proteins=None, stains=None):
        if((proteins != None) and (stains != None)):
            for protein in self.proteins:
                for stain in self.stains:
                    self.imagelocations[(protein, stain)]=""
        
    def checkExistance(self,check=None,message=""):
        dobreak=False
        for imfile in self.imagelocations:
            filex=self.imagelocations[imfile]
            if(not os.path.isfile(filex)):
                message+="\n file for"+str(imfile)+" does not exist ("
                message+=filex+")"
                dobreak=True
        if(dobreak):
            print(message)
                
        return dobreak

    def getStainFromProtein(self, protein,stain,gamma=False,clip=False,load_as_float=False,as_bool=False,value_at=False):

        if(isinstance(protein, Number)):
            num=protein
            protein=self.proteins[num]
        if(isinstance(stain, Number)):
            num=stain
            stain=self.stains[num]
        img=None
        if(not os.path.exists(self.imagelocations[(protein, stain)])):
            print("Image for "+(protein, stain)+" does not exist at "+
                self.imagelocations[(protein, stain)])
            return None

        
        
        if(load_as_float):
            img=img_as_float(
                io.imread(self.imagelocations[(protein, stain)]) )
        else:
            img=io.imread(self.imagelocations[(protein, stain)])

        if(value_at):
            if(isinstance(value_at, Number)):
                img[img!=value_at]=0
                img=img.astype("bool")
            else:
                print("value_at is not numerical ("+str(value_at)+type(value_at)+")")
                return None

        if(clip):
            if(type(clip) is tuple):
                img=np.clip(img,clip[0],clip[1])
            elif(isinstance(clip, Number)):
                maxr=255
                if(load_as_float):
                    maxr=1.0
                img=np.clip(img,clip,maxr)

        if(gamma):
            if(isinstance(gamma, Number)):
                img=adjust_gamma(img,gamma)

        if(as_bool):
            img=img.astype("bool")

        return img

    #stain 0 morphology
    def RCM(self,gamma=False,clip=False,load_as_float=False,as_bool=False,value_at=False):
        
        p0=self.getStainFromProtein(self.mainprotein,self.morphology,
            gamma=gamma,clip=clip,load_as_float=load_as_float)
        p1=self.getStainFromProtein(self.secoprotein,self.morphology,
            gamma=gamma,clip=clip,load_as_float=load_as_float)
        
        p0thr=sf.threshold_triangle(p0)
        p1thr=sf.threshold_triangle(p1)

        regConfMap=np.zeros_like(p0)
        regConfMap[p0[:,:]>p0thr]+=2
        regConfMap[p1[:,:]>p1thr]+=1
        regConfMap[regConfMap<3]*=0
        regConfMap=regConfMap.astype("bool")

        regConfMap=morphology.binary_dilation(regConfMap)
        regConfMap=morphology.binary_erosion(regConfMap)

        return regConfMap

    #based on stain expression dab (1) one can try (5) dabmembrane
    def CQM(self,gamma=False,clip=False,load_as_float=False,as_bool=False,value_at=False):

        p0=self.getStainFromProtein(self.mainprotein,self.expression,
            gamma=gamma,clip=clip,load_as_float=load_as_float)
        p1=self.getStainFromProtein(self.secoprotein,self.expression,
            gamma=gamma,clip=clip,load_as_float=load_as_float)

        p0thr=sf.threshold_triangle(p0)
        p1thr=sf.threshold_triangle(p1)

        colocQuantMapR=np.zeros_like(p0,dtype="float")
        colocQuantMapG=np.zeros_like(p0,dtype="float")
        colocQuantMapB=np.zeros_like(p0,dtype="float")

        colocQuantMapR[p0[:,:]>p0thr]+=1.0
        colocQuantMapG[p1[:,:]>p1thr]+=1.0

        colocQuantMapR=np.stack((colocQuantMapR,colocQuantMapG,colocQuantMapB),axis=-1)

        return colocQuantMapR


    def coreH(self,protein,gamma=False,clip=False,load_as_float=False,as_bool=False,value_at=False):
        if(isinstance(protein, Number)):
            num=protein
            protein=self.proteins[num]
        H=self.getStainFromProtein(protein,self.morphology,
            gamma=gamma,clip=clip,load_as_float=load_as_float)

        Hthr=sf.threshold_triangle(H)

        H[H[:,:]<Hthr]=0

        if(as_bool):
            H=H.astype("bool")

        return H

    def coreDAB(self,protein,gamma=False,clip=False,load_as_float=False,as_bool=False,value_at=False):
        if(isinstance(protein, Number)):
            num=protein
            protein=self.proteins[num]
        DAB=self.getStainFromProtein(protein,self.expression,
            gamma=gamma,clip=clip,load_as_float=load_as_float)

        DABthr=sf.threshold_triangle(DAB)

        DAB[DAB[:,:]<DABthr]=0

        if(as_bool):
            DAB=DAB.astype("bool")

        return DAB
