# Import Numpy/Scipy
import numpy as np
from skimage import io
from skimage import img_as_float
from skimage import transform as skitransform
from skimage import exposure as skiexposure
from skimage import filters as skifilters

# Import transforms
from pyAlphaAMD.transforms import CompositeTransform
from pyAlphaAMD.transforms import AffineTransform
from pyAlphaAMD.transforms import Rigid2DTransform
from pyAlphaAMD.transforms import Rotate2DTransform
from pyAlphaAMD.transforms import TranslationTransform
from pyAlphaAMD.transforms import ScalingTransform
from pyAlphaAMD.transforms import util

# Import optimizers
from pyAlphaAMD.optimizers import GradientDescentOptimizer

# Import generators and filters
import pyAlphaAMD.generators as generators
#import pyAlphaAMD.filters.filt as filters

from pyAlphaAMD import filters
# Import registration framework
from pyAlphaAMD.register import register

# Import misc
import math
import sys
import time
import os

class setupTransform:

    def __init__(self,refname,floname,plevels,sigmas,templocation,adjust,stretchContrast,blur,screen=None):
        # Registration Parameters
        self.alpha_levels = 7
        # Pixel-size
        self.spacing = np.array([1.0, 1.0])
        # Run the symmetric version of the registration framework
        self.symmetric_measure = False
        # Use the squared Euclidean distance
        self.squared_measure = False

        # The number of iterations
        self.param_iterations = 100
        # The fraction of the points to sample randomly (0.0-1.0)
        self.param_sampling_fraction = 0.4
        # Number of iterations between each printed output (with current distance/gradient/parameters)
        self.param_report_freq = 50

        self.plevels=plevels
        self.sigmas=sigmas

        self.refname=refname
        self.floname=floname
        self.templocation=templocation

        self.adjust=adjust
        self.stretchContrast=stretchContrast
        self.blur=blur
        self.screen=screen

        self.maskRef=None
        self.maskFlo=None

    def doRegistration(self):

        try:
            loadflo=io.imread(self.floname, as_gray=True)
            loadref=io.imread(self.refname, as_gray=True)
        except Exception as inst:
            print (type(inst) )    # the exception instance
            print (inst.args )     # arguments stored in .args
            print (inst)
            return None
    
        ref_im = img_as_float(loadref)
        flo_im_orig = img_as_float(loadflo)

        if self.screen:
            screenimg=io.imread(self.screen, as_gray=True)
            screenimg = img_as_float(screenimg)
            flo_im_orig= 1.0 - (1.0-flo_im_orig)*(1.0-screenimg*0.5)
            print(np.max(flo_im_orig))
            print(np.min(flo_im_orig))
            io.imsave(self.templocation+"flohdabscreened.png",flo_im_orig)


        #stretch
        if self.stretchContrast:
            p1,p99 = np.percentile(ref_im, (1, 99))
            ref_im = skiexposure.rescale_intensity(ref_im, in_range=(p1, p99))
            p1,p99 = np.percentile(flo_im_orig, (1, 99))
            flo_im_orig = skiexposure.rescale_intensity(flo_im_orig, in_range=(p1, p99))

            io.imsave(self.templocation+"ref_99.png",ref_im)
            io.imsave(self.templocation+"flo_99.png",flo_im_orig)

        if self.blur:
            ref_im=skifilters.gaussian(ref_im,sigma=0.05)
            flo_im_orig=skifilters.gaussian(flo_im_orig,sigma=0.05)  
            io.imsave(self.templocation+"ref_blur.png",ref_im)
            io.imsave(self.templocation+"flo_blur.png",flo_im_orig)      

        ref_im = filters.normalize(ref_im, 0.0, None)
        flo_im = filters.normalize(flo_im_orig, 0.0, None)

        perc=1.0

        if(self.adjust):
            arearef=float(ref_im.shape[0]*ref_im.shape[1])
            areaflo=float(flo_im.shape[0]*flo_im.shape[1])

            if areaflo<arearef:
                perc=arearef/areaflo
                perc=perc**0.5
                #if perc<0.85:
                init_t=AffineTransform(2)
                init_t.set_param(0,perc)
                init_t.set_param(3,perc)
                #reg.add_initial_transform(init_t, np.array([1.0/diag, 1.0/diag, 1.0/diag, 1.0/diag, 1.0, 1.0]))
                flo_im = skitransform.rescale(flo_im, 1.0/perc,preserve_range=True)
                #ref_im = skitransform.rescale(ref_im, perc, anti_aliasing=False)

        diag = 0.5 * (util.image_diagonal(ref_im, self.spacing) + util.image_diagonal(flo_im, self.spacing))

        weights1 = np.ones(ref_im.shape)
        weights2 = np.ones(flo_im.shape)

        mask1=None
        mask2=None


        if(self.maskRef and os.path.isfile(self.maskRef)):
            mask1=io.imread(self.maskRef).astype("bool")
        else:
            if(self.maskRef):
                print("maskRef: mask given but file doesnt exist")
            mask1 = np.ones(ref_im.shape, 'bool')

        if(self.maskFlo and os.path.isfile(self.maskFlo)):
            mask2=io.imread(self.maskFlo).astype("bool")
        else:
            if(self.maskFlo):
                print("maskRef: mask given but file doesnt exist")
            mask2 = np.ones(flo_im.shape, 'bool')

        # Initialize registration framework for 2d images
        reg = register.register(2)

        reg.set_report_freq(self.param_report_freq)
        reg.set_alpha_levels(self.alpha_levels)

        reg.set_reference_image(ref_im)
        reg.set_reference_mask(mask1)
        reg.set_reference_weights(weights1)

        reg.set_floating_image(flo_im)
        reg.set_floating_mask(mask2)
        reg.set_floating_weights(weights2)

        #plvels and sigmas must be same length
        for i in range(len(self.plevels)):
            reg.add_pyramid_level(self.plevels[i], self.sigmas[i])

        step_lengths = []
        for i in range(len(self.plevels)-1):
            step_lengths.append([1., 1.])
        step_lengths.append([1., 1e-2])
        step_lengths=np.array(step_lengths)

        # Create the transform and add it to the registration framework (switch between affine/rigid transforms by commenting/uncommenting)
        # Affine

        """if(self.adjust):
            arearef=float(ref_im.shape[0]*ref_im.shape[1])
            areaflo=float(flo_im.shape[0]*flo_im.shape[1])

            if areaflo<arearef:
                perc=arearef/areaflo
                #perc=perc**2
                if perc>1.1:
                    init_t=AffineTransform(2)
                    init_t.set_param(0,perc)
                    init_t.set_param(3,perc)
                    reg.add_initial_transform(init_t, np.array([1.0/diag, 1.0/diag, 1.0/diag, 1.0/diag, 1.0, 1.0]))
    
                    #flo_im = skitransform.resize(flo_im, (flo_im.shape[0] *perc, flo_im.shape[1] *perc))
                    #ref_im = skitransform.rescale(ref_im, perc, anti_aliasing=False)"""
        
        reg.add_initial_transform(AffineTransform(2), np.array([1.0/diag, 1.0/diag, 1.0/diag, 1.0/diag, 1.0, 1.0]))
    
        # Set the parameters
        reg.set_iterations(self.param_iterations)
        reg.set_gradient_magnitude_threshold(0.001)
        reg.set_sampling_fraction(self.param_sampling_fraction)
        reg.set_step_lengths(step_lengths)

        reg.initialize(self.templocation)

        # Start the registration
        reg.run()

        (transform, value) = reg.get_output(0)

        transform.extrascale=perc

        print('Transformation parameters: %s.' % str(transform.get_params()))

        return transform

    def applyTnSave(self,T,refname,filename,savename):

        ref_im=io.imread(refname)
        ref_space = np.zeros(ref_im.shape,"float")
        ref_im=None
        flo_im = io.imread(filename, as_gray=True)

        perc=T.extrascale
        flo_im = skitransform.rescale(flo_im, perc,preserve_range=True)
        
        #T.param[4]=0.0
        #T.param[5]=0.0
        ### Warp image
        c = util.make_image_centered_transform(T, ref_space, flo_im, self.spacing, self.spacing)
        # Transform the floating image into the reference image space by applying transformation 'c'
        c.warp(In = flo_im, Out = ref_space, in_spacing=self.spacing, out_spacing=self.spacing, mode='linear', bg_value = 0.0)

        # Save the registered image
        io.imsave(savename, ref_space.astype("uint8"))
