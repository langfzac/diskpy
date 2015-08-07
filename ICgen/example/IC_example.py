# -*- coding: utf-8 -*-
"""
An example script for generating initial conditions.  This assumes ICgen has
already been properly setup


Created on Wed Sep 17 11:23:32 2014

@author: ibackus
"""
import ICgen
import pynbody
SimArray = pynbody.array.SimArray

if __name__ == "__main__":
    
    # Initialize a blank initial conditions (IC) object:
    IC = ICgen.IC()
    
    # Echo the default settings to get an idea of what parameters can be
    # changed
    IC.settings()
    
    # Set up the surface density profile settings.  Notice that right now the
    # Only setting under 'Sigma profile parameters' is kind: None
    # Lets use a simple powerlaw with cut-offs at the interior and edge of the
    # disk
    IC.settings.sigma.kind = 'powerlaw'
    
    # Other available kinds are 'MQWS' and 'exponential'
    
    # Now echo the sigma settings (defaults)
    IC.settings.sigma()
    
    # The important parameters to set are:
    #   Rd : Disk radius, should be a pynbody SimArray
    #   Qmin : Minimum estimated Toomre Q in the disk
    #   n_points : number of radial points to calculate sigma at
    
    # Lets generate a disk with powerlaw up to 10 au followed by a cutoff
    # And a Q of 1.0
    # To save time, lets do it at low resolution
    IC.settings.sigma.Qmin = 1.0
    IC.settings.sigma.n_points = 100
    IC.settings.sigma.Rd = SimArray(10.0, 'au')
    
    # Lets be careful and save what we've done.  This will save the ICs to
    # IC.p in the current directory
    IC.save()
    
    # Lets change the settings used for numerically calculating the gas density
    # Echo defaults:
    IC.settings.rho_calc()
    # Change the resolution to be lower just to save time
    IC.settings.rho_calc.nr = 100 # Number of radial points to calculate on
    IC.settings.rho_calc.nz = 100 # Number of vertical points to calculate on
    
    # Set the number of particles
    IC.settings.pos_gen.nParticles = 50000
    
    # Set up the temperature profile to use.  Available kinds are 'powerlaw'
    # and 'MQWS'
    # We'll use something of the form T = T0(r/r0)^Tpower
    IC.settings.physical.kind = 'powerlaw'
    IC.settings.physical.Tpower = -0.5  # exponent
    IC.settings.physical.T0 = SimArray(150.0, 'K')  # temperature at r0
    IC.settings.physical.Tmin = SimArray(10.0, 'K') # Minimum temperature
    IC.settings.physical.r0 = SimArray(1.0, 'au')
    
    # Let's set the star mass and gas mass assuming H2
    IC.settings.physical.M = SimArray(1.0, 'Msol') # star mass in solar masses
    IC.settings.physical.m = SimArray(2.0, 'm_p') # mass of H2
    
    # Lets have changa run on the local preset
    IC.settings.changa_run.preset = 'local'
    
    # Save our work to IC.p
    IC.save()
    IC.settings()
    
    # We should be done, all we have to do now is tell the ICs to generate.
    # There are 2 ways to do this, and it may be fairly slow.
    
    # 1) One way is simply to call:
    IC.generate()
    IC.save()
    # This will run through the whole procedure and save a tipsy snapshot
    # to snapshot.std with a basic .param file saved to snapshot.param
    
    ## 2) Otherwise we can go step by step
    #IC.maker.sigma_gen() # Generate surface density profile and CDF
    #IC.maker.rho_gen() # Calculate density according to hydrodynamic equilibrium
    #IC.maker.pos_gen() # Generate particle positions
    #IC.maker.snapshot_gen() # Generate the final tipsy snapshot with velocities etc
    #IC.save()
    #
    ## This will run through the whole procedure and save a tipsy snapshot
    ## to snapshot.std with a basic .param file saved to snapshot.param