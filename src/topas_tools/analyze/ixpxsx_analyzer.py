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
from pathlib import Path
from glob import glob
from scipy.stats import norm
from typing import List, Dict, Tuple

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
                # IF we do not find the pattern, we cant record. so this has to be skipped. 
                if start_idx != None and end_idx != None: 
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
    # _summarize_log_info: {{{ 
    def _summarize_log_info(self, idx, entry):
        """Return a clean, human-readable summary of log_info."""
        log_info = entry.get("log_info", {})
        avg = log_info.get("avg_logvals", {})
        std = log_info.get("std_logvals", {})
        scan = log_info.get("scan_info", {})
    
        row = {"idx": idx}
    
        # Averages
        for k, v in avg.items():
            if "T" in k:
                row[k] = v
    
        # Standard deviations
        for k, v in std.items():
            if "T" in k:
                row[k] = v
    
        # Scan start/end timestamps
        timestamps = scan.get("timestamps")
        start_idx = scan.get("start_idx")
        end_idx = scan.get("end_idx")
    
        if isinstance(timestamps, (list, tuple)) and start_idx is not None and end_idx is not None:
            try:
                start_ts = timestamps[start_idx]
                end_ts = timestamps[end_idx]
                row["scan_start"] = start_ts
                row["scan_end"] = end_ts
                row["scan_duration_s"] = (end_ts - start_ts).total_seconds()
            except Exception:
                row["scan_start"] = None
                row["scan_end"] = None
                row["scan_duration_s"] = None
        else:
            row["scan_start"] = None
            row["scan_end"] = None
            row["scan_duration_s"] = None
    
        return row

    #}}}
    # export_full_refinement_summary: {{{ 
    def export_full_refinement_summary(self, refinement_dict, excel_path):
        excel_path = Path(excel_path).with_suffix(".xlsx")
        excel_path.parent.mkdir(parents=True, exist_ok=True)
    
        with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
    
            # 1. Summary sheet
            summary_rows = [
                self.summarize_refinement(idx, entry)
                for idx, entry in refinement_dict.items()
                if type(idx) == int 
            ]
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="summary", index=False)
    
            # 2. Log info sheet
            log_rows = []
            for idx, entry in refinement_dict.items():
                if type(idx) == str: 
                    continue
                log_rows.append(self._summarize_log_info(idx, entry))
         
            pd.DataFrame(log_rows).to_excel(writer, sheet_name="log_info", index=False)
    
            # 3. Pattern metadata
            pattern_rows = []
            for idx, entry in refinement_dict.items():
                if type(idx) == str: 
                    continue
                for method, m in entry["method"].items():
                    pat = m["pattern"]
                    row = {
                        "idx": idx,
                        "method": method,
                        "tth_len": len(pat["tth"]) if pat["tth"] is not None else None,
                        "yobs_len": len(pat["yobs"]) if pat["yobs"] is not None else None,
                        "ycalc_len": len(pat["ycalc"]) if pat["ycalc"] is not None else None,
                        "ydiff_len": len(pat["ydiff"]) if pat["ydiff"] is not None else None,
                    }
                    pattern_rows.append(row)
            pd.DataFrame(pattern_rows).to_excel(writer, sheet_name="pattern_meta", index=False)
    
            # 4. Profile data overview
            profile_rows = []
            for idx, entry in refinement_dict.items():
                if type(idx) == str:
                    continue
                for method, m in entry["method"].items():
                    for substance, pdict in m["profile_data"].items():

                        row = {
                            "idx": idx,
                            "method": method,
                            "substance": substance,
                            "num_peaks": len(pdict["H"]),
                            "tth_min": float(np.min(pdict["tth_deg"])),
                            "tth_max": float(np.max(pdict["tth_deg"])),
                            "d_min": float(np.min(pdict["d_angst"])),
                            "d_max": float(np.max(pdict["d_angst"])),
                        }
                        profile_rows.append(row)
            pd.DataFrame(profile_rows).to_excel(writer, sheet_name="profile_data", index=False)
    
            # 5. Out dict (phases)
            phase_rows = []
            for idx, entry in refinement_dict.items():
                if type(idx) == str:
                    continue
                for method, m in entry["method"].items():
                    out = m["out_dict"]
                    for phase_name, phase_dict in out.items():
                        if not phase_name.startswith("Ph"):
                            continue
                        row = {"idx": idx, "method": method, "phase": phase_name}
                        for var, d in phase_dict.items():
                            if isinstance(d, dict) and "value" in d:
                                row[f"{var}_value"] = d["value"]
                                row[f"{var}_error"] = d["error"]
                        phase_rows.append(row)
            pd.DataFrame(phase_rows).to_excel(writer, sheet_name="phases", index=False)
    
        return excel_path

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
    # export_analysis_to_excel:  {{{ 
    def export_analysis_to_excel(
        self, 
        results:dict, excel_dir, excel_filename, 
    ):
        """
        Export:
        - basic refinement summary (existing functionality)
        - full LP-vs-T analysis results (arrays, scalars)
        into a multi-sheet Excel workbook.
        """ 
        excel_dir = Path(excel_dir)
        excel_path = excel_dir.joinpath(excel_filename)
        if excel_path.suffix != ".xlsx":
            excel_path = excel_path.with_suffix(".xlsx")
        excel_path.parent.mkdir(parents=True, exist_ok=True)
    
        # Write the file: {{{ 
        with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
              
            # --- scalars ---
            # Scalars: {{{ 
            scalars = {
                "r2": results["r2"],
                "rmse_lp": results["rmse_lp"],
                "rmse_temp": results["rmse_temp"],
            }
            pd.DataFrame.from_dict(scalars, orient="index", columns=["value"]).to_excel(
                writer, sheet_name="scalars"
            )
    
            #}}}

            # --- raw data ---
            # RAW Data: {{{ 
            raw_df = pd.DataFrame({
                "temps": results["temps"],
                "std_temps": results["std_temps"],
                "lp_vals": results["lp_vals"],
                "lp_errs": results["lp_errs"],
                "mask": results["mask"],
            })
            raw_df.to_excel(writer, sheet_name="raw_data", index=False)
            #}}}
    
            # --- filtered data ---
            # Filtered data: {{{ 
            filt_df = pd.DataFrame({
                "filt_temps": results["filt_temps"],
                "filt_lp_vals": results["filt_lp_vals"],
                "filt_lp_errs": results["filt_lp_errs"],
            })
            filt_df.to_excel(writer, sheet_name="filtered_data", index=False)
            #}}}
    
            # --- fit results ---
            # Fit Results: {{{ 
            fit_df = pd.DataFrame({
                "eval_vals": results["eval_vals"],
                "diff_eval": results["diff_eval"],
                "dadt_fit": results["dadt_fit"],
                "temp_err_fit": results["temp_err_fit"],
                "total_temp_err_fit": results["total_temp_err_fit"],
                "ecdf_fit": results['ecdf_fit'],
                "cdf_fit": results['cdf_fit'],
            })
            fit_df.to_excel(writer, sheet_name="fit_results", index=False)
            #}}}
    
            # --- full-range results ---
            #  Full range results: {{{ 
            full_df = pd.DataFrame({
                "diff_full": results["diff_full"],
                "dadt_full": results["dadt_full"],
                "temp_err_full": results["temp_err_full"],
                "total_temp_err_full": results["total_temp_err_full"],
                'ecdf_full': results['ecdf_full'],
                'cdf_fit_full': results['cdf_fit_full'],
            })
            full_df.to_excel(writer, sheet_name="full_range", index=False)
    
            #}}}

            # --- metadata ---
            # Metadata: {{{ 
            meta_df = pd.DataFrame.from_dict(results.get("meta", {}), orient="index", columns=["value"])
            meta_df.to_excel(writer, sheet_name="meta")
            #}}}
        #}}} 
        return excel_path 
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
    # extract_std_and_temps: {{{ 
    def extract_std_and_temps(self, refinement_dict:dict):
        '''
        Returns a tuple of 
     
        0: temps
        1: standard deviations of temp
        2: hovertemplates
        '''
        stds = []
        temps = []
        hovers = []
    
        for idx, entry in refinement_dict.items():
            filename = self.get_dict_entry(entry, 'xdd')
            std = self.get_dict_entry(entry, 'log_info', 'std_logvals', 'std_TC_As')
            temp = self.get_dict_entry(entry, 'log_info', 'avg_logvals', 'avg_TC_As')
    
            if std is None or temp is None:
                continue
    
            stds.append(std)
            temps.append(temp)

            basename = os.path.basename(filename)
    
            hover = (
                f"{basename}<br>"
                f"idx: {idx}<br>"
                "Sample TC: %{x:.3f}<br>"
                "STD T: %{y:.3f}"
            )
            hovers.append(hover)
    
        return np.array(temps), np.array(stds), hovers


    #}}}
    # extract_lp_and_temps:  {{{ 
    def extract_lp_and_temps(self,
        refinement_dict, 
        phase_key='Ph1', 
        lp_key='lp_a', 
        method_key = 'xPx'
    ):
        '''
        Returns a tuple of arrays: 
        0: temps
        1: lp_vals
        2: lp_errors
        '''
        temps = []
        lp_vals = []
        lp_errs = []
    
        for key, entry in refinement_dict.items():
            if type(key) == str:
                continue
    
            method_entry = entry['method'][method_key]
            avg = entry['log_info']['avg_logvals']
    
            TC_A = avg['avg_TC_As']
            setpoint = avg['avg_set_temps']
    
            if np.isnan(TC_A):
                TC_A = 23
    
            temps.append(TC_A)
    
            out_dict = method_entry['out_dict'][phase_key]
            lp_vals.append(out_dict[lp_key]['value'])
            lp_errs.append(out_dict[lp_key]['error'])
    
        return np.array(temps), np.array(lp_vals), np.array(lp_errs)

    #}}}
    # filter_by_std: {{{ 
    def filter_by_std(
        self,
        temps,
        lp_vals,
        lp_errs,
        std_temps,
        threshold=5,
        rng=None,
    ):
        """
        Returns:
            filtered_temps
            filtered_lp_vals
            filtered_lp_errs
            mask
    
        threshold: maximum allowed standard deviation
        
        rng can be:
            - None
            - a single range
            - a list/tuple of ranges
            - a list/tuple of ints
        """
    
        n = len(temps)
    
        if len(std_temps) != n or len(lp_vals) != n or len(lp_errs) != n:
            raise ValueError("All input arrays must have the same length.")
    
        # --- Normalize rng into a set of indices ---
        exclude = set()
    
        if rng is not None:
            # If user passed a single range, wrap it
            if isinstance(rng, range):
                rng = [rng]
    
            # If user passed a single int, wrap it
            if isinstance(rng, int):
                rng = [rng]
    
            # Now rng is either a list of ranges or ints
            for item in rng:
                if isinstance(item, range):
                    for i in item:
                        if 0 <= i < n:
                            exclude.add(i)
                else:
                    # assume int-like
                    i = int(item)
                    if 0 <= i < n:
                        exclude.add(i)
    
        # --- Threshold-based exclusions ---
        for i, v in enumerate(std_temps):
            if v >= threshold:
                exclude.add(i)
    
        # --- Build mask ---
        mask = np.ones(n, dtype=bool)
        for i in exclude:
            mask[i] = False
    
        return temps[mask], lp_vals[mask], lp_errs[mask], mask 
    #}}}
    # fit_polynomial: {{{ 
    def fit_polynomial(self,temps, lp_vals, degree=4):
        '''
        Fits the data to a polynomial 
        returns a tuple: 
     
        0: polynomial 
        1: eval_vals (values calculated from data)
        2: r2: r square value
        3: rmse: rmse error
        '''
        params = np.polyfit(temps, lp_vals, deg=degree)
        poly = np.poly1d(params)
    
        eval_vals = poly(temps)
        r2 = self.calculate_rsq(lp_vals, eval_vals, precision=6)
        rmse = self.calculate_rmse(lp_vals, eval_vals, precision=6)
    
        return poly, eval_vals, r2, rmse
    #}}}
    # fit_cdf: {{{ 
    def fit_cdf(self,residuals):
        """ 
        Takes the residuals from a fit and fits them to a CDF

        Returns a tuple: 
            0: Empirical CDF
            1: Fit CDF
            2: mu
            3: sigma
        """
        residuals_sorted = np.sort(residuals)
        ecdf = np.arange(1, len(residuals_sorted)+1) / len(residuals_sorted)
        

        mu, sigma = norm.fit(residuals)
        cdf_fit = norm.cdf(residuals_sorted, loc = mu, scale = sigma)

        return ecdf, cdf_fit, mu, sigma
    #}}}
    # get_derivative: {{{ 
    def get_derivative(self, poly, xvals:np.ndarray):
        """ 
        Takes a np.poly1d object 
        from the fit of your data

        Uses numpy's derivative 
        capabilities

        Returns:
            derivative of polynomial evaluated for your data
        """
        dpoly = np.polyder(poly)
        dadt = dpoly(xvals) # Evaluates the array 

        return dadt
    #}}}
    # get_total_temp_error: {{{ 
    def get_total_temp_error(
        self, 
        lp_temp_err:np.ndarray,
        measured_temp_err:np.ndarray,
    ):
        """ 
        Calculates the sum of squares error
        for the temperatures using the error calculated 
        from the difference from the fit

        and the actual measured error in temperature 
        """

        return np.sqrt(lp_temp_err**2 + measured_temp_err**2)

    #}}}
    # print_polynomial: {{{ 
    def print_polynomial_fit(self,poly, r2 = None, rmse = None, ):
        '''
        Prints relevant information from the 
        polynomial fit to data 
        '''
        poly_printout = ['LP = ']
        for j, coeff in enumerate(poly.coeffs):
            num_coeffs = len(poly.coeffs)
            exp = num_coeffs - 1 - j # This should be the exponent
            if coeff >=0 and j != 0:
                string = ' + '
            else:
                string = ''
            string += f'{np.format_float_scientific(coeff,5)}'
            if exp != 0:
                string += f'T^{exp} '
            poly_printout.append(string)
        poly_printout = ''.join(poly_printout)
        print(poly_printout)
        if r2:
            print(f'R^2: {r2}')
        if rmse:
            print(f'RMSE: ± {rmse} Å')

    #}}} 
    # analyze_lp_temperature_series: {{{ 
    def analyze_lp_temperature_series(
        self,
        refinement_dict,
        substance="Si",
        phase = 1,
        lp="a",
        method="xPx",
        poly_deg=2,
        skip_rng=None,
        threshold=5,
        nbins=30,
        hist_color="blue",
        export_excel=False,
        excel_dir=None,
        excel_filename=None,
        plot=True,
        **kwargs
    ):
        """
        High-level pipeline for LP-vs-T analysis:
        - Extract temps, LPs, stds
        - Filter by STD and optional skip ranges
        - Fit polynomial
        - Compute residuals and LP-based temperature error
        - Compute derivative and sensitivity
        - Compute total temperature error
        - Generate plots (optional)
        - Return all arrays in a structured dictionary
        - Optionally export arrays to Excel
        """
    
        # -----------------------------
        # 1. Extract raw data
        # -----------------------------
        # Raw data: {{{ 
        phase_key = f'Ph{phase}'
        lp_key = f'lp_{lp}'
        temps, std_temps, _ = self.extract_std_and_temps(
            refinement_dict,
        )

        temps, lp_vals, lp_errs = self.extract_lp_and_temps(
            refinement_dict, 
            phase_key= phase_key,
            lp_key = lp_key,
            method_key = method,
        )
        #}}}
    
        # -----------------------------
        # 2. Filter by STD + skip ranges
        # -----------------------------
        # filter by STD and skip: {{{ 
        filt_temps, filt_lp_vals, filt_lp_errs, mask = self.filter_by_std(
            temps, lp_vals, lp_errs, std_temps,
            threshold=threshold,
            rng=skip_rng
        )
        #}}}
    
        # -----------------------------
        # 3. Polynomial fit
        # -----------------------------
        # polyfit: {{{ 
        poly, eval_vals, r2, rmse = self.fit_polynomial(
            filt_temps, filt_lp_vals, degree=poly_deg
        )
        #}}}
        self.print_polynomial_fit(poly, r2, rmse)
    
        # -----------------------------
        # 4. Residuals
        # -----------------------------
        # Residuals: {{{ 
        diff_eval = filt_lp_vals - eval_vals
        full_eval = poly(temps)
        diff_full = lp_vals - full_eval
        #}}}
        # CDF: {{{ 
        ecdf, cdf_fit, mu, sigma = self.fit_cdf(diff_eval)
        ecdf_full, cdf_fit_full, mu_full, sigma_full = self.fit_cdf(diff_full)
        #}}}
    
        # -----------------------------
        # 5. Derivatives
        # -----------------------------
        # Derivatives: {{{ 
        dadt_fit = self.get_derivative(poly, filt_temps)
        dadt_full = self.get_derivative(poly, temps)
        #}}}
    
        # -----------------------------
        # 6. Temperature error from LP deviations
        # -----------------------------
        # Temp err from LP devs: {{{ 
        temp_err_fit = diff_eval / dadt_fit
        temp_err_full = diff_full / dadt_full
    
        rmse_temp = np.sqrt(np.mean(temp_err_fit**2))
        #}}}
        avg_lp = np.average(lp_vals)
        pct_diff = rmse/avg_lp * 100
        print(f'RMSE temperature error: {rmse_temp:.3f} {self._degree}C')
        print(f'RMSE error is {pct_diff:.3e} % of mean lattice parameter ({avg_lp:.4f} Å)')
    
        # -----------------------------
        # 7. Total temperature error
        # -----------------------------
        # Total T error: {{{ 
        total_temp_err_full = self.get_total_temp_error(
            temp_err_full, std_temps
        )
        total_temp_err_fit = self.get_total_temp_error(
            temp_err_fit, std_temps[mask]
        )
        #}}}
        # -----------------------------
        # Build Results: 
        # -----------------------------
        # Build results: {{{ 
        results = {
            "temps": temps,
            "std_temps": std_temps,
            "lp_vals": lp_vals,
            "lp_errs": lp_errs,
            "mask": mask,
            "filt_temps": filt_temps,
            "filt_lp_vals": filt_lp_vals,
            "filt_lp_errs": filt_lp_errs,
            "poly": poly,
            "eval_vals": eval_vals,
            "r2": r2,
            "rmse_lp": rmse,
            "diff_eval": diff_eval,
            "diff_full": diff_full,
            "dadt_fit": dadt_fit,
            "dadt_full": dadt_full,
            "ecdf_fit": ecdf,
            "ecdf_full":ecdf_full,
            "cdf_fit": cdf_fit,
            "cdf_fit_full": cdf_fit_full,
            "temp_err_fit": temp_err_fit,
            "temp_err_full": temp_err_full,
            "rmse_temp": rmse_temp,
            "total_temp_err_fit": total_temp_err_fit,
            "total_temp_err_full": total_temp_err_full,
            "meta": {
                "substance": substance,
                "lp": lp,
                "method": method,
                "poly_deg": poly_deg,
                "threshold": threshold,
                "nbins": nbins,
                "mu_fit": mu,
                "sigma_fit": sigma,
                "mu_full": mu_full,
                "sigma_full":sigma_full,
            },
        }
        #}}} 
        # -----------------------------
        # 8. Plotting (optional)
        # -----------------------------
        # Plotting: {{{ 
        if plot: 
            # Fit : {{{ 
            title_text = f"{substance} LP {lp} {method} deg = {poly_deg}"
            self.plot_fit(
                temps, lp_vals, lp_errs,
                filt_temps, filt_lp_vals, filt_lp_errs,
                poly, rmse,
                threshold=threshold,
                title_text=title_text,
                **kwargs
            )
            #}}}  
            # Residuals: {{{  
            self.plot_residuals(
                temps, diff_full, lp_errs,
                filt_temps, diff_eval, filt_lp_errs,
                rmse,
                title_text= f'Δ {title_text} < ±{threshold}°C STD deg = {poly_deg}', 
                **kwargs

            )
            #}}}
            # Histogram of LP residuals{{{ 
            self.plot_lp_histogram(
                diff_eval,
                nbins=nbins,
                color = hist_color,
                title_text= f"{substance} LP {lp} ({method}, deg={poly_deg}) Residuals", 
                **kwargs
            )
            self.show_figure()
            #}}} 
            # Fit to CDF: {{{ 
            self.plot_cdf_for_lps(
                diff_eval,ecdf, cdf_fit, mu, sigma, 
                diff_full, ecdf_full, cdf_fit_full, mu_full, sigma_full,
                substance, lp,
                title_text = f'{substance} LP ({lp}, Å) Fit to CDF deg = {poly_deg}',
                **kwargs
            )
            #}}}
            #Sensitivity + temp error {{{ 
            # LP Sensitivity: {{{ 
            self.plot_lp_sensitivity_to_T(
                temps, dadt_full,
                title_text=f"{substance} {method} poly={poly_deg}",
                lp=lp,
                show_figure=False
            )
            self.add_data_to_plot(
                filt_temps, dadt_fit,
                name=f"d{lp}/dT (fit)",
                mode="lines+markers",
                color="blue",
                show_figure=False
            )
            #}}}
            # Temperature Sensitivity: {{{ 
            self.add_data_to_plot(
                temps, np.abs(temp_err_full),
                name=f"Temp error ({lp}) full",
                color="lightsalmon",
                y3=True,
                mode="lines+markers",
                show_figure=False
            )
            self.add_data_to_plot(
                filt_temps, np.abs(temp_err_fit),
                name=f"Temp error ({lp}) fit",
                color="red",
                y3=True,
                y3_title=f"ΔT (°C)",
                mode="lines+markers",
                legend_x=-0.2
            )
            #}}}
            self.show_figure()
            #}}}
            # Decomposed temperature error{{{ 
            self.plot_decomposed_temp_error(
                temps=temps,
                total_temp_err=total_temp_err_full,
                lp_temp_err=np.abs(temp_err_full),
                meas_temp_err=std_temps,
                title_text=substance,
                lp=lp
            )
            #}}}
             
        #}}}
    
        # -----------------------------
        # 9. Export to Excel (optional)
        # -----------------------------
        # Exporting: {{{ 
        if export_excel:
            if excel_dir is None or excel_filename is None:
                raise ValueError(
                    "Must specify excel_dir and excel_filename when export_excel=True"
                ) 
            self.export_analysis_to_excel( 
                results=results,
                excel_dir=excel_dir,
                excel_filename = f'{excel_filename}_{substance}_LP_{lp}_Poly_{poly_deg}', 
            )
        #}}}
    
        # -----------------------------
        # 10. Return all arrays
        # -----------------------------
        return results 
    #}}}
    # solve_for_T: {{{ 
    def lp_to_temp(self, p, lp_target, domain = None):
        """ 
        This uses a polynomial fit as input 
        and allows you to solve for the 
        temperature that a given lattice parameter 
        corresponds to
        """
        # Solve p(T) = lp_target
        roots = (p - lp_target).roots
        # Keep only real roots
        real = roots[np.isreal(roots)].real

        if domain is not None:
            lo, hi = domain
            real = [r for r in real if lo <= r <= hi]
        return np.array(real)
    #}}}
    # get_indices_for_temperature: {{{ 
    def get_indices_for_temperature(self, refinement_dict, target_temp):
        """ 
        This gets all of the patterns from your 
        refinement dictionary with the same setpoint
        """
        indices = []
        for i, entry in refinement_dict.items():
            if i == "log":
                continue
            sp = self.get_dict_entry(entry, "log_info", "avg_logvals", "avg_set_temps")
            if sp == target_temp:
                indices.append(i)
        return indices

    #}}}
    # collect_lp_deltas: {{{ 
    def collect_lp_deltas(self, refinement_dict, baseline_idx, idx, method, pd_to_ph):
        baseline_entry = refinement_dict[baseline_idx]
        entry = refinement_dict[idx]
    
        base_out = baseline_entry["method"][method]["out_dict"]
        curr_out = entry["method"][method]["out_dict"]
        profile_data = entry["method"][method]["profile_data"]
    
        deltas = {}
        labels = ["a", "b", "c", "al", "be", "ga"]
     
        for substance, pd_entry in profile_data.items():
            ph_key = pd_to_ph[substance]
    
            base_lps = ixpxsx_parser.get_lps_from_out_dict(base_out[ph_key])
            curr_lps = ixpxsx_parser.get_lps_from_out_dict(curr_out[ph_key])
    
            deltas[substance] = {}
    
            for label, base_lp_tuple, curr_lp_tuple in zip(labels, base_lps, curr_lps):
                base_lp, _, base_fixed = base_lp_tuple
                curr_lp, curr_lp_e, curr_fixed = curr_lp_tuple
    
                if base_fixed or curr_fixed:
                    continue
                if base_lp is None or curr_lp is None:
                    continue
    
                pct = abs(base_lp - curr_lp) / base_lp * 100
    
                deltas[substance][label] = {
                    "value": curr_lp,
                    "error": curr_lp_e,
                    "pct_diff": pct,
                }
    
        return deltas


    #}}}
    # get_pattern_for_overlay: {{{ 
    def get_pattern_for_overlay(self, refinement_dict, idx, method):
        method_dict = refinement_dict[idx]["method"][method]
        pat = method_dict["pattern"]
        return {
            "tth": pat["tth"],
            "yobs": pat["yobs"],
            "ycalc": pat["ycalc"],
        }

    #}}}
    # overlay_patterns_at_temperature: {{{ 
    def overlay_patterns_at_temperature(
        self,
        refinement_dict,
        target_temp,
        method="xPx",
        pd_to_ph={"alumina": "Ph2", "si": "Ph1"},
        offset_start_index=1,
        tth_offset=0.0,
        colors=None,
        fit_colors=None,
        show_figure=True,
        *args,
        **kwargs
    ):
        """ 
        This allows you to overlay all of the patterns with identical setpoint 
        in a dataset. 
        
        offset_start_index: If there was an error like we had where 
            the IOC reboot caused a permanent offset after a point,
            this prm defines when that offset kicks in. 
        tth_offset: This is the offset that you request. 
        """
        indices = self.get_indices_for_temperature(refinement_dict, target_temp)
        if not indices:
            print(f"No refinements found at {target_temp} °C.")
            return
     
        if colors is None:
            colors = ["teal", "green", "darkblue", "purple"]
        if fit_colors is None:
            fit_colors = ["orange", "salmon", "rebeccapurple", "gold"]

        baseline_idx = indices[0]
        baseline_entry = refinement_dict[baseline_idx]
        base_method_dict = baseline_entry['method'][method]
        base_out = base_method_dict['out_dict']
        base_pd = base_method_dict['profile_data']
 
        # print the baseline LPs: {{{ 
        print(f"\nBaseline pattern LPs (idx {baseline_idx}):")
        baseline_lps = {}
        labels = ["a", "b", "c", "al", "be", "ga"]
    
        for substance, pd_entry in base_pd.items():
            ph_key = pd_to_ph[substance]
            lps = ixpxsx_parser.get_lps_from_out_dict(base_out[ph_key])
    
            baseline_lps[substance] = {}
            print(substance)
    
            for label, (lp, lp_e, fixed) in zip(labels, lps):
                if not fixed and lp is not None:
                    baseline_lps[substance][label] = lp
                    if label in ["a", "b", "c"]:
                        print(f"\t{label}: {lp:.4f} ± {lp_e:.4f} Å")
                    else:
                        print(f"\t{label}: {lp:.4f} ± {lp_e:.4f} deg")
        #}}}
     
        patterns = []
        lp_delta_info = {}
    
        for j, idx in enumerate(indices):
            pat = self.get_pattern_for_overlay(refinement_dict, idx, method)
    
            apply_offset = offset_start_index is not None and idx >= offset_start_index

            if j == 0:
                hkl_ticks = self.get_hkl_ticks_for_pattern(
                    refinement_dict,
                    idx,
                    method,
                    pd_to_ph,
                    offset=1000,
                )
            else:
                hkl_ticks = None
    
            patterns.append({
                "idx": idx,
                "temp": refinement_dict[idx].get("temp"),
                "tth": pat["tth"],
                "yobs": pat["yobs"],
                "ycalc": pat["ycalc"],
                "color": colors[(j-1) % len(colors)] if j > 0 else "black",
                "fit_color": fit_colors[(j-1) % len(fit_colors)] if j > 0 else "grey",
                "apply_offset": apply_offset,
                "hkl_ticks": hkl_ticks,
            })
    
            if j > 0:
                lp_delta_info[idx] = self.collect_lp_deltas(
                    refinement_dict, baseline_idx, idx, method, pd_to_ph
                )
    
        # Hand off to the Plotter
        self.plot_overlayed_patterns(
            patterns=patterns,
            tth_offset=tth_offset,
            show_figure=show_figure,
            lp_delta_info=lp_delta_info,
            *args,**kwargs,
        )
    
    #}}}
    # get_hkl_ticks_for_pattern: {{{ 
    def get_hkl_ticks_for_pattern(
        self, 
        refinement_dict, 
        idx, 
        method, 
        pd_to_ph, 
        offset=1000
    ):
        """
        Returns a list of dicts, each representing a tick trace:
            {
                "tth": array,
                "y": array,
                "name": substance,
                "hover": list_of_strings,
                "color": color
            }
        """
        entry = refinement_dict[idx]
        method_dict = entry["method"][method]
        profile_data = method_dict["profile_data"]
        out_dict = method_dict["out_dict"]
    
        # Get ydiff to anchor tick offsets
        ydiff = method_dict["pattern"]["ydiff"]
        base_y = min(ydiff)
    
        tick_traces = []
        colors = ["blue", "red", "green", "orange", "purple", "brown"]
    
        for i, (substance, pd_entry) in enumerate(profile_data.items()):
            hs, ks, ls = ixpxsx_parser.get_hkl_from_pd(pd_entry)
            d = ixpxsx_parser.get_d_from_pd(pd_entry)
            tth_pos = ixpxsx_parser.get_tth_from_pd(pd_entry)
            beta_total, beta_total_e = ixpxsx_parser.get_beta_total_from_pd(
                    pd_entry
            )
    
            # vertical offset for this substance
            y_offset = base_y - (np.ones_like(tth_pos) * offset * (i + 1))
    
            # hover templates
            hts = []
            hkls = [] # This stores the tuples of hkls
            for j, p in enumerate(tth_pos):
                h = hs[j]
                k = ks[j]
                l = ls[j]
                hts.append(
                    f"{substance} ({h}, {k}, {l})"
                    f"<br>2{self._theta}: {p}"
                    f"<br>d: {d[j]} Å"
                    f"<br>{self._beta}: {beta_total[j]} ± {beta_total_e[j]}"
                )
                hkls.append((h,k,l))
    
            tick_traces.append({
                "tth": tth_pos,
                "y": y_offset,
                "name": substance,
                "hover": hts,
                "color": colors[i % len(colors)],
                "hkls": hkls
            })
    
        return tick_traces

    #}}}
    # summarize_all_setpoints: {{{ 
    def summarize_experiment_by_setpoint(
        self,
        refinement_dict,
        method="xPx",
        pd_to_ph={"alumina": "Ph2", "si": "Ph1"},
        printouts = True,
    ):
        """
        Produces grouped printouts and a summary list of dictionaries
        containing:
            - Rwp
            - Setpoint
            - TC_A avg/std
            - TC_B avg/std
            - TC_A - TC_B
            - TC_A - setpoint
            - TC_B - setpoint
            - Lattice parameters
            - LP deltas relative to the FIRST entry for each setpoint
        """
    
        # -----------------------------
        # 1. Group indices by setpoint
        # -----------------------------
        setpoint_groups = {}
        for idx, entry in refinement_dict.items():
            if type(idx) == str:
                continue
            sp = entry["log_info"]["avg_logvals"].get("avg_set_temps")
            if sp is None:
                continue
            setpoint_groups.setdefault(sp, []).append(idx)
    
        # -----------------------------
        # 2. Storage for Excel export
        # -----------------------------
        summary_rows = []
    
        # -----------------------------
        # 3. Loop through each setpoint group
        # -----------------------------
        for sp, indices in sorted(setpoint_groups.items()):
            if printouts:
                print("\n" + "=" * 80)
                print(f"SETPOINT: {sp} °C")
                print("=" * 80)
    
            # Establish baseline LPs for this setpoint
            baseline_lp = None
            # Loop through all the grouped indices: {{{ 
            for j, idx in enumerate(indices):
                entry = refinement_dict[idx]
                log_info = entry["log_info"]
                #  Basic Thermometry: {{{ 
                avg = log_info["avg_logvals"]
                std = log_info["std_logvals"]
    
                tc_a = avg.get("avg_TC_As")
                tc_b = avg.get("avg_TC_Bs")
                tc_a_std = std.get("std_TC_As")
                tc_b_std = std.get("std_TC_Bs")
    
                diff_tcA_tcB = tc_a - tc_b
                diff_tcA_sp = tc_a - sp
                diff_tcB_sp = tc_b - sp
                #}}}
    
                # Rwp
                method_dict = entry["method"][method]
                rwp = method_dict["out_dict"]["fit_metrics"]["r_wp"]
     
                # Lattice params: {{{ 
                lp_labels = ["a", "b", "c", "al", "be", "ga"]
                lp_dict = {}
                out_dict = method_dict["out_dict"]
                profile_data = method_dict["profile_data"]


    
                for substance, pd_entry in profile_data.items():
                    ph_key = pd_to_ph[substance]
                    lps = ixpxsx_parser.get_lps_from_out_dict(out_dict[ph_key])
    
                    lp_dict[substance] = {}
                    for label, (lp, lp_e, fixed) in zip(lp_labels, lps):
                        if not fixed and lp is not None:
                            lp_dict[substance][label] = {
                                "value": lp,
                                "error": lp_e,
                            }
                    # --- Compute c/a ratio if both present ---
                    # Compute c/a ratio if both are present: {{{ 
                    if "c" in lp_dict[substance] and "a" in lp_dict[substance]:
                        a_val = lp_dict[substance]["a"]["value"]
                        c_val = lp_dict[substance]["c"]["value"]
                        a_err = lp_dict[substance]["a"]["error"]
                        c_err = lp_dict[substance]["c"]["error"]
                 
                        if a_val not in (None, 0) and c_val is not None:
                            ratio = c_val / a_val
                            # error propagation: σ(c/a) = (c/a)*sqrt((σc/c)^2 + (σa/a)^2)
                            ratio_err = ratio * np.sqrt((c_err / c_val)**2 + (a_err / a_val)**2)
                 
                            lp_dict[substance]["c_over_a"] = {
                                "value": ratio,
                                "error": ratio_err,
                            }

                    #}}}
                #}}}
    
                # Establish baseline LPs for this setpoint
                if j == 0:
                    baseline_lp = lp_dict
     
                # Compute LP deltas: {{{ 
                lp_deltas = {}
                for substance in lp_dict:
                    lp_deltas[substance] = {}
                    for label in lp_dict[substance]:
                        curr_val = lp_dict[substance][label]["value"]
                        base_val = baseline_lp[substance][label]["value"]
                        pct = abs(curr_val - base_val) / base_val * 100 if base_val else None
    
                        lp_deltas[substance][label] = {
                            "value": curr_val,
                            "error": lp_dict[substance][label]["error"],
                            "pct_diff": pct,
                        } 
                    # compute delta c/a if present: {{{ 
                    if "c_over_a" in lp_dict[substance]:
                        curr_val = lp_dict[substance]["c_over_a"]["value"]
                        base_val = baseline_lp[substance]["c_over_a"]["value"]
                        pct = abs(curr_val - base_val) / base_val * 100 if base_val else None
                 
                        lp_deltas[substance]["c_over_a"] = {
                            "value": curr_val,
                            "error": lp_dict[substance]["c_over_a"]["error"],
                            "pct_diff": pct,
                        }
                    #}}}
                #}}}

    
                # -----------------------------
                # PRINT BLOCK
                # -----------------------------
                # printouts: {{{ 
                if printouts:
                    print("-" * 60)
                    print(f"idx {idx} — Rwp = {rwp:.3f}")
                    print(f"TC_A: {tc_a:.2f} ± {tc_a_std:.2f}")
                    print(f"TC_B: {tc_b:.2f} ± {tc_b_std:.2f}")
                    print(f"TC_A - TC_B = {diff_tcA_tcB:.2f}")
                    print(f"TC_A - SP = {diff_tcA_sp:.2f}")
                    print(f"TC_B - SP = {diff_tcB_sp:.2f}")
     
                    print("\nLattice Parameters:")
                    for substance, vals in lp_dict.items():
                        print(f"  {substance}:")
                        for label, d in vals.items():
                            print(
                                f"\t{label}: {d['value']:.4f} ± {d['error']:.4f}"
                            )
                        if "c_over_a" in lp_dict[substance]:
                            r = lp_dict[substance]["c_over_a"]
                            print(
                                f"\tc/a: {r['value']:.6f} ± {r['error']:.6f}"
                            )

    
                    print("\nLP Differences from Baseline:")
                    for substance, vals in lp_deltas.items():
                        print(f"  {substance}:")
                        for label, d in vals.items():
                            print(
                                f"\t{label}: {d['value']:.4f} ± {d['error']:.4f} "
                                f"({d['pct_diff']:.4f}% diff)"
                            )
                        if "c_over_a" in lp_deltas[substance]:
                            d = lp_deltas[substance]["c_over_a"]
                            print(
                                f"\tc/a: {d['value']:.6f} ± {d['error']:.6f} "
                                f"({d['pct_diff']:.4f}% diff)"
                            )

                #}}}
    
                # -----------------------------
                # Append to summary rows
                # -----------------------------
                row = {
                    "idx": idx,
                    "setpoint": sp,
                    "rwp": rwp,
                    "tc_a": tc_a,
                    "tc_a_std": tc_a_std,
                    "tc_b": tc_b,
                    "tc_b_std": tc_b_std,
                    "tcA_minus_tcB": diff_tcA_tcB,
                    "tcA_minus_sp": diff_tcA_sp,
                    "tcB_minus_sp": diff_tcB_sp,
                    "lp": lp_dict,
                    "lp_deltas": lp_deltas,
                }
                summary_rows.append(row)
            #}}}
    
    
        return summary_rows
    
    #}}}
    # select_temperature_groups: {{{ 
    def select_temperature_groups(
        self,
        sp_summary_rows,
        setpoint,
        idx=None,
        require_single=False
    ):
        """
        Return all entries whose setpoint matches EXACTLY.
        This mirrors your manual loop behavior.
    
        Parameters
        ----------
        sp_summary_rows : list of dict
        setpoint : float
            Exact setpoint value to match (no tolerance).
        idx : int or list[int] or None
            Optional refinement_dict idx filter.
        require_single : bool
            If True, raise an error if multiple matches are found.
    
        Returns
        -------
        list[dict] or dict
        """
    
        # Normalize idx input
        if isinstance(idx, int):
            idx = [idx]
    
        matches = []
    
        for row in sp_summary_rows:
            if row["setpoint"] == setpoint:
                if idx is None or row["idx"] in idx:
                    matches.append(row)
    
        if not matches:
            raise ValueError(f"No entries found with setpoint == {setpoint}")
    
        if require_single:
            if len(matches) > 1:
                raise ValueError(
                    f"Multiple entries found for setpoint {setpoint}: "
                    f"{[m['idx'] for m in matches]}"
                )
            return matches[0]
    
        return matches

    #}}}
    # compute_lp_based_temperatures: {{{ 
    def compute_lp_based_temperatures(self, phase_dicts: List[Dict], domain=(0, np.inf)):
        """
        For each calibration curve (each phase_dict), compute the temperature
        predicted from its lattice parameters using lp_to_temp().
    
        Returns:
            List[np.ndarray]: one array per phase_dict, containing T_calc for each LP.
        """
        all_calc_temps = []
    
        for phase_dict in phase_dicts:
            lp_vals = self.get_dict_entry(phase_dict, "lp_vals")
            poly = self.get_dict_entry(phase_dict, "poly")
    
            t_calc = np.array([
                min(self.lp_to_temp(poly, lp, domain=domain))
                for lp in lp_vals
            ])
    
            all_calc_temps.append(t_calc)
    
        return all_calc_temps
    #}}}
    # compute_lp_temperature_for_index: {{{ 
    def compute_lp_temperature_for_index(
        self,
        idx: int,
        phase_dicts: List[Dict],
        lp_labels: List[str],
        measured_temps: List[float],
        domain=(0, np.inf),
        printout: bool = True,
    ) -> Tuple[float, float]:
        """
        Compute the temperature predicted by each calibration curve for a single index.
    
        Returns:
            avg_calc_temp (float)
            std_calc_temp (float)
            calc_temps (np.ndarray)
        """
        measured_temp = measured_temps[idx]
    
        calc_temps = []
        lp_values = []
    
        # Compute T_calc for each calibration curve
        for phase_dict in phase_dicts:
            lp_val = self.get_dict_entry(phase_dict, "lp_vals")[idx]
            lp_values.append(lp_val)
    
            poly = self.get_dict_entry(phase_dict, "poly")
            t_calc = min(self.lp_to_temp(poly, lp_val, domain=domain))
            calc_temps.append(t_calc)
    
        calc_temps = np.array(calc_temps)
        avg_calc_temp = np.mean(calc_temps)
        std_calc_temp = np.std(calc_temps)
    
        if printout:
            print(
                f"Average LP‑based T: {avg_calc_temp:.3f} ± {std_calc_temp:.3f} {self._degree}C "
                f"(Measured: {measured_temp:.3f} {self._degree}C)"
            )
    
        # Pairwise comparisons
        combos_done = set()
        for i, t1 in enumerate(calc_temps):
            for j, t2 in enumerate(calc_temps):
                if i >= j:
                    continue
    
                label1 = lp_labels[i]
                label2 = lp_labels[j]
    
                diff = abs(t1 - t2)
                pct_diff = diff / measured_temp * 100
    
                diff1_from_avg = abs(t1 - avg_calc_temp)
                diff2_from_avg = abs(t2 - avg_calc_temp)
    
                if printout:
                    print(f"\nComparison: {label1} vs {label2}")
                    print(f"  ΔT = {diff:.3f} {self._degree}C ({pct_diff:.2f}% of measured)")
                    print(f"  |T({label1}) - avg| = {diff1_from_avg:.3f} {self._degree}C")
                    print(f"  |T({label2}) - avg| = {diff2_from_avg:.3f} {self._degree}C")
                    print(f"  LP({label1}) = {lp_values[i]:.6f} → T = {t1:.3f}")
                    print(f"  LP({label2}) = {lp_values[j]:.6f} → T = {t2:.3f}")
    
        return avg_calc_temp, std_calc_temp #, calc_temps

    #}}}
    # prepare_overlay_difference_data: {{{ 
    def prepare_overlay_difference_data(
        self,
        refinement_dict,
        indices,
        method="xPx",
        phase_key="Ph1",
        reference_hkl=(1,1,1),
        diff_scale=1.0,
        pd_to_ph={'alumina':'Ph2','si':'Ph1'},
    ):
        """
        Prepare normalized patterns, difference curves, and HKL ticks.
        Normalization is done using the observed intensity of a specific
        HKL reflection from a specific phase.
        """
    
        patterns = []
        baseline = None
    
        # -----------------------------------------
        # Translate phase_key → substance name ("si" or "alumina")
        # -----------------------------------------
        try:
            substance_name = [pd for pd, ph in pd_to_ph.items() if ph == phase_key][0]
        except IndexError:
            raise ValueError(f"phase_key '{phase_key}' not found in pd_to_ph mapping.")
    
        for i, idx in enumerate(indices):
            entry = refinement_dict[idx]
            method_entry = entry["method"][method]
    
            tth = method_entry["pattern"]["tth"]
            yobs = method_entry["pattern"]["yobs"]
            ycalc = method_entry["pattern"]["ycalc"]
    
            # -----------------------------------------
            # Get HKL ticks (list of dicts)
            # -----------------------------------------
            tick_list = self.get_hkl_ticks_for_pattern(
                refinement_dict,
                idx,
                method=method,
                pd_to_ph=pd_to_ph
            )
    
            # -----------------------------------------
            # Find the tick dict for the desired substance
            # -----------------------------------------
            phase_tick_dict = None
            for d in tick_list:
                if d["name"].lower() == substance_name.lower():
                    phase_tick_dict = d
                    break
    
            if phase_tick_dict is None:
                raise ValueError(
                    f"Substance '{substance_name}' not found in HKL ticks for idx {idx}"
                )
    
            # -----------------------------------------
            # Find HKL index using the new hkls list
            # -----------------------------------------
            hkls = phase_tick_dict["hkls"]
            try:
                hkl_idx = hkls.index(reference_hkl)
            except ValueError:
                raise ValueError(
                    f"HKL {reference_hkl} not found in substance '{substance_name}' for idx {idx}"
                )
    
            # -----------------------------------------
            # Extract the 2θ position of that HKL
            # -----------------------------------------
            ref_tth = phase_tick_dict["tth"][hkl_idx]
    
            # -----------------------------------------
            # Extract observed intensity at that peak
            # -----------------------------------------
            peak_idx = np.argmin(np.abs(tth - ref_tth))
            ref_intensity = yobs[peak_idx]
    
            # -----------------------------------------
            # Normalize pattern
            # -----------------------------------------
            if i == 0:
                baseline_intensity = ref_intensity
                yobs_norm = yobs.copy()
                ycalc_norm = ycalc.copy()
            else:
                scale = baseline_intensity / ref_intensity

                yobs_norm = yobs * scale
                ycalc_norm = ycalc * scale
    
            # -----------------------------------------
            # Store pattern
            # -----------------------------------------
            patterns.append({
                "idx": idx,
                "temp": entry["temp"],
                "tth": tth,
                "yobs": yobs_norm,
                "ycalc": ycalc_norm,
                "hkl_ticks": tick_list,
            })
    
            if i == 0:
                baseline = yobs_norm.copy()
    
        # -----------------------------------------
        # Difference curves
        # -----------------------------------------
        for p in patterns:
            p["diff"] = (p["yobs"] - baseline) * diff_scale
    
        return patterns
    
    #}}}
#}}}
