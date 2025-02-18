#-------------------------------------------------------------------------------
# Name:        Spectralsim
# Purpose:     Simulation of standard normal random fields
#
# Author:      Dr.-Ing. S. Hoerning
#
# Created:     02.05.2018, Centre for Natural Gas, EAIT,
#                          The University of Queensland, Brisbane, QLD, Australia
#-------------------------------------------------------------------------------

import numpy as np
import covariancefunction as covfun
import pyfftw

class spectral_random_field(object):
    def __init__(self,
                 domainsize = (100,100),
                 covmod     = '1.0 Exp(2.)',
                 periodic   = False,
                 pyfftwmode = False,
                 seed = None,
                 ):

        self.counter = 0
        self.periodic = periodic
        self.pyfftwmode = pyfftwmode
        self.seed = seed

        # create self.xyz for plotting 3d
        if len(domainsize) == 3:
            self.xyz = np.mgrid[[slice(0,n,1) for n in domainsize]].reshape(3,-1).T
        # adjust domainsize by cutoff for non-perjodic output
        self.cutoff = 0
        if not self.periodic:
            cutoff = covfun.find_maximum_range(covmod)
            cutoffs = []
            for dim in domainsize:
                tsize = dim + cutoff
                # find closest multiple of 8 that is larger than tsize
                m8 = np.int(np.ceil(tsize/8.)*8.)
                cutoffs.append(m8 - dim)

            self.cutoff = np.array(cutoffs)


        self.domainsize = np.array(domainsize)+self.cutoff
        self.covmod     = covmod
        self.ndim       = len(self.domainsize)
        self.npoints    = np.prod(self.domainsize)

        self.grid = np.mgrid[[slice(0,n,1) for n in self.domainsize]]

        # ensure periodicity of domain
        for i in range(self.ndim):
            self.domainsize = self.domainsize[:,np.newaxis]
        self.grid = np.min((self.grid,np.array(self.domainsize)-self.grid),axis=0)

        # compute distances from origin (--> wavenumbers in fourier space)
        self.h = ((self.grid**2).sum(axis=0))**0.5
        # covariances (in fourier space!!!)
        self.Q = covfun.Covariogram(self.h, self.covmod)

        # FFT of covariances
        self.FFTQ = np.abs(np.fft.fftn(self.Q))

        # eigenvalues of decomposition
        self.sqrtFFTQ = np.sqrt(self.FFTQ / self.npoints)

        self.rng = np.random.default_rng(seed=self.seed)

        if self.pyfftwmode:
#             pyfftw.config.NUM_THREADS = 4
            pyfftw.interfaces.cache.enable()
            pyfftw.interfaces.cache.set_keepalive_time(5)

        self.Y = self.simnew()

    def simnew(self):
        """
        Returns two random fields at once. Shape of Y: (2, ysize, xsize).
        """
        
        self.counter += 1
        # compute random field via inverse fourier transform
        real = self.rng.standard_normal(size = self.sqrtFFTQ.shape, dtype=np.float32)
        imag = self.rng.standard_normal(size = self.sqrtFFTQ.shape, dtype=np.float32)
        epsilon = real + 1j*imag
        rand = epsilon * self.sqrtFFTQ
        if self.pyfftwmode:
            Y1 = np.real(pyfftw.interfaces.numpy_fft.ifftn(rand))*self.npoints
            Y2 = np.imag(pyfftw.interfaces.numpy_fft.ifftn(rand))*self.npoints
#             self.Y = np.real(pyfftw.interfaces.numpy_fft.ifftn(rand))*self.npoints
        else:
            Y1 = np.real(np.fft.ifftn(rand))*self.npoints
            Y2 = np.imag(np.fft.ifftn(rand))*self.npoints

        if not self.periodic:
            # readjust domainsize to correct size (--> no boundary effects...)
            gridslice = [slice(0,(self.domainsize.squeeze()-self.cutoff)[i],1)
                                                      for i in range(self.ndim)]
            Y1 = Y1[tuple(gridslice)]
            Y1 = Y1.reshape(self.domainsize.squeeze()-self.cutoff)
            Y2 = Y2[tuple(gridslice)]
            Y2 = Y2.reshape(self.domainsize.squeeze()-self.cutoff)

        self.Y = np.concatenate((Y1[np.newaxis, :],Y2[np.newaxis,:]), axis=0)
        
        return self.Y

    
    def simnew_real(self):
        """
        Returns one random field. Shape of Y: (ysize, xsize).
        """
        self.counter += 1
        # compute random field via inverse fourier transform
        # real = np.random.standard_normal(size=self.sqrtFFTQ.shape)
        # imag = np.random.standard_normal(size=self.sqrtFFTQ.shape)
        real = self.rng.standard_normal(size = self.sqrtFFTQ.shape, dtype=np.float32)
        imag = self.rng.standard_normal(size = self.sqrtFFTQ.shape, dtype=np.float32)
        epsilon = real + 1j*imag
        rand = epsilon * self.sqrtFFTQ
        if self.pyfftwmode:
            self.Y = np.real(pyfftw.interfaces.numpy_fft.ifftn(rand))*self.npoints
        else:
            self.Y = np.real(np.fft.ifftn(rand))*self.npoints

        if not self.periodic:
            # readjust domainsize to correct size (--> no boundary effects...)
            gridslice = [slice(0,(self.domainsize.squeeze()-self.cutoff)[i],1)
                                                      for i in range(self.ndim)]

            self.Y = self.Y[tuple(gridslice)]
            self.Y = self.Y.reshape(self.domainsize.squeeze()-self.cutoff)

        return self.Y





