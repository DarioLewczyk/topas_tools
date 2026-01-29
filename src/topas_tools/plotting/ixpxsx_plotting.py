# Authorship: {{{ 
"""  
Written by: Dario C. Lewczyk
Date: 01/28/26
"""
#}}}
# imports: {{{ 
from topas_tools.plotting.plotting_utils import GenericPlotter
#}}}

# make_hovertemplate: {{{
def make_hovertemplate(xs, ys, yerrs, hs, ks, ls,  labels = ['s (nm^-1)', 'IZTF IB']):
    hts = []
    for i, y in enumerate(ys):
        x = np.around(xs[i],4)
        yerr = np.around(yerrs[i], 4)
        y = np.around(y, 4)
        h = int(hs[i])
        k = int(ks[i])
        l = int(ls[i])
        hts.append(f'hkl: ({h},{k},{l})<br>{labels[0]}: {x}<br>{labels[1]}: {y} ± {yerr}<br>'+'y: %{y}')
    return hts
#}}}
