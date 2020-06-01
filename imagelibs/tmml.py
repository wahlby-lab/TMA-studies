import skimage
import scipy
from skimage import io,img_as_float,img_as_uint
from skimage.filters import gaussian
from skimage.feature import hessian_matrix, hessian_matrix_eigvals
from skimage.feature import structure_tensor, structure_tensor_eigvals
from sklearn.ensemble import RandomForestClassifier as RFC
import numpy as np
from scipy import ndimage
import pickle

def gaussian_smoothing(img, sigma, multichannel=True):
    gimg=gaussian(img,sigma=sigma,multichannel=multichannel)
    return gimg

#/home/leslie/Documents/TM_notebooks/seeds/squarepatches/seeds/seed80.png
#sigmas=[10.0,5.0,3.5,1.6]
#        0    1   2   3
#        0:3  3:6 6:9 9:

#Difference of gaussian
def DOG(img,s1=None,s2=None):
    g1=None; g2=None
    if(s1 is not None):
        g1=gaussian_smoothing(img,s1)    
    if(s2 is not None):
        g2=gaussian_smoothing(img,s2)
    
    if(g1 is not None):
        if(g2 is not None):
            return g2-g1
        else:
            return img - g1
    else:
        return None
    
#gaussian gradient magnitude    
def ggm(img,sigma):
    if(len(img.shape)==2):
        img=np.expand_dims(img, axis=-1)
        ggmi=ndimage.gaussian_gradient_magnitude(img, sigma=sigma)
        return ggmi
    if(len(img.shape)==3):
        if(img.shape[2]==1):
            ggmi=ndimage.gaussian_gradient_magnitude(img, sigma=sigma)
            return ggmi
        if(img.shape[2]==3):
            ggms=[]
            for i in range(3):
                ggmi=ndimage.gaussian_gradient_magnitude(img[...,i], sigma=sigma)
                ggms.append(ggmi)
            ggmi=np.stack(ggms,axis=-1)
            return ggmi
#structure tensor eigenvalues        
def ste(img,sigma):
    if(len(img.shape)==2):
        img=np.expand_dims(img, axis=-1)
        Axx, Axy, Ayy = structure_tensor(img, sigma=sigma)
        stei=structure_tensor_eigvals(Axx, Axy, Ayy)[0]
        return stei
    if(len(img.shape)==3):
        if(img.shape[2]==1):
            Axx, Axy, Ayy = structure_tensor(img, sigma=sigma)
            stei=structure_tensor_eigvals(Axx, Axy, Ayy)[0]
            return stei
        if(img.shape[2]==3):
            steis=[]
            for i in range(3):
                Axx, Axy, Ayy = structure_tensor(img[...,i], sigma=sigma)
                stei=structure_tensor_eigvals(Axx, Axy, Ayy)[0]
                steis.append(stei)
            stei=np.stack(steis,axis=-1)
            return stei

#Hessian matrix Eigenvalues        
def hme(img,sigma):
    if(len(img.shape)==2):
        img=np.expand_dims(img, axis=-1)
        H_elems = hessian_matrix(img,sigma=sigma,order='rc')
        hme=hessian_matrix_eigvals(H_elems)[0]
        return hme
    if(len(img.shape)==3):
        if(img.shape[2]==1):
            H_elems = hessian_matrix(img,sigma=sigma,order='rc')
            hme=hessian_matrix_eigvals(H_elems)[0]
            return hme
        if(img.shape[2]==3):
            hmeis=[]
            for i in range(3):
                H_elems = hessian_matrix(img[...,i], sigma=sigma,order='rc')
                hmei=hessian_matrix_eigvals(H_elems)[0]
                hmeis.append(hmei)
            hmei=np.stack(hmeis,axis=-1)
            return hmei 
        

def getFeatures(img,s1,s2=None):
    features=gaussian_smoothing(img,s1)
    dogs=DOG(img,s1,s2)
    features=np.concatenate((features,dogs),axis=-1)
    ggms=ggm(img,s1)
    features=np.concatenate((features,ggms),axis=-1)
    stes=ste(img,s1)
    features=np.concatenate((features,stes),axis=-1)
    hmes=hme(img,s1)
    features=np.concatenate((features,hmes),axis=-1)
    return features


