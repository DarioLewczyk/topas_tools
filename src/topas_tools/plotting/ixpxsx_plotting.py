# Authorship: {{{ 
"""  
Written by: Dario C. Lewczyk
Date: 01/28/26
"""
#}}}
# imports: {{{ 
import os
import numpy as np
from topas_tools.plotting.plotting_utils import GenericPlotter
from topas_tools.utils.topas_utils import Utils
from topas_tools.analyze import ixpxsx_parser as ip 
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
#  IxPxSx_Plotter: {{{ 
class IxPxSx_Plotter(Utils, GenericPlotter):
    """ 
    This provides tools to easily parse and generate figures for 
    relevant data stored in the refinement_dict
    """
    # plot_ixpxsx_xy: {{{ 
    def plot_ixpxsx_xy(
        self,
        refinement_dict:dict,
        idx = 0,
        method = 'IPS',
        offset = 1000,
        pd_to_ph = {'alumina': 'Ph2', 'si': 'Ph1'},
        *args,
        **kwargs
    ):
        """ 
        This function allows us to plot the results
        of a refinement using whatever IxPxSx method
        that you choose

        pd_to_ph: profile_data key to out_dict Ph key
            Since the out_dict doesn't care about substance
            name, need to translate it manually

        kwargs: colors
        """
        colors = kwargs.get('colors', ['blue', 'red', 'green', 'orange'])

        #  get all dictionaries: {{{ 
        ref_dict = self.get_dict_entry(refinement_dict, idx) # Ref dict at idx 

        method_dict = self.get_dict_entry(ref_dict, 'method', method)
        log_info = self.get_dict_entry(ref_dict, 'log_info')

        out_dict = self.get_dict_entry(method_dict, 'out_dict')
        profile_data = self.get_dict_entry(method_dict, 'profile_data')
     
        avg_logvals = self.get_dict_entry(log_info, 'avg_logvals')
        std_logvals = self.get_dict_entry(log_info, 'std_logvals')
        #}}}

        #  print out temp information: {{{ 
        sp, tc_a, tc_b = ip.get_temps_from_log(
                avg_logvals, mode = 'avg'
        )
        sp_std, tca_std, tcb_std = ip.get_temps_from_log(
                std_logvals, mode = 'std'
        )
        print(f'Setpoint for scan: {sp:.1f} {self._deg_c}')
        print(f'Avg TC (A) for scan: {tc_a:.2f} ± {tca_std:.2f} {self._deg_c}')
        print(f'Avg TC (B) for scan: {tc_b:.2f} ± {tcb_std:.2f} {self._deg_c}')
        #}}}

        #  get xdd name: {{{ 
        xdd = self.get_dict_entry(refinement_dict, idx, 'xdd')
        if xdd:
            xdd = os.path.basename(xdd)
        else:
            xdd = ''
        #}}}
        #  get Rwp: {{{ 
        rwp = out_dict['fit_metrics'].get('r_wp') 
        try:
            ips_out_dict = self.get_dict_entry(
                ref_dict, 'method', 'IPS','out_dict'
            )
            ips_rwp = self.get_dict_entry(
                ips_out_dict, 'fit_metrics', 'r_wp'
            )
            print(f'Improvement in Rwp {method} vs. IPS:\n\t{rwp - ips_rwp}')
        except:
            ips_out_dict = None
        #}}}
        #  get the xy data to plot: {{{ 
        tth, yobs, ycalc, ydiff = ip.get_output_xy_from_refinement_dict(
                refinement_dict = refinement_dict,
                idx = idx, 
                method = method
        )
        #}}}
        #  make xy plot: {{{ 
        title_text = f'{xdd} ({method}) Rwp: {rwp:.2f}'
        self.plot_topas_xy_output(
            tth = tth,
            yobs = yobs,
            ycalc = ycalc,
            ydiff=ydiff,
            title_text= title_text,
            *args,
            **kwargs
        )
        #}}}
        # get the hkl ticks: {{{ 
        for i, (substance, entry) in enumerate(profile_data.items()):
            h,k,l = ip.get_hkl_from_pd(entry)
            d = ip.get_d_from_pd(entry)
            tth_pos = ip.get_tth_from_pd(entry)
            beta_total, beta_total_e = ip.get_beta_total_from_pd(entry)
            color = colors[i]

            # This defines offset from the bottom of the pattern
            y_offset = min(ydiff) - (np.ones_like(tth_pos)*offset*(i+1))

            hts = [] 
            # loop through the 2theta positions: {{{ 
            for j, p in enumerate(tth_pos):
                hts.append(
                    f'{substance} ({h[j]}, {k[j]}, {l[j]})' +
                    f'<br>2{self._theta}: {p}<br>d: {d[j]} Å' +
                    f'<br>{self._beta}: {beta_total[j]} ± {beta_total_e[j]}'
                )    
            #}}}
            #  Print out info about the refinement LPs: {{{ 
            try:
                out_ph_entry = out_dict.get(pd_to_ph.get(substance)) 
            except:
                raise ValueError(f'Substance: {substance} not in profile_data')
            lps = ip.get_lps_from_out_dict(out_ph_entry)

            lp_printout = substance
            lp_labels= [
                    'a', 'b', 'c', 
                    self._alpha, self._beta, self._gamma
            ]
            #  loop through lps: {{{ 
            for k,(lp, lp_e, fixed) in enumerate(lps):
                lp_txt = lp_labels[k]
                #  Å LPs: {{{ 
                if k <=2 and lp and not fixed:
                    lp = np.around(lp, 4)
                    lp_printout += f'\n\t{lp_txt}: {lp}'
                    if lp_e:
                        lp_e = np.format_float_scientific(lp_e, 2)
                        lp_printout += f' ± {lp_e} Å'
                    else:
                        lp_printout += ' Å'
                #}}}
                #  deg LPs: {{{ 
                elif k >2 and lp and not fixed: 
                    lp = np.around(lp, 2)
                    lp_printout += f'\n\t{lp_txt}: {lp}'
                    if lp_e:
                        lp_e = np.format_float_scientific(lp_e, 2)
                        lp_printout += f'± {lp_e} {self._degree}'
                    else:
                        lp_printout += f' {self._degree}'
                #}}}
            #}}}
            print(lp_printout)
            #}}}
            #  compare LPs to IPS if present: {{{ 
            try:
                ips_ph_entry = ips_out_dict.get(pd_to_ph.get(substance))
                ips_lps = ip.get_lps_from_out_dict(ips_ph_entry) 
            except:
                ips_lps = None
            if not ips_lps == None:
                printout = substance
                ips_ph_entry = ips_out_dict.get(pd_to_ph.get(substance))
                ips_lps = ip.get_lps_from_out_dict(ips_ph_entry)
                for k, (lp, _, fixed) in enumerate(lps):
                    lp_label = lp_labels[k]
                    ips_lp, _, ips_fixed = ips_lps[k]
                    if lp and ips_lp and not fixed:
                    
                        printout += f'\n\t{lp_label} (IPS-{method}): '
                        diff = ips_lp - lp # difference
                        pct_diff = diff/ips_lp * 100 
                        if k <=2:
                            printout += f'{diff:.4f} ({pct_diff:.4f}%) Å'
                        if k > 2:
                            printout += f'{diff:.4f} ({pct_diff:.4f}%)'
                            printout += f'{self._degree}'
                print(printout) 
            #}}}
            # add substance to plot: {{{ 
            self.add_data_to_plot(
                tth_pos,
                y_offset,
                name = substance,
                hovertemplate = hts,
                symbol = 'line-ns',
                color = color,
                *args,
                **kwargs
            )
            #}}}
        #}}}
        self.show_figure()
    #}}}
#}}}
