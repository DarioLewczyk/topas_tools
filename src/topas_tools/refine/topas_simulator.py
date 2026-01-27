# Authorship: {{{
''' 
Written by: Dario C. Lewczyk
Date: 01/27/26
'''
#}}}
# imports: {{{
import numpy as np
import random
import copy
from shutil import copyfile
#}}}
# FakeTOPAS: {{{
class FakeTOPAS:
    '''
    A lightweight simulator to mimic the behavior of TOPAS during refinements
    It modifies values in an inp/out dictionary and writes a Dummy.out file 
    '''
    def __init__(self, noise = 0.1):
        self.noise = noise # Relative noise applied to values
    # _perturb: {{{
    def _perturb(self, value):
        if value is None:
            return None
        return value * (1 + random.uniform(-self.noise, self.noise))
    #}}}
    # simulate: {{{
    def simulate(self, 
            lines, 
            inp_dict, 
            out_filename = 'Dummy.out',
            output_xy:str = None,
            ):
        ''' 
        lines: These are the lines from the inp file you read in
        inp_dict: the dictionary with all your inp stuff
        out_filename: The name of the .out file made
        '''

        # Working copy of lines:
        new_lines = copy.deepcopy(lines)
        # 1. Phases: {{{
        for ph, params in inp_dict.items():
            if not ph.startswith('Ph'):
                continue
            with open(f'{ph}_cry.out', 'w') as f:
                f.write('CRY LINES')
            for var, entry in params.items():
                ln = entry['linenumber']
                old_line = new_lines[ln]

                val = entry.get('value')
                err = entry.get('error')

                new_val = self._perturb(val)
                new_err = self._perturb(err) if err is not None else None

                updated = old_line
                if val is not None:
                    updated = updated.replace(str(val), f"{new_val:.8g}", 1)
                if err is not None:
                    updated = updated.replace(str(err), f'{new_err:.8g}', 1)
                new_lines[ln] = updated
        #}}}
        # 2. Specimen Displacement: {{{
        sd = inp_dict.get('Specimen_Displacement')
        if sd:
            ln = sd['linenumber']
            old_line = new_lines[ln]

            val = sd.get('value')
            err = sd.get('error')

            new_val = self._perturb(val)
            new_err = self._perturb(err) if err is not None else None

            updated = old_line.replace(str(val), f'{new_val:.8g}', 1)
            if err is not None:
                updated = updated.replace(str(err), f'{new_err:.8g}',1)

            new_lines[ln] = updated
        #}}}
        # 3. Modify background: {{{
        bkg = inp_dict.get("bkg")
        if bkg:
            ln = bkg["linenumber"]
            old_line = new_lines[ln]

            # Reconstruct the bkg line with perturbed values
            new_terms = []
            for term in bkg["terms"]:
                v = self._perturb(term["value"])
                e = self._perturb(term["error"]) if term["error"] else None
                if e is not None:
                    new_terms.append(f"{v:.8g}`_{e:.8g}")
                else:
                    new_terms.append(f"{v:.8g}")

            new_line = "bkg @ " + " ".join(new_terms)
            new_lines[ln] = new_line

        #}}}
        # 4. Add fake fit metrics: {{{
        metrics = (
            f"r_exp  {random.uniform(1,5):.6f} "
            f"r_wp   {random.uniform(2,10):.6f} "
            f"gof    {random.uniform(0.5,3):.6f}"
        )
        new_lines.append("\n")
        new_lines.append(metrics + "\n")
        #}}}
        # 5. Write Dummy.out: {{{
        with open(out_filename, 'w') as f:
            for line in new_lines:
                f.write(line if line.endswith('\n') else line + '\n') 
        #}}}
        # 6. If an output_xy, need to make the file: {{{
        if output_xy is not None:
            with open(f'{output_xy}.xy', 'w') as f:
                f.write('XY')
        #}}}

                
    #}}}
#}}}
