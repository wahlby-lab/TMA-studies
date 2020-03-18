#This file contains some basic processing for tiles that will be used with the 
#goal of using WSI parts.

import numpy as np
from skimage import io
from skimage import img_as_float
from skimage import img_as_ubyte
from scipy.linalg import lstsq

class ColorProjector:
    def __init__(self):
        #this is for HDAB only
        self.absorbanceMatrix=[[ 0.6641974 ,  0.5952016 ,  0.45230175],\
             [ 0.45010985,  0.57665003 , 0.68181806]]
        self.white=None
        
    def estimateAbsorbances(self,s1,s2,s3=None):
        absorbance_array=[]
        def estimate(stainimg):
            eps = 1.0 / 256.0 / 2.0
            flo_image=img_as_float(stainimg)
            log_image = np.log(flo_image + eps)
            data = [- log_image[:, :, i].flatten() for i in range(3)]
            # Order channels by strength
            sums = [np.sum(x) for x in data]
            order = np.lexsort([sums])
            # Calculate relative absorbance against the strongest.
            strongest = data[order[-1]][:, np.newaxis]
            absorbances = [lstsq(strongest, d)[0][0] for d in data]
            # Normalize
            absorbances = np.array(absorbances)
            absorbances = absorbances / np.sqrt(np.sum(absorbances ** 2))
            return absorbances
            
        if(s1 is None):
            s1=self.absorbanceMatrix[0]
            absorbance_array.append(s1)
        else:
            e=estimate(s1)
            absorbance_array.append(e)

        if(s2 is None):
            s2=self.absorbanceMatrix[1]
            absorbance_array.append(s2)
        else:
            e=estimate(s2)
            absorbance_array.append(e)
            
        if(s3 is not None and s1 is not None and s2 is not None):
            e=estimate(s3)
            absorbance_array.append(e)
        
        return absorbance_array
    
    def separateStains(self,ndarray,absorbM=None,stain=0):
        flo_tile=img_as_float(ndarray)
        eps = 1.0 / 256.0 / 2.0
        image = flo_tile[:,:,:3] + eps

        if(absorbM is None):
            absorbM=self.absorbanceMatrix
        #scaled_image=np.zeros_like(ndarray)

        log_image = np.log(image)
        stainMat=np.matrix(absorbM)
        inv_abs_array=[]
        for ia in range(len(absorbM)):
            inv_abs_array.append(np.array(stainMat.I[:,ia]).flatten())
        
        scaled_image = log_image * inv_abs_array[stain][np.newaxis, np.newaxis, :]

        image = np.exp(np.sum(scaled_image, 2))

        image -= eps
        image=np.clip(image,0.0,1.0)
        image = 1 - image

        image8bit=img_as_ubyte(image)
            
        return image8bit

    def nearestWhiteIntensity(self,ndarray,cutoff=0.95):
        #flo_img=img_as_float(ndarray)
        norm=np.linalg.norm(ndarray,axis=2)
        norm= norm.astype(float)
        maximum=np.max(ndarray)
        minimum=np.min(ndarray)
        norm=(norm-minimum)/(maximum-minimum)
        mostwhites=ndarray[np.where(norm > cutoff)]
        
        avg=np.floor(np.average(mostwhites,axis=0))
        self.white=avg
        return avg
        
        
    
    def whiteBalance(self,ndarray,bg=None,cutoff=0.95):
        inbg=None
        if(bg is None):
            if(self.white is None):
                self.white=self.nearestWhiteIntensity(ndarray,cutoff=cutoff)
                
            inbg=self.white
        else:
            inbg=bg    

        flo_img=img_as_float(ndarray)
        channels=1
        if(len(flo_img.shape)>2):
            channels=flo_img.shape[2]
        
        maxintensity=np.iinfo(ndarray.dtype).max
        
        for c in range(channels):
            flo_img[:,:,c]*=maxintensity/inbg[c]
            
        flo_img= np.clip(flo_img, 0, 1)
        flo_img*=255
        ndarray=flo_img.astype(ndarray.dtype)
        return ndarray
        
        
        
        
        
        