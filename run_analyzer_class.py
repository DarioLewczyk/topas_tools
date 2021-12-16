import sys,os
old_mac = '/Users/christopherlewczyk/Documents/Stony_Brook/Khalifah_Research_Group/Python_Tools/'
new_mac = '/Users/dariolewczyk/Documents/Stony_Brook/Khalifah_Research_Group/Python_Tools/'
if os.path.exists(old_mac):
    sys.path.insert(0,old_mac)
elif os.path.exists(new_mac):
    sys.path.insert(0,new_mac)
import python_to_topas_rietveld as ref
from importlib import reload #ensures we are always on the newest version
reload(ref)#ensures we are always on the newest version
def run_analyzer(title='',
        select_figures=False, 
        show_rwp=True,
        xlim=80,
        ylim=17500,
        no_bottom_ylim = False,
        only_show_sample_name_and_number = True,
        show_title = True,
        full_custom_title = '' 
        ):
    data = ref.Analyzer()
    data.make_plots(show_diff=True,
            legend_size=24,
            title_size=28,
            usr_title=title,
            lower_case_title=True,
            select_figures=select_figures, 
            only_show_sample_name_and_number=only_show_sample_name_and_number,
            show_rwp=show_rwp,
            xlim=xlim,
            ylim=ylim,
            no_bottom_ylim=no_bottom_ylim,
            show_titles= show_title,
            fully_custom_title=full_custom_title
            )
    data.show_plots()
    return data
def reload_ref():
    reload(ref)

