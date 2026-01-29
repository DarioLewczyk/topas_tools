# Authorship: {{{ 
""" 
Written by Dario C. Lewczyk
Date: 01/28/26
"""
#}}}
#  Imports: {{{ 
import os
import numpy as np
from glob import glob

## This is necessary for grabbing the logfiles and headers
from aps_11bm_tools.utils.utils import Utils as APSUtils

## These are necessary for parsing TOPAS files
from topas_tools.utils.topas_parser import TOPAS_Parser
from topas_tools.utils.topas_utils import Utils as TOPASUtils

# This gives the ability to parse TOPAS 8 IxPxSx profiles.out files
from topas_tools.analyze import ixpxsx_parser 

#}}}
# IxPxSxAnalyzer: {{{ 
class IxPxSxAnalyzer(APSUtils, TOPAS_Parser)
#}}}
