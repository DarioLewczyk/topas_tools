# Authorship: {{{ 
""" 
Written by Dario C. Lewczyk
Date: 01/28/26
"""
#}}}
#  Imports: {{{ 
import os
import numpy as np
import pandas as pd
from glob import glob

## This is necessary for grabbing the logfiles and headers
from aps_11bm_tools.utils.utils import Utils as APSUtils

## These are necessary for parsing TOPAS files
from topas_tools.utils.topas_parser import TOPAS_Parser
from topas_tools.plotting.ixpxsx_plotting import IxPxSx_Plotter

# This gives the ability to parse TOPAS 8 IxPxSx profiles.out files
from topas_tools.analyze import ixpxsx_parser

if __name__ == "__main__":
    # In this case, import regular tqdm because running from CLI
    from tqdm import tqdm
else:
    # If running as a module, import notebook version
    from tqdm.notebook import tqdm
#}}}
# IxPxSxAnalyzer: {{{ 
class IxPxSxAnalyzer(IxPxSx_Plotter, TOPAS_Parser, APSUtils):
    """  
    Class designed to make collection and analysis of 
    IxPxSx data (particularly automated) fast and easy
    This also works well with temperature series data
    from the APS
    """
    def __init__(
        self, 
        refinement_dir:str = os.getcwd(),
        logfile_dir:str = None,
        ixpxsx_methods:list = ['IPS', 'xPS', 'xPx', 'xxx'],
        mode = 0
    ):
        """  
        refinement_dir: directory with all refinement subdirectories 
        logfile_dir: directory where your logfile (if applicable) is
        ixpxsx_methods: subdirs (and method names) for your analysis

        NOTE: 
            All of the refinement directories should have the same
            IxPxSx method directories
        """
        super().__init__()
         
        self.refinement_dir = refinement_dir
        self.logfile_dir = logfile_dir
        self.ixpxsx_methods = ixpxsx_methods
    # get_refinement_dict: {{{ 
    def get_refinement_dict(
        self, 
        log_fn:str,
        **kwargs

    ):
        """  
        This function will gather useful information from logs, 
        profile_data, and TOPAS OUT files and build a dictionary
        of all of the data sorted by method for each directory
        of an IxPxSx refinement set

        logfiles must be .txt
        """
        refinement_dict = {} 
        log_dict = {}
        log_timestamps = None
        logfile = None

        log_separator = kwargs.setdefault('log_separator', '\t')
        data_extension = kwargs.setdefault('data_extension', 'xy')
        
        # search for logfile and parse if given: {{{ 
        if log_fn:
            if not log_fn.endswith('.txt'):
                log_fn = f'{log_fn}.txt'
            logfile = glob(os.path.join(self.logfile_dir, log_fn))
            if len(logfile) != 1:
                raise ValueError('Logfile {log_fn} not found!')
            logfile = logfile[0]

            log_dict = self._parse_single_logfile(
                logfile=logfile, log_separator=log_separator
            )
            # Datetime object list for the log
            log_timestamps = log_dict['log_info'].get('timestamps')
        #}}}
        # Get directories from refinements: {{{ 
        refinement_dirs = self.get_dirs_for_ixpxsx_automations(
            home_dir= self.refinement_dir,
            data_extension= data_extension,
            ixpxsx_types=self.ixpxsx_methods,
        )
        #}}}
        # Loop though refinement directories: {{{
        pbar1 = tqdm(refinement_dirs, desc = "Refinement Dirs", position=0)
        for i, path in enumerate(pbar1):
            pbar1.set_description_str(f'Processing {os.path.basename(path)}')
            # Initialize the entry
            refinement_dict[i] = {
                'xdd': '',
                'header_info': {},
                'log_info': {
                    'filename':logfile,
                    'avg_logvals':{},
                    'std_logvals':{},
                    'scan_info':{},
                },
                'method': {},

            } 
            # get XDD Pattern Info: {{{ 
            dummy_out = os.path.join(path, 'Dummy.out')
            with open(dummy_out, 'r') as f:
                lines = f.readlines()

            dummy_dict = self.get_inp_out_dict(
                lines, 
                record_phase_prms=False,
                record_bkg=False,
                record_displacement=False,
                record_fit_metrics=False,
                record_output_xy=False, 
                fileextension=data_extension,
            )
            xdd_fn = dummy_dict['xdd'].get('filename')
            xdd_fn = os.path.join(path,xdd_fn)
            if not os.path.exists(xdd_fn):
                raise ValueError(f"No file: {xdd_fn}")
            # Update the refinement_dict
            refinement_dict[i]['xdd'] = xdd_fn
                
            # Now, we need to get the header info
            _, header = self._get_header(xdd_fn)
            header_dict = self.parse_xye_header(header)

            #Update header
            refinement_dict[i]['header_info'] = header_dict
            xdd_timestamp = header_dict.get('timestamp')
            num_steps = header_dict.get('num_steps')
            tps = header_dict.get('time_per_step')
            scantime_s = num_steps * tps
            #}}}
            # update the log info for entry: {{{ 
            if log_dict:
                start_idx, end_idx = self.find_scan_indices(
                    dt_list= log_timestamps,
                    target_dt=xdd_timestamp,
                    scantime=scantime_s,
                )
                log_info = refinement_dict[i]['log_info']
                scan_info = log_info['scan_info']
                scan_info.update({
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                })
                for key, value in log_dict['log_info'].items(): 
                    scan_info.update({
                        key:value[start_idx:end_idx]
                    })
                    try:
                        val_slice = value[start_idx:end_idx]
                        val_slice = np.array(val_slice)

                        avg_val = np.average(val_slice)
                        std_val = np.std(val_slice)
                        
                        log_info['avg_logvals'].update({
                            f'avg_{key}':avg_val
                        })
                        log_info['std_logvals'].update({
                            f'std_{key}':std_val
                        })
                        if 'set_temps' in key:
                            # The setpoint should be a good way to 
                            # get the temperature for the scan
                            refinement_dict[i]['temp'] = int(avg_val)
                    except:
                        pass
            #}}} 
            #  loop through IxPxSx Methods: {{{  
            for ixpxsx in os.scandir(path): 
                tth, yobs, ycalc, ydiff = None, None, None, None
                if ixpxsx.is_dir(): 
                    # Initialize the method
                    refinement_dict[i]['method'][ixpxsx.name] = {}
                    method_dict = refinement_dict[i]['method'][ixpxsx.name]

                    ixpxsx_dir = ixpxsx.path
                    # There should be a set of files here
                    # 1) profiles.out
                    # 2) possibly an output .xy
                    # 3) a TOPAS .out file
 
                    topas_out = [
                        f for f in glob(os.path.join(ixpxsx_dir, '*.out'))
                        if '_profile' not in f
                    ][0]
                    # 1) Get the refined pattern data
                    output_xy = glob(os.path.join(ixpxsx_dir, '*.xy'))
                    if output_xy:
                        output_xy = output_xy[0] # Should only be 1
                        tth, yobs, ycalc, ydiff = self.load_output_xy(output_xy)
                    # 2) We get the profiles.out data into dictionaries
                    profile_data = ixpxsx_parser.parse_ixpxsx_dir(ixpxsx_dir)
                    # 3) Get the out_dict
                    with open(topas_out,'r') as f:
                        lines = f.readlines()
                    out_dict = self.get_inp_out_dict(lines)

                    method_dict.update({
                        'pattern': {
                            'tth': tth,
                            'yobs': yobs,
                            'ycalc': ycalc,
                            'ydiff': ydiff,
                        },
                        'profile_data': profile_data,
                        'out_dict':out_dict,
                    }) 
            #}}}  
        #}}}
        refinement_dict['log'] = log_dict
        return refinement_dict
    #}}}
    # summarize_refinement: {{{ 
    def summarize_refinement(self, idx, entry):
        """ 
        This will return a flattened entry for a refinement_dict
        that can be easily exported to Excel.
        """
    
        row = {}
    
        # top-level
        row["idx"] = idx
        row["temp"] = entry.get("temp")
        xdd_fn = str(os.path.basename(entry.get("xdd")))
        row["xdd"] = xdd_fn#entry.get("xdd")
        # header_info
        # h = entry.get("header_info", {})
        # for k, v in h.items():
        #     row[f"header_{k}"] = v
    
        # log_info
        log = entry.get("log_info", {})
        avg = log.get("avg_logvals", {})
        std = log.get("std_logvals", {})
    
        for k, v in avg.items():
            if 'T' in k:
                row[f"avg_{k}"] = v
        for k, v in std.items():
            if 'T' in k:
                row[f"std_{k}"] = v
    
        # method
        methods = entry.get('method')
        for method, method_entry in methods.items():
         
            # Out Dict 
            out = method_entry.get('out_dict')
            # phases (Ph1, Ph2)
            for phase_name, phase_dict in out.items():
                if phase_name.startswith("Ph"):
                    for var, d in phase_dict.items():
                        # d = {"value": ..., "error": ...}
                        if isinstance(d, dict) and 'keepS' not in var:
                            row[f"{phase_name}_{method}_{var}_value"] = d.get("value")
                            row[f"{phase_name}_{method}_{var}_error"] = d.get("error")
    
            # specimen displacement
            sd = out.get("Specimen_Displacement", {})
            if isinstance(sd, dict):
                row[f"displacement_value_{method}"] = sd.get("value")
                row[f"displacement_error_{method}"] = sd.get("error")
    
            # fit metrics
            fm = out.get("fit_metrics", {})
            if isinstance(fm, dict):
                row[f"r_wp_{method}"] = fm.get("r_wp")
        return row

    #}}}
    # basic_ref_dict_to_excel: {{{ 
    def basic_ref_dict_to_excel(
            self, 
            refinement_dict:dict, 
            excel_dir:str, 
            filename:str
    ):
        """ 
        Exports a refinement dictionary to Excel

        NOTE: This does not include the profile data or the 
                full log or any of the other array-like data
                stored in refinement_dict
        """
        if not filename.endswith('.xlsx'):
            filename = f'{filename}.xlsx'


        summary_rows = [
            self.summarize_refinement(idx, entry)
            for idx, entry in refinement_dict.items()
            if idx != 'log' # This is very important to skip!
        ]
     
        df = pd.DataFrame(summary_rows)
        
        # Create the Excel sheet
        if not os.path.exists(excel_dir):
            os.makedirs(excel_dir)
        excel_file = os.path.join(excel_dir, filename)
        df.to_excel(excel_file, index=False)

        return df
    #}}}
#}}}
