# Authorship: {{{
# Written by: Dario C. Lewczyk
# Date: 09-13-2024
#}}}
# Imports: {{{
from topas_tools.plotting.plotting_utils import GenericPlotter
from topas_tools.utils.topas_utils import Utils, UsefulUnicode
import re
import os
#}}}
# JANA_Plot: {{{
class JANA_Plot(GenericPlotter, UsefulUnicode):
    # __init__: {{{
    def __init__(self, hklm_dir:str = None): 
        GenericPlotter.__init__(self) 
        UsefulUnicode.__init__(self)
    #}}}
#}}}
