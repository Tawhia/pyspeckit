"""
units.py

Author: Adam Ginsburg
Affiliation: University of Colorado at Boulder
Created on March 9th, 2011

Unit parsing and conversion tool.  
The SpectroscopicAxis class is meant to deal with unit conversion internally
"""


length_dict = {'meters':1.0,'m':1.0,
        'centimeters':1e-2,'cm':1e-2,
        'millimeters':1e-3,'mm':1e-3,
        'nanometers':1e-9,'nm':1e-9,
        'micrometers':1e-6,'micron':1e-6,'microns':1e-6,'um':1e-6,
        'kilometers':1e3,'km':1e3,
        'angstroms':1e-10,'A':1e-10,
        }

frequency_dict = {
        'Hz':1.0,
        'kHz':1e3,
        'MHz':1e6,
        'GHz':1e9,
        'THz':1e12,
        }

velocity_dict = {'meters/second':1.0,'m/s':1.0,
        'kilometers/s':1e3,'km/s':1e3,'kms':1e3,
        'centimeters/s':1e-2,'cm/s':1e-2,'cms':1e-2,
        }

conversion_dict = {
        'VELOCITY':velocity_dict,  'Velocity':velocity_dict,  'velocity':velocity_dict,  'velo': velocity_dict, 'VELO': velocity_dict,
        'LENGTH':length_dict,      'Length':length_dict,      'length':length_dict, 
        'FREQUENCY':frequency_dict,'Frequency':frequency_dict,'frequency':frequency_dict, 'freq': frequency_dict, 'FREQ': frequency_dict,
        }

unit_type_dict = {
    'Hz' :'frequency', 'kHz':'frequency', 'MHz':'frequency', 'GHz':'frequency',
    'THz':'frequency', 
    'meters/second':'velocity', 'm/s':'velocity', 'kilometers/s':'velocity',
    'km/s':'velocity', 'kms':'velocity', 'centimeters/s':'velocity',
    'cm/s':'velocity', 'cms':'velocity', 
    'meters':'length','m':'length',
    'centimeters':'length','cm':'length',
    'millimeters':'length','mm':'length',
    'nanometers':'length','nm':'length',
    'micrometers':'length','micron':'length','microns':'length','um':'length',
    'kilometers':'length','km':'length',
    'angstroms':'length','A':'length',
    None: None,
    }

xtype_dict = {
        'VLSR':'velocity','VRAD':'velocity','VELO':'velocity',
        'VOPT':'velocity',
        'VHEL':'velocity',
        'VGEO':'velocity',
        'VREST':'velocity',
        'velocity':'velocity',
        'Z':'redshift',
        'FREQ':'frequency',
        'frequency':'frequency',
        'WAV':'length',
        'WAVE':'length',
        'wavelength':'length',
        }

frame_dict = {
        'VLSR':'LSR','VRAD':'LSR','VELO':'LSR',
        'VOPT':'LSR',
        'VHEL':'heliocentric',
        'VGEO':'geocentric',
        'velocity':'LSR',
        'VREST':'rest',
        'Z':'rest',
        'FREQ':'rest',
        'frequency':'rest',
        'WAV':'rest',
        'WAVE':'rest',
        'wavelength':'rest',
        }

speedoflight_ms = 2.99792458e8 # m/s

import numpy as np

