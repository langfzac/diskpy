# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 23:25:44 2015

@author: ibackus
"""
import numpy as np
import os
import copy
import pynbody
SimArray = pynbody.array.SimArray

from diskpy.utils import configparser, strip_units, get_units

# Constants
G = SimArray(1.0,'G')

# Set up default filenames
_dir = os.path.dirname(os.path.realpath(__file__))
_paramdefault = os.path.join(_dir, 'default.param')
_directordefault = os.path.join(_dir, 'default.director')
_changadefault = os.path.join(_dir, 'changadefaults.param')

# Load the default parameters
_paramdefault = configparser(_paramdefault, 'param')
_directordefault = configparser(_directordefault, 'director')
_changadefault = configparser(_changadefault, 'param')

def getpar(key, param={}):
    """
    Attempts to retrieve the key from param or from the ChaNGa default param 
    options.  Raises ValueError if key not found in either.
    
    Parameters
    ----------
    key : object
    param : str or dict
        Paramname or param dict (see diskpy.utils.configparser).  If not 
        supplied, only the ChaNGa defaults are searched
    
    Returns
    -------
    value 
        The value, taken from param if present, otherwise taken from the ChaNGa
        default params
    """
    if isinstance(param, str):
        
        param = configparser(param, 'param')
        
    if key in param:
        
        value = param[key]
        
    elif key in _changadefault:
        
        value = _changadefault[key]
        
    else:
        
        raise ValueError("Could not find {0} in param or defaults".format(key))
        
    return value
    
def make_director(sigma_min, sigma_max, r, resolution=1200, filename='snapshot'):
    """
    Makes a director dictionary for ChaNGa runs based on the min/max surface
    density, maximum image radius, and image resolution for a gaseous
    protoplanetary disk.  The created dictionary can be saved with
    diskpy.utils.configsave

    The method is to use an example director file (saved as default.director)
    which works for one simulation and scale the various parameters accordingly.
    default.director should have a commented line in it which reads:
        #sigma_max float
    where float is the maximum surface density of the simulation in simulation
    units.

    **ARGUMENTS**

    sigma_min : float
        The surface density that corresponds to 0 density on the image (ie the
        minimum threshold).  Required for setting the dynamic range
    sigma_max : float
        Maximum surface density in the simulation
    r : float
        Maximum radius to plot out to
    resolution : int or float
        Number of pixels in image.  The image is shape (resolution, resolution)
    filename : str
        prefix to use for saving the images.  Example: if filename='snapshot',
        then the outputs will be of form 'snapshot.000000000.ppm'

    **RETURNS**

    director : dict
        A .director dictionary.  Can be saved with diskpy.utils.configsave
    """
    # -----------------------------------------------------------
    # Parse defaults to get scale factor for c
    # -----------------------------------------------------------
    sigma_min, sigma_max, r = strip_units([sigma_min, sigma_max, r])
    defaults = _directordefault
    if '#sigma_max' not in defaults:

        raise KeyError('Default .director file should have a line e.g. << #sigma_max 0.01 >>')

    sigma_max0 = defaults['#sigma_max']
    c0 = defaults['colgas'][3]
    n0 = defaults['size'][0]
    r0 = defaults['eye'][2]
    A = (c0 * float(n0)**2)/(sigma_max0 * r0**2)

    # -----------------------------------------------------------
    # Create new director dictionary
    # -----------------------------------------------------------
    director = copy.deepcopy(defaults)
    director.pop('#sigma_max', None)

    logscale_min = sigma_min/sigma_max

    if pynbody.units.has_units(logscale_min):

        logscale_min = float(logscale_min.in_units('1'))

    c = A * float(sigma_max * r**2 /float(resolution)**2)

    director['colgas'][3] = c
    director['size'] = [resolution, resolution]
    director['eye'][2] = r
    director['file'] = filename

    return director

def make_param(snapshot, filename=None):
    """
    Generates a default param dictionary.  Can be saved using 
    diskpy.utils.configsave

    EXAMPLE

    snapshot = pynbody.load('snapshot.std')  # Load snapshot
    param_dict = make_param(snapshot)  # Make default param dict
    diskpy.utils.configsave(param_dict, 'snapshot.param', ftype='param') # Save

    Optionally, the user can set the snapshot filename manually
    """
    param = copy.deepcopy(_paramdefault)

    if filename is not None:

        param['achInFile'] = filename
        param['achOutName'] = os.path.splitext(filename)[0]

    elif snapshot.filename != '<created>':

        param['achInFile'] = snapshot.filename
        param['achOutName'] = os.path.splitext(snapshot.filename)[0]

    # Set up the length units
    param['dKpcUnit'] = snapshot['pos'].units.ratio('kpc')
    # Set up the mass units
    param['dMsolUnit'] = snapshot['mass'].units.ratio('Msol')
    # Set the mean molecular mass
    param['dMeanMolWeight'] = snapshot.gas['mu'][0]

    return param
    
def units_from_param(param):
    """
    Figures out the simulation units from a .param file

    **ARGUMENTS**

    param : str or param dict (see configparser)
        Simulation .param file or param dict loaded by configparser
        Can also be a list or numpy array of these in which case a list
        of units dicts is returned

    **RETURNS**

    units : dict
        A dictionary of the units used in the simulation, returned as
        pynbody units
    """
    # Iterate over param if necessary
    if isinstance(param, (list, np.ndarray)):

        outlist = []

        for par in param:

            outlist.append(units_from_param(par))

        return outlist
    
    # Load param if necessary
    if isinstance(param, str):

        param = configparser(param, 'param')

    # Universal G
    G = pynbody.units.G

    # Load units
    dKpcUnit = getpar('dKpcUnit', param)
    dMsolUnit = getpar('dMsolUnit', param)

    # Set up pynbody units
    m_unit = pynbody.units.Unit('{0} Msol'.format(dMsolUnit))
    l_unit = pynbody.units.Unit('{0} kpc'.format(dKpcUnit))
    t_unit = (l_unit**3/(G*m_unit))**(1,2)

    # Convert the time unit to something sensible
    years = t_unit.in_units('yr')
    t_unit = pynbody.units.Unit('{0} yr'.format(years))
    
    # Calculate a couple derived units as well
    v_unit = l_unit/t_unit
    rho_unit = m_unit/l_unit**3
    acc_unit = l_unit/t_unit**2
    pres_unit = rho_unit * v_unit**2
    
    # Return
    outdict = {'l_unit':l_unit, 'm_unit':m_unit, 't_unit':t_unit, 
               'v_unit': v_unit, 'rho_unit': rho_unit, 'acc_unit': acc_unit, 
               'pres_unit': pres_unit}
    return outdict
        
def setup_units(m, x):
    """
    Sets up units for a ChaNGa simulation, defined by position and mass units.
     * time unit = :math:`\\sqrt{L_{unit}^3/G M_{unit}}`
     * velocity unit = :math:`L_{unit}/T_{unit}`
     * temperature units = Kelvin
    
    Parameters
    ----------
    m, x : Unit, string, or SimArray
        Define the mass and position units
    
    Returns
    -------
    units : dict
        A dictionary containing the units
    """
    m_unit = get_units(m)
    pos_unit = get_units(x)
        
    # time units are sqrt(L^3/GM)
    t_unit = np.sqrt((pos_unit**3)*np.power((G*m_unit), -1)).units
    # velocity units are L/t
    v_unit = (pos_unit/t_unit).ratio('km s**-1')
    # Make it a unit
    v_unit = pynbody.units.Unit('{0} km s**-1'.format(v_unit))
    # Temperature (just a hard-coded default)
    temp_unit = get_units('K')
    units = {'m': m_unit, 't': t_unit, 'v': v_unit, 'x': pos_unit, 
    'temp': temp_unit}
    return units
        
def setup_param(param, snapshot=None, r_orb=1.0, n_orb=10.0, n_image=None, n_snap=100, \
n_check=None):
    """
    Sets up the following for a .param file:

        nSteps
        dDumpFrameStep
        iOutInterval
        iCheckInterval

    **ARGUMENTS**

    param : str or param_dict (see diskpy.utils.configparser, configsave)
        parameter file for the simulation, must already have dDelta and units
        set properly
        IF a str, assumed to be a filename
    snapshot : str or TipsySnap(see pynbody) or None
        Snapshot for the simulation.  Needed to estimate the outer orbital
        period.
        IF a str, assumed to be a filename
        IF None, the file pointed to by param is used
    r_orb : float
        radius to calculate the outer orbital period at as a fraction of the
        radius of the farthest out particle.  Must be between 0 and 1
    n_orb : float
        number of outer orbital periods to run simulation for
    n_image : int or None
        Total number of frames to dump (ie, dDumpFrameStep)
        If None, defaults to n_snap
    n_snap : int
        Total number of simulation outputs
    n_check : int or None
        Total number of simulation checkpoints.  If None, defaults to n_snap
    """

    if (r_orb > 1) | (r_orb < 0):

        raise ValueError('r_orb must be between 0 and 1')

    if isinstance(snapshot, str):

        # A filename has been passed, not a tipsy snapshot
        snapshot = pynbody.load(snapshot)

    if isinstance(param, str):

        # A filename has been passed.  Load the dictionary
        param = configparser(param, 'param')

    else:

        # Copy so as to not overwrite the input dict
        param = copy.deepcopy(param)

    R_max = r_orb * snapshot.g['rxy'].max()
    M_star = snapshot.s['mass']

    # Read in .param stuff
    l_unit = '{} kpc'.format(param['dKpcUnit'])
    m_unit = '{} Msol'.format(SimArray(param['dMsolUnit'], 'Msol'))

    # Outer radius and star mass in simulation units
    r = float(R_max.in_units(l_unit))
    M = float(M_star.in_units(m_unit))

    # Calculate the number of time steps to use
    dt = param['dDelta']
    period = 2*np.pi*np.sqrt(r**3/M)
    N = int(np.round(n_orb * period/dt))
    param['nSteps'] = N

    # Calculate how often to output snapshots, frames, checkpoints
    if n_check is None:

        n_check = n_snap

    if n_image is None:

        n_image = n_snap

    param['dDumpFrameStep'] = int(N/n_image)
    param['iOutInterval'] = int(N/n_snap)
    param['iCheckInterval'] = int(N/n_check)

    return param

def find_param_names(simdir='.', paramfile=None, prefix=None):
    """
    Tries to find the .param and associated .log file for a simulation
    
    Returns paramfile, logfile
    
    If a filename is not found it will be returned as None
    """
    import path
    
    prefix = str(prefix)
    with path.Path(simdir) as directory:
        if paramfile is None:
            paramfile = prefix + '.param'
            if not os.path.isfile(paramfile):
                import glob
                names = glob.glob('*.param')
                if len(names) != 1:
                    print("could not find .param file")
                    paramfile = None
                else:
                    paramfile = names[0]
        
        logfile = None
        if paramfile is not None:
            
            try:
                # Load the param file
                param = configparser(paramfile, 'param')
                # Try to load the log file
                achOutName = getpar('achOutName', param)
                
                if os.path.isfile(achOutName + '.log'):
                    logfile = achOutName + '.log'
            except IOError:
                paramfile = None
        
        if logfile is None:
            if os.path.isfile(prefix + '.log'):
                logfile = prefix + '.log'
    
    if paramfile is not None:
        paramfile = os.path.join(simdir, paramfile)
    if logfile is not None:
        logfile = os.path.join(simdir, logfile)
    return paramfile, logfile
