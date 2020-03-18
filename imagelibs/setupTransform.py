# Import Numpy/Scipy
import numpy as np
from skimage import io

# Import transforms
from pyalphaamd.transforms import CompositeTransform
from pyalphaamd.transforms import AffineTransform
from pyalphaamd.transforms import Rigid2DTransform
from pyalphaamd.transforms import Rotate2DTransform
from pyalphaamd.transforms import TranslationTransform
from pyalphaamd.transforms import ScalingTransform
from pyalphaamd.transforms import util

# Import optimizers
from pyalphaamd.optimizers import GradientDescentOptimizer

# Import generators and filters
import pyalphaamd.generators as generators
import pyalphaamd.filters.filt as filters

# Import registration framework
from pyalphaamd.register import Register as Register

# Import misc
import math
import sys
import time
import os

class setupTransform:

    def __init__(self,refname,floname,plevels,sigmas):
        # Registration Parameters
        self.alpha_levels = 7
        # Pixel-size
        self.spacing = np.array([1.0, 1.0])
        # Run the symmetric version of the registration framework
        self.symmetric_measure = True
        # Use the squared Euclidean distance
        self.squared_measure = False

        # The number of iterations
        self.param_iterations = 100
        # The fraction of the points to sample randomly (0.0-1.0)
        self.param_sampling_fraction = 0.3
        # Number of iterations between each printed output (with current distance/gradient/parameters)
        self.param_report_freq = 50

        self.plevels=plevels
        self.sigmas=sigmas

        self.refname=refname
        self.floname=floname

    def doRegistration(self):
        ref_im = io.imread(self.refname, as_grey=True)
        flo_im_orig = io.imread(self.floname, as_grey=True) 
        ref_im = filters.normalize(ref_im, 0.0, None)
        flo_im = filters.normalize(flo_im_orig, 0.0, None)
    
        diag = 0.5 * (util.image_diagonal(ref_im, self.spacing) + util.image_diagonal(flo_im, self.spacing))

        weights1 = np.ones(ref_im.shape)
        mask1 = np.ones(ref_im.shape, 'bool')
        weights2 = np.ones(flo_im.shape)
        mask2 = np.ones(flo_im.shape, 'bool')

        # Initialize registration framework for 2d images
        reg = Register(2)

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
        reg.add_initial_transform(AffineTransform(2), np.array([1.0/diag, 1.0/diag, 1.0/diag, 1.0/diag, 1.0, 1.0]))
    
        # Set the parameters
        reg.set_iterations(self.param_iterations)
        reg.set_gradient_magnitude_threshold(0.001)
        reg.set_sampling_fraction(self.param_sampling_fraction)
        reg.set_step_lengths(step_lengths)

        # Start the registration
        reg.run()

        (transform, value) = reg.get_output(0)

        print('Transformation parameters: %s.' % str(transform.get_params()))

        return transform

    def applyTnSave(self,T,refname,filename,savename):

        ref_im=io.imread(refname)
        ref_space = np.zeros(ref_im.shape)
        ref_im=None
        flo_im = io.imread(filename, as_grey=True)

        ### Warp image
        c = util.make_image_centered_transform(T, ref_space, flo_im, self.spacing, self.spacing)
        # Transform the floating image into the reference image space by applying transformation 'c'
        c.warp(In = flo_im, Out = ref_space, in_spacing=self.spacing, out_spacing=self.spacing, mode='spline', bg_value = 0.0)

        # Save the registered image
        io.imsave(savename, ref_space)
        