import os
python_tools_path = os.path.dirname(os.path.realpath(__file__))
working_dir = os.getcwd()
os.chdir(python_tools_path) #This changes to the python tools directory. 
inp_template_dir = python_tools_path + '/BVO_Rietveld'
os.chdir('../BiVO4_Work/CaWO4_Enumeration/output/Fixed_Output')
cif_directory = os.getcwd()
print('python tools path: {}\n working dir: {}\n inp template dir: {}\n cif dir: {}'.format(python_tools_path,
    working_dir,
    inp_template_dir,
    cif_directory))

