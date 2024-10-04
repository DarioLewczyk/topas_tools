pyFprime readme:
pyFprime is a rewrite in python of the Windows utility routine I wrote in 1994 in pascal.

pyFprime calculates values of f' & f" for elements Li-Cf for the range in x-ray wavelength 0.05-3.0A (248-4.13keV) using the Cromer & Liberman algorithm and orbital cross-section tables. It's operation is largely self-explanatory (I hope). Note that the Cromer - Liberman algorithm fails in computing f' for wavelengths < 0.16A (77.48keV) for the heaviest elements (Au-Cf) and fails to correctly compute f', f" and mu for wavelengths > 2.67 (4.64keV) for very heavy elements (Am-Cf). pyFprime plots for each selected element f' and f" for the allowed energy range and the corresponding x-ray form factor including the energy dependent f' value. The latter plot covers the accessible range (0-160 degrees 2-theta) for the wavelength/energy selected up to a limit of sin(theta)/lambda of 2.0; it can be plotted in sin(theta)/lambda, q or 2-theta units. 

Tested with 
(Windows)
python 2.5.2 & 2.5.4
wxpython 2.8.8.1 & 2.8.9.2
matplotlib 0.91.4 & 0.98.5.2
(Mac OS X)
python:  2.6.1
wxpython:  2.8.9.1
matplotlib:  0.98.5.2
(Linux -- FC10)
python:  2.5.2
wxpython:  2.8.9.1
matplotlib:  0.98.1

Install all of these before trying pyFprime. Compatibility with other versions of these packages is unknown.

Identified problems:
Linux: drag of vertical line in f', f'' plot fails; elements buttons are drawn with borders 
which partly obscures the element labels

Bob Von Dreele & Brian Toby
6/14/2009