class SpectroscopicAxis(np.ndarray):
    """
    A Spectroscopic Axis object to store the current units of the spectrum and
    allow conversion to other units and frames.  Typically, units are velocity,
    wavelength, frequency, or redshift.  Wavenumber is also hypothetically
    possible.
    """

    def __new__(self, xarr, unit, frame='rest', xtype=None, reffreq=None,
            redshift=None):
        subarr = np.array(xarr)
        subarr = subarr.view(self)
        subarr.units = unit
        subarr.frame = frame
        if xtype in xtype_dict:
            subarr.xtype = xtype_dict[xtype]
            subarr.frame = frame_dict[xtype]
        else:
            subarr.xtype = unit_type_dict[subarr.units]
        subarr.reffreq = reffreq
        subarr.redshift = redshift

        return subarr

    def convert_to(self,unit,frame='rest',**kwargs):
        if unit == self.units and frame == self.frame:
            print "Already in desired units and frame"
        elif frame == self.frame:
            conversion_factor = conversion_dict[self.xtype][self.units] / conversion_dict[self.xtype][unit] 
            self *= conversion_factor
        else:
            print "Converting frames from %s to %s" % (self.frame,frame)

    def velocity_to_frequency(self,center_frequency=None,frequency_units='Hz',convention='radio'):
        """
        Conventions defined here:
        http://www.gb.nrao.edu/~fghigo/gbtdoc/doppler.html
        * Radio 	V = c (f0 - f)/f0 	f(V) = f0 ( 1 - V/c )
        * Optical 	V = c (f0 - f)/f 	f(V) = f0 ( 1 + V/c )-1
        * Redshift 	z = (f0 - f)/f 	f(V) = f0 ( 1 + z )-1
        * Relativistic 	V = c (f02 - f 2)/(f02 + f 2) 	f(V) = f0 { 1 - (V/c)2}1/2/(1+V/c) 
        """
        if center_frequency is None:
            raise ValueError("Cannot convert velocity to frequency without specifying a central frequency.")
        if frequency_units not in frequency_dict:
            raise ValueError("Bad frequency units: %s" % (frequency_units))

        velocity_ms = self * velocity_dict['m/s'] / velocity_dict[self.units]
        if convention == 'radio':
            freq = central_frequency * (1.0 - velocity_ms / speedoflight_ms)
        elif convention == 'optical':
            freq = central_frequency * (1.0 + velocity_ms / speedoflight_ms) - 1.0
        elif convention == 'relativistic':
            freq = central_frequency * (1.0 - (velocity_ms / speedoflight_ms)**2)**0.5 / (1.0 + velocity_ms/speedoflight_ms)
        else:
            raise ValueError('Convention "%s" is not allowed.' % (convention))
        self[:] = freq
        self.units = frequency_units
        self.xtype = 'Frequency'

    def frequency_to_velocity(self,center_frequency=None,center_frequency_units='Hz',velocity_units='m/s',convention='radio'):
        """
        Conventions defined here:
        http://www.gb.nrao.edu/~fghigo/gbtdoc/doppler.html
        * Radio 	V = c (f0 - f)/f0 	f(V) = f0 ( 1 - V/c )
        * Optical 	V = c (f0 - f)/f 	f(V) = f0 ( 1 + V/c )-1
        * Redshift 	z = (f0 - f)/f 	f(V) = f0 ( 1 + z )-1
        * Relativistic 	V = c (f02 - f 2)/(f02 + f 2) 	f(V) = f0 { 1 - (V/c)2}1/2/(1+V/c) 
        """
        if center_frequency is None:
            raise ValueError("Cannot convert frequency to velocity without specifying a central frequency.")
        if center_frequency_units not in frequency_dict:
            raise ValueError("Bad frequency units: %s" % (frequency_units))
        if velocity_units not in velocity_dict:
            raise ValueError("Bad velocity units: %s" % (velocity_units))

        frequency_hz = self * frequency_dict['Hz'] / frequency_dict[self.units]
        center_frequency_hz = center_frequency * frequency_dict['Hz'] / frequency_dict[center_frequency_units]

        if convention == 'radio':
            velocity = speedoflight_ms * ( frequency_hz - center_frequency_hz ) / center_frequency_hz
        elif convention == 'optical':
            velocity = speedoflight_ms * ( frequency_hz - center_frequency_hz ) / frequency_hz
        elif convention == 'relativistic':
            velocity = speedoflight_ms * ( center_frequency_hz**2 - frequency_hz**2 ) / ( center_frequency_hz**2 + frequency_hz )**2
        else:
            raise ValueError('Convention "%s" is not allowed.' % (convention))
        self[:] = velocity * velocity_dict['m/s'] / velocity_dict[velocity_units]
        self.units = velocity_units
        self.xtype = 'Velocity'