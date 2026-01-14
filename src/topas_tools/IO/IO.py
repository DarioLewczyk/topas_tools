# Authorship: {{{
''' 
Dario C. Lewczyk
Date: 10_02_25
'''
#}}}
# Imports: {{{
import os
import numpy as np
import pandas as pd
#}}}

# export_xy_with_hkl:{{{
def export_xy_with_hkl(idx:int = None, rietveld_data:dict =None, excel_dir:str = None, fn:str = None):
    home = os.getcwd()
    try:
        os.chdir(excel_dir)
    except:
        os.mkdir(excel_dir)
        os.chdir(excel_dir)
        
    entry = rietveld_data[idx]
    time = str(np.around(entry['corrected_time']/60, 2)).replace('.','p')
    fn = f'{fn}_{time}_min'
    xy = entry['xy']
    hkli = entry['hkli']
    
    tth, yobs, ycalc, ydiff = (xy['2theta'], xy['yobs'], xy['ycalc'], xy['ydiff'])
    
    df_labels = [f'tth_{fn}', f'yobs_{fn}', f'ycalc_{fn}', f'ydiff_{fn}']
    
    hkli_df_labels = []
    hkli_df_entries = []
    df_data = [tth, yobs, ycalc, ydiff]
    
    for i, struct in hkli.items():
        
        try:
            sub = struct['substance'] # Get the substance name.
        except:
            break
        
        hkli_entry = struct['hkli']
        
        hkl_labels = [str(h).replace(',','_') for h in hkli_entry['hkl']] # list of hkl tuples
        hkl_tth = hkli_entry['tth']
        
        df_data.append(hkl_labels)
        df_data.append(hkl_tth)
        df_data.append(np.ones_like(hkl_tth))
        df_labels.extend([f'hkl_{sub}_{fn}', f'hkl_tth_{sub}_{fn}', f'hkl_Is_{sub}_{fn}'])
        

    df = pd.DataFrame(df_data, index=df_labels).T
    with pd.ExcelWriter(f'{fn}.xlsx') as writer:
        df.to_excel(writer, index = False, )
    print(f'{fn}.xlsx written to:\n\t{excel_dir}')
    os.chdir(home)
    return df
    
            
            

#}}}
