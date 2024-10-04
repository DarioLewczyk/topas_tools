#!/usr/bin/env python

########### SVN repository information ###################
# $Date: 2011-07-05 20:09:41 +0000 (Tue, 05 Jul 2011) $
# $Author: vondreele $
# $Revision: 89 $
# $URL: trunk/setup.py $
# $Id: setup.py 89 2011-07-05 20:09:41Z vondreele $
########### SVN repository information ###################

from distutils.core import setup
import os
import sys

# make sure our development source is found FIRST!
sys.path.insert(0, os.path.abspath('./src/pyFprime'))
import fprime

#  http://docs.python.org/distutils/setupscript.html
#  http://docs.python.org/install/index.html

long_description = '''For calculating real and resonant X-ray scattering factors to 250keV;       
based on Fortran program of Cromer & Liberman corrected for 
Kissel & Pratt energy term; Jensen term not included'''

setup(name = 'pyFprime',
      version = fprime.__version__,
      author = 'Robert B. Von Dreele (Argonne National Laboratory)',
      author_email = 'vondreele@anl.gov',
      url         = 'https://subversion.xor.aps.anl.gov/trac/pyFprime',
      license = '(c) 2008',
      description = 'calculate real and resonant X-ray scattering factors',
      long_description = long_description,
      packages=['pyFprime',],
      package_dir={'pyFprime': 'src/pyFprime'},
      package_data = {'pyFprime': ['*.dat', 'readme.txt']},
)
