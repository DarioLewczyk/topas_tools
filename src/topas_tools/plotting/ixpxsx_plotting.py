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
    # __init__: {{{ 
    def __init__(self):  
        super().__init__()
        # plot_defaults: {{{ 
        self._plot_defaults = {
            "fit": {
                "height": 600,
                "width": 1000,
                "notation": "power",
                "legend_x": 0.5,
                "font_size": 16,
            },
            "residuals": {
                "height": 600,
                "width": 1000,
                "notation": "power",
                "ldegend_x": -0.1,
                "font_size": 16,
                "yrange": [-0.001, 0.001],
            },
            "histogram": {
                "height": 600,
                "width": 500,
                "notation": "power",
                "opacity": 0.7,
                "bargap": 0.05,
            },
            "cdf": {
                "height": 600,
                "width": 1000,
                "notation": "power",
                "legend_x": 0.75,
            },
            "lp_sensitivity": {
                "height": 650,
                "width": 1000,
                "notation": "power",
                "color": "lightblue",
                "mode": "lines+markers",
            },
            "temp_sensitivity": {
                "height": 650,
                "width": 1000,
                "notation": "power",
                "color": "lightsalmon",
                "mode": "markers",
            },
            "decomposed_temp_error": {
                "height": 900,
                "width": 700,
                "notation": "power",
                "xrange": [0, 1400],
            },
        }

        #}}}
    #}}}
    # _merge_plot_kwargs: {{{ 
    def _merge_plot_kwargs(self, plot_type: str, user_kwargs: dict):
        """
        Merge:
        1. global defaults (if you add them later)
        2. per-plot defaults
        3. user overrides
        """
        defaults = self._plot_defaults.get(plot_type, {})
        merged = {**defaults, **user_kwargs}
        return merged

    #}}}
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
        # The default behavior is to show the plot.
        show_figure = kwargs.get('show_figure', True) 

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
        if show_figure:
            self.show_figure()
    #}}}
    # plot_fit: {{{ 
    def plot_fit(
        self, temps, lp_vals, lp_errs,
        filt_temps, filt_lp_vals, filt_lp_errs,
        poly, rmse,
        threshold=5,
        title_text = 'Si LP a xPx',
        *args,
        **kwargs,
    ):
        """ 
        temps: list of all of the temperature data
        lp_vals: list of all LP vals
        lp_errs: list of all LP errors

        filt_temps: list of only temps from fit range
        filt_lp_vals = list of only LPs from fit range
        filt_lp_errs = list of only LP errs from fit range

        threshold: STD threshold from filter
        title_text: Additional title text if wanted
        """
        kwargs = self._merge_plot_kwargs("fit", kwargs)
        kwargs.setdefault('legend_x', 0.5)
 
        x_temps = np.linspace(0, 1300, 1000)
        fit_vals = poly(x_temps)

        hts = []
        hts_filt = []

        for i, temp in enumerate(temps):
            lp = lp_vals[i]
            lpe = lp_errs[i]
            hts.append(
                    f'Pattern: {i}<br>'+
                    f'Temp: {temp} {self._degree}C<br>'
                    f'LP: {lp:.6f} ± {lpe:.6f}',
            )
            if lp in filt_lp_vals and lpe in filt_lp_errs:
                hts_filt.append(
                    f'Pattern: {i}<br>'+
                    f'Temp: {temp} {self._degree}C<br>'
                    f'LP: {lp:.6f} ± {lpe:.6f}',
                )
     
        main_title = f'{title_text} (Refined LPs < ±{threshold}°C STD)'
        # Main fit plot
        self.plot_data(
            temps, lp_vals, name='All LPs',
            yaxis_title='Lattice Parameter (Å)',
            xaxis_title=f'Temperature {self._deg_c}',
            title_text= main_title,
            color='lightgrey', y_err=lp_errs, mode='markers', symbol='circle-open', 
            hovertemplate = hts,
            *args, **kwargs
        )
        self.add_data_to_plot(
            filt_temps, filt_lp_vals, y_err=filt_lp_errs,
            color='black', mode='markers',
            name=f'Si LP (a) < ±{threshold}°C STD',
            hovertemplate = hts_filt,
        )
        self.add_data_to_plot(
            x_temps, fit_vals,
            name=f'Fit: RMSE = {rmse} Å',
            color='red', mode='lines', 
            *args, **kwargs
        )
        self.show_figure() 
    #}}}
    # plot_residuals: {{{ 
    def plot_residuals(self,
        temps, diff_full, lp_errs,
        filt_temps, diff_eval, filt_lp_errs,
        rmse,
        title_text,  
        *args, **kwargs
    ):
        """ 
        Plots the results of fitting LP data
        to a polynomial model as residuals
        """
        x_temps = np.linspace(0, 1300, 1000)
        kwargs = self._merge_plot_kwargs("residuals",kwargs)

 
        # Residuals: {{{   
        # Plot the full dataset: {{{ 
        self.plot_data(
            temps, diff_full, name='ΔLP (all refinements)',
            yaxis_title='Δ Lattice Parameter (Å)',
            xaxis_title=f'Temperature {self._deg_c}',
            color='lightgrey', y_err=lp_errs, mode='markers',
            symbol='circle-open',
            title_text=title_text, 
            *args, **kwargs
        )
        #}}}
        # Plot the filtered dataset: {{{ 
        self.add_data_to_plot(
            filt_temps, diff_eval,
            name='Δ LP (only fit)',
            color='black', mode='markers',
            symbol='circle-open', y_err=filt_lp_errs
        )
        self.add_data_to_plot(
            x_temps, np.zeros_like(x_temps),
            name=f'Baseline fit: RMSE = {rmse} Å',
            color='red', mode='lines', 
            *args, **kwargs

        )
        #}}} 
        self.show_figure()
        #}}}
    #}}}
    # plot_lp_sensitivity_to_T: {{{ 
    def plot_lp_sensitivity_to_T(self, 
        temps, 
        derivative, 
        title_text = 'Si xPx LP',
        lp:str = 'a',
        *args,
        **kwargs,
    ):
        """ 
        This function allows you to quickly plot the sensitivity of
        LPs to T
        """
        kwargs = self._merge_plot_kwargs("lp_sensitivity", kwargs)
        kwargs.setdefault('height', 650)
        kwargs.setdefault('width',1000)
        kwargs.setdefault('show_figure',True)
        kwargs.setdefault('color', 'lightblue')
        kwargs.setdefault('mode', 'lines+markers')
        kwargs.setdefault('name',f'd{lp}/dT sensitivity')

        self.plot_data(temps, derivative,
            title_text=f'{title_text} ({lp}) Sensitivity to T',    
            xaxis_title=f'Temperature {self._deg_c}',
            yaxis_title=f'd{lp}/dT (Å/°C)',   
            *args,
            **kwargs,
        )
    #}}}
    # plot_T_sensitivity_to_lp: {{{ 
    def plot_T_sensitivity_to_lp(self,
        temps, 
        temp_err,
        title_text = 'Si xPx LP',
        lp:str = 'a',
        *args,
        **kwargs,
    ):
        """ 
        This function plots the sensitivity of T
        to the lattice parameter given its distance
        from the calibration curve

        Useful for seeing how errors propagate
        """
        kwargs = self._merge_plot_kwargs("temp_sensitivity", kwargs)
        height = kwargs.get('height', 650)
        width = kwargs.get('width',1000)
        kwargs.setdefault('show_figure',True)
        kwargs.setdefault('color', 'lightsalmon')
        kwargs.setdefault('mode', 'markers')
        kwargs.setdefault('name', 'Temp error (full range)')
        self.plot_data(
            temps, np.zeros_like(temps),
            title_text=f'{title_text} ({lp}) Temp error from LPs', 
            xaxis_title=f'Temperature {self._deg_c}',
            yaxis_title='ΔT (°C)',
            mode = 'lines',
            dash = 'dash',
            color = 'black',
            show_in_legend=False,
            height = height,
            width = width, 
        )

        self.add_data_to_plot(temps,temp_err,
            *args,
            **kwargs,
        )
    #}}}
    # plot_decomposed_temp_error: {{{ 
    def plot_decomposed_temp_error(self,
        temps:np.ndarray,
        total_temp_err:np.ndarray,
        lp_temp_err:np.ndarray,
        meas_temp_err:np.ndarray,
        title_text = 'Si',
        lp:str = 'a',
        *args,
        **kwargs
    ):
        """ 
        Useful to see what is the dominant contributor to 
        temperature errors
        """
        kwargs = self._merge_plot_kwargs("decomposed_temp_error", kwargs)
        kwargs.setdefault('height', 900)
        kwargs.setdefault('width', 700)
        kwargs.setdefault('xrange', [0, 1400])
        
        # Total error: {{{ 
        self.plot_data(
            temps, total_temp_err,
            name=f"σ(T_total, {lp})",
            yaxis_title="Temperature Uncertainty (°C)",
            xaxis_title=f"Temperature {self._deg_c}",
            color="black",
            mode="markers",
            title_text=f"Temperature Uncertainty Components ({title_text} {lp})",
            *args, **kwargs
        )
        #}}}
        # lp error: {{{ 
        self.add_data_to_plot(
            temps, 
            lp_temp_err,
            name=f"σ(T_from_LP, {lp})", 
            color="red", 
            mode="markers",
            symbol = 'circle-open'
        )
        #}}}
        # measured error: {{{ 
        self.add_data_to_plot(
            temps, meas_temp_err,
            name="σ(T_meas)", color="blue", 
            mode="markers", legend_x=0,
            symbol = 'circle-open', 
            *args,
            **kwargs
        )
        #}}}
        # zero line{{{ 
        self.add_data_to_plot(
            temps, np.zeros_like(temps),
            color = 'grey',
            mode = 'lines',
            dash = 'dash',
            *args,
            **kwargs
        )
        #}}}
         
        self.show_figure()

    #}}}
    # plot_lp_histogram: {{{ 
    def plot_lp_histogram(self,
        x,
        nbins,
        color,
        title_text,
        xaxis_title = "Δ LP (Å)",
        *args,
        **kwargs,

    ):
        """ 
        Generic histogram for a series of lattice parameters
        good for seeing the distribution of points about a fit line
        """
        kwargs = self._merge_plot_kwargs('histogram', kwargs)
        self.plot_histogram(
            x,
            nbins=nbins,
            color=color,
            title_text=title_text,
            xaxis_title= xaxis_title, 
            *args,
            **kwargs 
        ) 
    #}}}
    # plot_cdf_for_lps: {{{ 
    def plot_cdf_for_lps(
        self, 
        residuals, ecdf, cdf_fit, mu, sigma,
        residuals_full, ecdf_full, cdf_fit_full, mu_full, sigma_full,
        substance, lp,
        title_text,
        *args, **kwargs
    ):
        """ 
        This function plots a CDF fit to your data so that it can clearly be seen how 
        well the fit does at distributing errors normally about the mean. 
        """
        kwargs = self._merge_plot_kwargs('cdf', kwargs)
        
        xaxis_title = f'Residual LP ({lp}, Å)'
        yaxis_title = 'CDF'
        
        fit_stats_full = f'µ = {mu_full:.2e}, σ={sigma_full:.2e}',
        fit_stats = f'µ = {mu:.2e}, σ={sigma:.2e}',

        title_text = f'{title_text} ({fit_stats})'

        residuals_sorted = np.sort(residuals)
        residuals_full_sorted = np.sort(residuals_full)

        # Full dataset: {{{ 
        self.plot_data(
            residuals_full_sorted, ecdf_full, 
            name = f'Emperical CDF (Full {substance} {lp})',
            color = 'lightgrey',mode = 'markers', symbol = 'circle-open', 
            xaxis_title=xaxis_title,yaxis_title=yaxis_title, 
            title_text=title_text, 
            hovertemplate = 'Residual: %{x:.4e} Å<br>CDF: %{y:.2f}',
            *args, **kwargs
        )
        self.add_data_to_plot(
            residuals_full_sorted, cdf_fit_full,
            name = f'CDF (Full {substance} {lp})',
            color = 'lightsalmon', mode = 'lines', dash = 'dash',
            hovertemplate = f'{fit_stats_full}<br>'+'Residual: %{x:.4e} Å<br>CDF: %{y:.2f}',
            
        )
        #}}}
        # fit region: {{{ 
        self.add_data_to_plot(
            residuals_sorted, ecdf, name = f'Empirical CDF ({substance} {lp})', 
            color = 'black',  
            mode = 'markers', symbol = 'circle-open',
            hovertemplate = 'Residual: %{x:.4e} Å<br>CDF: %{y:.2f}',
        ) 
        self.add_data_to_plot(
            residuals_sorted, cdf_fit, 
            name = f'Normal CDF ({substance} {lp})',
            color = 'red', mode = 'lines',
            hovertemplate = f'{fit_stats_full}<br>'+'Residual: %{x:.4e} Å<br>CDF: %{y:.2f}', 
            *args,
            **kwargs
        )
        #}}}
        self.show_figure()
    #}}}
    # plot_overlayed_patterns: {{{ 
    def plot_overlayed_patterns(
        self,
        patterns,
        tth_offset=0.0,
        show_figure=True,
        lp_delta_info=None,
        *args,
        **kwargs
    ):
        kwargs.setdefault('height', 650)
        kwargs.setdefault('width', 1200)
        # Use the first pattern to initialize the figure
        first = patterns[0]
        tth0 = first["tth"] - (tth_offset if first["apply_offset"] else 0.0)
    
        self.plot_data(
            tth0,
            first["yobs"],
            name=f"Observed {first['temp']}°C (idx {first['idx']})",
            color=first["color"],
            mode="lines",
            show_figure=False,
            *args,
            **kwargs
        )
        self.add_data_to_plot(
            tth0,
            first["ycalc"],
            name=f"Calculated {first['temp']}°C (idx {first['idx']})",
            color=first["fit_color"],
            mode="lines",
        )
        # --- Add HKL ticks for baseline pattern ---
        if "hkl_ticks" in patterns[0]:
            for tick in patterns[0]["hkl_ticks"]:
                self.add_data_to_plot(
                    tick["tth"],
                    tick["y"],
                    name=tick["name"],
                    hovertemplate=tick["hover"],
                    symbol="line-ns",
                    color=tick["color"],
                    mode="markers",
                )
     
    
        if lp_delta_info and first["idx"] in lp_delta_info:
            print(f"\nLP deltas for idx {first['idx']} ({first['temp']}°C):")
            for substance, vals in lp_delta_info[first["idx"]].items():
                print(f"  {substance}:")
                for lp_label, d in vals.items():
                    print(
                        f"    {lp_label}: {d['value']:.4f} ± {d['error']:.4e} "
                        f"({d['pct_diff']:.4f}% diff)"
                    )
    
        # Remaining patterns
        for p in patterns[1:]:
            tth = p["tth"] - (tth_offset if p["apply_offset"] else 0.0)
    
            self.add_data_to_plot(
                tth,
                p["yobs"],
                name=f"Observed {p['temp']}°C (idx {p['idx']})",
                color=p["color"],
                mode="lines",
            )
            self.add_data_to_plot(
                tth,
                p["ycalc"],
                name=f"Calculated {p['temp']}°C (idx {p['idx']})",
                color=p["fit_color"],
                mode="lines",
                *args,
                **kwargs
            )
    
            if lp_delta_info and p["idx"] in lp_delta_info:
                print(f"\nLP deltas for idx {p['idx']} ({p['temp']}°C):")
                for substance, vals in lp_delta_info[p["idx"]].items():
                    print(f"  {substance}:")
                    for lp_label, d in vals.items():
                        print(
                            f"    {lp_label}: {d['value']:.4f} ± {d['error']:.4f} "
                            f"({d['pct_diff']:.4f}% diff)"
                        )
    
        if show_figure:
            self.show_figure()


    #}}}
    # plot_overlay_with_differences: {{{ 
    def plot_overlay_with_differences(
        self,
        patterns,
        tth_offset=0.0,
        show_calc=True,
        show_figure=True,
        tick_offset=0.05,
        *args,
        **kwargs
    ):
        """
        Plot normalized patterns, optional calculated patterns,
        difference curves, and HKL ticks using the tick arrays
        produced by get_hkl_ticks_for_pattern().
        """
    
        # Baseline pattern
        base = patterns[0]
        tth0 = base["tth"] - tth_offset
    
        # First pattern initializes the figure
        self.plot_data(
            tth0,
            base["yobs"],
            name=f"Obs idx {base['idx']} ({base['temp']}°C)",
            mode="lines",
            color="blue",
            show_figure=False,
            *args,
            **kwargs
        )
    
        if show_calc:
            self.add_data_to_plot(
                tth0,
                base["ycalc"],
                name=f"Calc idx {base['idx']}",
                mode="lines",
                color="black",
            )
    
        # HKL ticks for baseline 
        tick_list = base["hkl_ticks"]
        for tick in tick_list:
            tth_arr = tick['tth']
            y_arr = tick["y"]
            hover_arr = tick["hover"]
            name = tick["name"]
            color = tick["color"]

            self.add_data_to_plot(
                tth_arr - tth_offset,
                y_arr,
                name=name,
                hovertemplate=hover_arr,
                mode="markers",
                symbol="line-ns",
                color=color,
            )
    
        # Remaining patterns
        for i, p in enumerate(patterns[1:], start=1):
            tth = p["tth"] - tth_offset 
            color = self._generate_color_family(seed = i*0.13)
    
            # Observed
            self.add_data_to_plot(
                tth,
                p["yobs"],
                name=f"Obs idx {p['idx']} ({p['temp']}°C)",
                mode="lines",
                color=color,
            )
    
            # Calculated
            if show_calc:
                self.add_data_to_plot(
                    tth,
                    p["ycalc"],
                    name=f"Calc idx {p['idx']}",
                    mode="lines",
                    color="black",
                )
    
            # HKL ticks (with vertical offset)
            tick_list = p["hkl_ticks"]
            for tick in tick_list:
                tth_arr = tick["tth"]
                y_arr = tick["y"]
                hover_arr= tick["hover"]
                name = tick["name"]
            
                self.add_data_to_plot(
                    tth_arr - tth_offset,
                    y_arr - i * tick_offset,
                    name="HKL",
                    hovertemplate=hover_arr,
                    mode="markers",
                    symbol="line-ns",
                    color=color,
                )
    
            # Difference curve
            self.add_data_to_plot(
                tth,
                p["diff"],
                name=f"Δ idx {p['idx']} vs {base['idx']}",
                mode="lines",
                dash="dot",
                color=color,
                *args,
                **kwargs
            )
    
        if show_figure:
            self.show_figure()

    #}}} 
    # plot_overlay_with_differences: {{{ 
    def plot_overlay_with_differences(
        self,
        patterns,
        tth_offset=0.0,
        show_calc=True,
        show_figure=True,
        tick_offset=0.05,
        *args,
        **kwargs
    ):
        # Defaults: 
        kwargs.setdefault('xaxis_title',f'2{self._theta}{self._degree}')
        kwargs.setdefault('yaxis_title', 'Intensity')
        kwargs.setdefault('title_text', 'Difference between patterns')
        kwargs.setdefault('height', 600)
        kwargs.setdefault('width', 1200)
        kwargs.setdefault('legend_x',0)
    
        # Baseline pattern
        base = patterns[0]
        colors = self._generate_color_family(seed=0.1)
        tth0 = base["tth"] - tth_offset
    
        # Observed baseline
        self.plot_data(
            tth0,
            base["yobs"],
            name=f"Obs idx {base['idx']} ({base['temp']}°C)",
            mode="lines",
            color=colors["base"],
            show_figure=False, 
            *args,
            **kwargs
        )
    
        # Calculated baseline
        if show_calc:
            self.add_data_to_plot(
                tth0,
                base["ycalc"],
                name=f"Calc idx {base['idx']}",
                mode="lines",
                color=colors["calc"],
            )
    
        # HKL ticks for baseline
        for tick in base["hkl_ticks"]:
            self.add_data_to_plot(
                tick["tth"] - tth_offset,
                tick["y"],
                name=f"HKL {tick['name']}",
                hovertemplate=tick["hover"],
                mode="markers",
                symbol="line-ns",
                color=colors["ticks"],
            )
    
        # Remaining patterns
        for i, p in enumerate(patterns[1:], start=1):
            colors = self._generate_color_family(seed=i*0.33)
            tth = p["tth"] - tth_offset
    
            # Observed
            self.add_data_to_plot(
                tth,
                p["yobs"],
                name=f"Obs idx {p['idx']} ({p['temp']}°C)",
                mode="lines",
                color=colors["base"],
            )
    
            # Calculated
            if show_calc:
                self.add_data_to_plot(
                    tth,
                    p["ycalc"],
                    name=f"Calc idx {p['idx']}",
                    mode="lines",
                    color=colors["calc"],
                )
    
            # HKL ticks
            for tick in p["hkl_ticks"]:
                self.add_data_to_plot(
                    tick["tth"] - tth_offset,
                    tick["y"] - i * tick_offset,
                    name=f"HKL {tick['name']}",
                    hovertemplate=tick["hover"],
                    mode="markers",
                    symbol="line-ns",
                    color=colors["ticks"],
                )
    
            # Difference curve
            self.add_data_to_plot(
                tth,
                p["diff"],
                name=f"Δ idx {p['idx']} vs {base['idx']}",
                mode="lines",
                dash="dot",
                color=colors["diff"],
                *args,
                **kwargs
            )
    
        if show_figure:
            self.show_figure()
    
    #}}}
#}}}
