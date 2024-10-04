"""Element: functions for element types

   :copyright: 2008, Robert B. Von Dreele (Argonne National Laboratory)
"""

import wx
import math
import sys
import os.path
import wx.lib.colourselect as wscs
import wx.lib.buttons as wlb


ATMDATA_FILE = 'atmdata.dat'
XSECT_FILE = 'Xsect.dat'


def locate_distribution_file(name):
    '''locate a standard data file supplied in the distribution directory
    
    :return: full, absolute path to file, in this directory or None
    :rtype: str or None
    '''
    path = os.path.abspath( os.path.dirname(__file__) )
    filename = os.path.join(path, name)
    return {True: filename, False: None}[os.path.exists(filename)]


def GetFormFactorCoeff(El):
    """Read form factor coefficients from ``atmdata.dat`` file
    
    :param El: element 1-2 character symbol case irrevelant
    :return: FormFactors: list of form factor dictionaries
    
    each dictionary is::
    
    'Symbol':4 character element symbol with valence (e.g. 'NI+2')
    'Z': atomic number
    'fa': 4 A coefficients
    'fb': 4 B coefficients
    'fc': C coefficient 
    
    """
    ElS = El.upper()
    ElS = ElS.rjust(2)
    filename = locate_distribution_file(ATMDATA_FILE)
    try:
        FFdata = open(filename,'Ur')
    except:
        wx.MessageBox(message="Could not find or open file: %s" % filename,
            caption="No atmdata.dat file",style=wx.OK | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
        sys.exit()
    S = '1'
    FormFactors = []
    while S:
        S = FFdata.readline()
        if S[3:5] == ElS:
            if S[5:6] != '_' and S[8:9] == ' ':
                Z=int(S[:2])
                Symbol = S[3:7]
                S = S[12:]
                fa = (float(S[:7]),float(S[14:21]),float(S[28:35]),float(S[42:49]))
                fb = (float(S[7:14]),float(S[21:28]),float(S[35:42]),float(S[49:56]))
                FormFac = {'Symbol':Symbol,'Z':Z,'fa':fa,'fb':fb,'fc':float(S[56:63])}
                FormFactors.append(FormFac)               
    FFdata.close()
    return FormFactors
        
def GetAtomInfo(El):
    ''' :param str El: 2 character element symbol '''
    ElS = El.upper().rjust(2)
    filename = locate_distribution_file(ATMDATA_FILE)
    try:
        FFdata = open(filename,'Ur')
    except:
        wx.MessageBox(message="Could not find or open file: %s" % filename,
            caption="No atmdata.dat file",style=wx.OK | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP)
        sys.exit()
    S = '1'
    AtomInfo = {}
    Mass = []
    while S:
        S = FFdata.readline()
        if S[3:5] == ElS:
            if S[5:6] == '_':
                if not Mass:                                 #picks 1st one; natural abundance or 1st isotope
                    Mass = float(S[10:19])
                if S[5:9] == '_SIZ':
                    Z=int(S[:2])
                    Symbol = S[3:5].strip()
                    Drad = float(S[12:22])
                    Arad = float(S[22:32])
    FFdata.close()
    AtomInfo={'Symbol':Symbol,'Mass':Mass,'Z':Z,'Drad':Drad,'Arad':Arad}    
    return AtomInfo
      
def GetXsectionCoeff(El):
    """Read atom orbital scattering cross sections for fprime calculations via Cromer-Lieberman algorithm
    
    :param El: 2 character element symbol
    :return: Orbs: list of orbitals each a dictionary with detailed orbital information used by FPcalc
    
    each dictionary is::

        'OrbName': Orbital name read from file
        'IfBe' 0/2 depending on orbital
        'BindEn': binding energy
        'BB': BindEn/0.02721
        'XSectIP': 5 cross section inflection points
        'ElEterm': energy correction term
        'SEdge': absorption edge for orbital
        'Nval': 10/11 depending on IfBe
        'LEner': 10/11 values of log(energy)
        'LXSect': 10/11 values of log(cross section)

    """
    AU = 2.80022e+7
    C1 = 0.02721
    ElS = El.upper()
    ElS = ElS.ljust(2)
    filename = locate_distribution_file(XSECT_FILE)
    try:
        xsec = open(filename,'Ur')
    except:
        wx.MessageBox(message="Could not find or open file: %s" % filename,
            caption="No Xsect.dat file",style=wx.OK | wx.ICON_EXCLAMATION |wx.STAY_ON_TOP)
        sys.exit()
    S = '1'
    Orbs = []
    while S:
        S = xsec.readline()
        if S[:2] == ElS:
            S = S[:-1]+xsec.readline()[:-1]+xsec.readline()
            OrbName = S[9:14]
            S = S[14:]
            IfBe = int(S[0])
            S = S[1:]
            val = S.split()
            BindEn = float(val[0])
            BB = BindEn/C1
            Orb = {'OrbName':OrbName,'IfBe':IfBe,'BindEn':BindEn,'BB':BB}
            Energy = []
            XSect = []
            for i in range(11):
                Energy.append(float(val[2*i+1]))
                XSect.append(float(val[2*i+2]))
            XSecIP = []
            for i in range(5): XSecIP.append(XSect[i+5]/AU)
            Orb['XSecIP'] = XSecIP
            if IfBe == 0:
                Orb['SEdge'] = XSect[10]/AU
                Nval = 11
            else:
                Orb['ElEterm'] = XSect[10]
                del Energy[10]
                del XSect[10]
                Nval = 10
                Orb['SEdge'] = 0.0
            Orb['Nval'] = Nval
            D = dict(zip(Energy,XSect))
            Energy.sort()
            X = []
            for key in Energy:
                X.append(D[key])
            XSect = X
            LEner = []
            LXSect = []
            for i in range(Nval):
                LEner.append(math.log(Energy[i]))
                if XSect[i] > 0.0:
                    LXSect.append(math.log(XSect[i]))
                else:
                    LXSect.append(0.0)
            Orb['LEner'] = LEner
            Orb['LXSect'] = LXSect
            Orbs.append(Orb)
    xsec.close()
    return Orbs
    
def GetMagFormFacCoeff(El):
    """Read magnetic form factor data from atmdata.dat file
    
    :param str El: 2 character element symbol
    :return: MagFormFactors: list of all magnetic form factors dictionaries for element El.
    
    each dictionary contains::

        'Symbol':Symbol
        'Z':Z
        'mfa': 4 MA coefficients
        'nfa': 4 NA coefficients
        'mfb': 4 MB coefficients
        'nfb': 4 NB coefficients
        'mfc': MC coefficient
        'nfc': NC coefficient

    """
    ElS = El.upper()
    ElS = ElS.rjust(2)
    filename = locate_distribution_file(ATMDATA_FILE)
    try:
        FFdata = open(filename,'Ur')
    except:
        wx.MessageBox(message="Could not find or open file: %s" % filename,
            caption="No atmdata.dat file",style=wx.OK | wx.ICON_EXCLAMATION |wx.STAY_ON_TOP)
        sys.exit()
    S = '1'
    MagFormFactors = []
    while S:
        S = FFdata.readline()
        if S[3:5] == ElS:
            if S[8:9] == 'M':
                SN = FFdata.readline()               #'N' is assumed to follow 'M' in atmdata.dat
                Z=int(S[:2])
                Symbol = S[3:7]
                S = S[12:]
                SN = SN[12:]
                mfa = (float(S[:7]),float(S[14:21]),float(S[28:35]),float(S[42:49]))
                mfb = (float(S[7:14]),float(S[21:28]),float(S[35:42]),float(S[49:56]))
                nfa = (float(SN[:7]),float(SN[14:21]),float(SN[28:35]),float(SN[42:49]))
                nfb = (float(SN[7:14]),float(SN[21:28]),float(SN[35:42]),float(SN[49:56]))
                FormFac = {'Symbol':Symbol,'Z':Z,'mfa':mfa,'nfa':nfa,'mfb':mfb,'nfb':nfb,
                    'mfc':float(S[56:63]),'nfc':float(SN[56:63])}
                MagFormFactors.append(FormFac)
    FFdata.close()
    return MagFormFactors

def ScatFac(FormFac, SThL):
    """compute value of form factor
    
    :param dict FormFac: dictionary  defined in :meth:`GetFormFactorCoeff()` 
    :param float SThL: sin-theta/lambda
    :return: f: real part of form factor
    :rtype: float
    """
    f = FormFac['fc']
    fa = FormFac['fa']
    fb = FormFac['fb']
    for i in range(4):
        t = -fb[i]*SThL*SThL
        if t > -35.0: f += fa[i]*math.exp(t)
    return f
            
def FPcalc(Orbs, KEv):
    """
    Compute real & imaginary resonant X-ray scattering factors
    
    :param list Orbs: list of orbital dictionaries as defined in GetXsectionCoeff
    :param float KEv: x-ray energy in keV
    :return: C: (f',f",mu): real, imaginary parts of resonant scattering & atomic absorption coeff.
    """
    def Aitken(Orb, LKev):
        Nval = Orb['Nval']
        j = Nval-1
        LEner = Orb['LEner']
        for i in range(Nval):
            if LEner[i] <= LKev: j = i
        if j > Nval-3: j= Nval-3
        T = [0,0,0,0,0,0]
        LXSect = Orb['LXSect']
        for i in range(3):
           T[i] = LXSect[i+j]
           T[i+3] = LEner[i+j]-LKev
        T[1] = (T[0]*T[4]-T[1]*T[3])/(LEner[j+1]-LEner[j])
        T[2] = (T[0]*T[5]-T[2]*T[3])/(LEner[j+2]-LEner[j])
        T[2] = (T[1]*T[5]-T[2]*T[4])/(LEner[j+2]-LEner[j+1])
        C = T[2]
        return C
    
    def DGauss(Orb,CX,RX,ISig):
        ALG = (0.11846344252810,0.23931433524968,0.284444444444,
        0.23931433524968,0.11846344252810)
        XLG = (0.04691007703067,0.23076534494716,0.5,
        0.76923465505284,0.95308992296933)
        
        D = 0.0
        B2 = Orb['BB']**2
        R2 = RX**2
        XSecIP = Orb['XSecIP']
        for i in range(5):
            X = XLG[i]
            X2 = X**2
            XS = XSecIP[i]
            if ISig == 0:
                S = BB*(XS*(B2/X2)-CX*R2)/(R2*X2-B2)
            elif ISig == 1:
                S = 0.5*BB*B2*XS/(math.sqrt(X)*(R2*X2-X*B2))
            elif ISig == 2:
                T = X*X2*R2-B2/X
                S = 2.0*BB*(XS*B2/(T*X2**2)-(CX*R2/T))
            else:
                S = BB*B2*(XS-Orb['SEdge']*X2)/(R2*X2**2-X2*B2)
            A = ALG[i]
            D += A*S
        return D 
    
    AU = 2.80022e+7
    C1 = 0.02721
    C = 137.0367
    FP = 0.0
    FPP = 0.0
    Mu = 0.0
    LKev = math.log(KEv)
    RX = KEv/C1
    if Orbs:
        for Orb in Orbs:
            CX = 0.0
            BB = Orb['BB']
            BindEn = Orb['BindEn']
            if Orb['IfBe'] != 0: ElEterm = Orb['ElEterm']
            if BindEn <= KEv:
                CX = math.exp(Aitken(Orb,LKev))
                Mu += CX
                CX /= AU
            Corr = 0.0
            if Orb['IfBe'] == 0 and BindEn >= KEv:
                CX = 0.0
                FPI = DGauss(Orb,CX,RX,3)
                Corr = 0.5*Orb['SEdge']*BB**2*math.log((RX-BB)/(-RX-BB))/RX
            else:
                FPI = DGauss(Orb,CX,RX,Orb['IfBe'])
                if CX != 0.0: Corr = -0.5*CX*RX*math.log((RX+BB)/(RX-BB))
            FPI = (FPI+Corr)*C/(2.0*math.pi**2)
            FPPI = C*CX*RX/(4.0*math.pi)
            FP += FPI
            FPP += FPPI
        FP -= ElEterm
    
    return (FP, FPP, Mu)
    

class PickElement(wx.Dialog):
    """Makes periodic table widget for picking element - caller maintains element list"""
    Elem = []
    def _init_ctrls(self, prnt,list):
        wx.Dialog.__init__(self, id=-1, name='PickElement',
              parent=prnt, pos=wx.DefaultPosition, size=wx.Size(580, 360),
              style=wx.DEFAULT_DIALOG_STYLE, title='Pick Element')
        panel = wx.Panel(self)
        
        REcolor = wx.Colour(128, 128, 255)
        Metcolor = wx.Colour(192, 192, 192)
        Noblecolor = wx.Colour(255, 128, 255)
        Alkcolor = wx.Colour(255, 255, 128)
        AlkEcolor = wx.Colour(255, 128, 0)
        SemMetcolor = wx.Colour(128, 255, 0)
        NonMetcolor = wx.Colour(0, 255, 255)
        White = wx.Colour(255, 255, 255)
        self.Elem = []
        for El in list:
            self.Elem.append(El.lower().capitalize())

        
        self.ElTable = [
            ("H",   0,0, "Hydrogen",    White,           0.0000),
            ("He", 17,0, "Helium",      Noblecolor,      0.0000),
            ("Li",  0,1, "Lithium",     Alkcolor,        0.0004),
            ("Be",  1,1, "Beryllium",   AlkEcolor,       0.0006),
            ("B",  12,1, "Boron",       NonMetcolor,     0.0012),
            ("C",  13,1, "Carbon",      NonMetcolor,     0.0018),
            ("N",  14,1, "Nitrogen",    NonMetcolor,     0.0030),
            ("O",  15,1, "Oxygen",      NonMetcolor,     0.0042),
            ("F",  16,1, "Fluorine",    NonMetcolor,     0.0054),
            ("Ne", 17,1, "Neon",        Noblecolor,      0.0066),
            ("Na",  0,2, "Sodium",      Alkcolor,        0.0084),
            ("Mg",  1,2, "Magnesium",   AlkEcolor,       0.0110),
            ("Al", 12,2, "Aluminum",    SemMetcolor,     0.0125),
            ("Si", 13,2, "Silicon",     NonMetcolor,     0.0158),
            ("P",  14,2, "Phosphorus",  NonMetcolor,     0.0180),
            ("S",  15,2, "Sulphur",     NonMetcolor,     0.0210),
            ("Cl", 16,2, "Chlorine",    NonMetcolor,     0.0250),
            ("Ar", 17,2, "Argon",       Noblecolor,      0.0285),
            ("K",   0,3, "Potassium",   Alkcolor,        0.0320),
            ("Ca",  1,3, "Calcium",     AlkEcolor,       0.0362),
            ("Sc",  2,3, "Scandium",    Metcolor,        0.0410),
            ("Ti",  3,3, "Titanium",    Metcolor,        0.0460),
            ("V",   4,3, "Vanadium",    Metcolor,        0.0510),
            ("Cr",  5,3, "Chromium",    Metcolor,        0.0560),
            ("Mn",  6,3, "Manganese",   Metcolor,        0.0616),
            ("Fe",  7,3, "Iron",        Metcolor,        0.0680),
            ("Co",  8,3, "Cobalt",      Metcolor,        0.0740),
            ("Ni",  9,3, "Nickel",      Metcolor,        0.0815),
            ("Cu", 10,3, "Copper",      Metcolor,        0.0878),
            ("Zn", 11,3, "Zinc",        Metcolor,        0.0960),
            ("Ga", 12,3, "Gallium",     SemMetcolor,      0.104),
            ("Ge", 13,3, "Germanium",   SemMetcolor,      0.114),
            ("As", 14,3, "Arsenic",     NonMetcolor,      0.120),
            ("Se", 15,3, "Selenium",    NonMetcolor,      0.132),
            ("Br", 16,3, "Bromine",     NonMetcolor,      0.141),
            ("Kr", 17,3, "Krypton",     Noblecolor,       0.150),
            ("Rb",  0,4, "Rubidium",    Alkcolor,         0.159),
            ("Sr",  1,4, "Strontium",   AlkEcolor,        0.171),
            ("Y",   2,4, "Yittrium",    Metcolor,         0.180),
            ("Zr",  3,4, "Zirconium",   Metcolor,         0.192),
            ("Nb",  4,4, "Niobium",     Metcolor,         0.204),
            ("Mo",  5,4, "Molybdenium", Metcolor,         0.216),
            ("Tc",  6,4, "Technetium",  Metcolor,         0.228),
            ("Ru",  7,4, "Ruthenium",   Metcolor,         0.246),
            ("Rh",  8,4, "Rhodium",     Metcolor,         0.258),
            ("Pd",  9,4, "Palladium",   Metcolor,         0.270),
            ("Ag", 10,4, "Silver",      Metcolor,         0.285),
            ("Cd", 11,4, "Cadmium",     Metcolor,         0.300),
            ("In", 12,4, "Indium",      SemMetcolor,      0.318),
            ("Sn", 13,4, "Tin",         SemMetcolor,      0.330),
            ("Sb", 14,4, "Antimony",    SemMetcolor,      0.348),
            ("Te", 15,4, "Tellurium",   NonMetcolor,      0.363),
            ("I",  16,4, "Iodine",      NonMetcolor,      0.384),
            ("Xe", 17,4, "Xenon",       Noblecolor,       0.396),
            ("Cs",  0,5, "Caesium",     Alkcolor,         0.414),
            ("Ba",  1,5, "Barium",      AlkEcolor,        0.438),
            ("La",  2,5, "Lanthanium",  Metcolor,         0.456),
            ("Ce",  3.5,6.5, "Cerium",      REcolor,      0.474),
            ("Pr",  4.5,6.5, "Praseodymium",REcolor,      0.492),
            ("Nd",  5.5,6.5, "Neodymium",   REcolor,      0.516),
            ("Pm",  6.5,6.5, "Promethium",  REcolor,      0.534),
            ("Sm",  7.5,6.5, "Samarium",    REcolor,      0.558),
            ("Eu",  8.5,6.5, "Europium",    REcolor,      0.582),
            ("Gd",  9.5,6.5, "Gadolinium",  REcolor,      0.610),
            ("Tb", 10.5,6.5, "Terbium",     REcolor,      0.624),
            ("Dy", 11.5,6.5, "Dysprosium",  REcolor,      0.648),
            ("Ho", 12.5,6.5, "Holmium",     REcolor,      0.672),
            ("Er", 13.5,6.5, "Erbium",      REcolor,      0.696),
            ("Tm", 14.5,6.5, "Thulium",     REcolor,      0.723),
            ("Yb", 15.5,6.5, "Ytterbium",   REcolor,      0.750),
            ("Lu", 16.5,6.5, "Lutetium",    REcolor,      0.780),
            ("Hf",  3,5, "Hafnium",     Metcolor,         0.804),
            ("Ta",  4,5, "Tantalum",    Metcolor,         0.834),
            ("W",   5,5, "Tungsten",    Metcolor,         0.864),
            ("Re",  6,5, "Rhenium",     Metcolor,         0.900),
            ("Os",  7,5, "Osmium",      Metcolor,         0.919),
            ("Ir",  8,5, "Iridium",     Metcolor,         0.948),
            ("Pt",  9,5, "Platinium",   Metcolor,         0.984),
            ("Au", 10,5, "Gold",        Metcolor,         1.014),
            ("Hg", 11,5, "Mercury",     Metcolor,         1.046),
            ("Tl", 12,5, "Thallium",    SemMetcolor,      1.080),
            ("Pb", 13,5, "Lead",        SemMetcolor,      1.116),
            ("Bi", 14,5, "Bismuth",     SemMetcolor,      1.149),
            ("Po", 15,5, "Polonium",    SemMetcolor,      1.189),
            ("At", 16,5, "Astatine",    NonMetcolor,      1.224),
            ("Rn", 17,5, "Radon",       Noblecolor,       1.260),
            ("Fr",  0,6, "Francium",    Alkcolor,         1.296),
            ("Ra",  1,6, "Radium",      AlkEcolor,        1.332),
            ("Ac",  2,6, "Actinium",    Metcolor,         1.374),
            ("Th",  3.5,7.5, "Thorium",     REcolor,      1.416),
            ("Pa",  4.5,7.5, "Protactinium",REcolor,      1.458),
            ("U",   5.5,7.5, "Uranium",     REcolor,      1.470),
            ("Np",  6.5,7.5, "Neptunium",   REcolor,      1.536),
            ("Pu",  7.5,7.5, "Plutonium",   REcolor,      1.584),
            ("Am",  8.5,7.5, "Americium",   REcolor,      1.626),
            ("Cm",  9.5,7.5, "Curium",      REcolor,      1.669),
            ("Bk", 10.5,7.5, "Berkelium",   REcolor,      1.716),
            ("Cf", 11.5,7.5, "Californium", REcolor,      1.764)]
            
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        elPanel = wx.Panel(panel)
            
        i=0
        for E in self.ElTable:
            PickElement.ElButton(self,parent=elPanel,name=E[0],
                pos=wx.Point(E[1]*30+20,E[2]*30+25),tip=E[3],color=E[4])
            i+=1
        mainSizer.Add(elPanel,0,wx.EXPAND)
        mainSizer.Add((10,10),0)
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        OkBtn = wx.Button(panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(panel,-1,"Cancel")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM, 10)
        panel.SetSizer(mainSizer)
        panel.Fit()
                 
    def OnOk(self,event):
        if self.Elem:
            self.EndModal(wx.ID_OK)
        else:        
            self.EndModal(wx.ID_CANCEL)        
        
    def OnCancel(self,event):
        self.EndModal(wx.ID_CANCEL)        

    def __init__(self, parent,list):
        self._init_ctrls(parent,list)
        
    def ElButton(self, parent, name, pos, tip, color):
        Black = wx.Colour(0,0,0)
        if name in self.Elem:
            color = Black
        El = wscs.ColourSelect(label=name, parent=parent,colour=color,
            pos=pos, size=wx.Size(32, 32), style=wx.RAISED_BORDER)
        El.SetBackgroundColour(color)
        El.SetLabel(name)
        El.Bind(wx.EVT_BUTTON, self.OnElButton)

    def OnElButton(self, event):
        Black = wx.Colour(0,0,0)
        btn = event.GetEventObject()
        El = btn.GetLabel()
        if btn.GetColour() != Black:
            for Elem in self.ElTable:
                if El in Elem:
                    ElColor = Elem[4]
            if El in self.Elem:
                btn.SetColour(ElColor)
                self.Elem.remove(El)
            else:
                btn.SetColour(wx.Colour(255,0,0))
                self.Elem.append(El)
        
class DeleteElement(wx.Dialog):
    """Delete element from selected set widget"""
    def _init_ctrls(self, parent):
        l = len(DeleteElement.Elems)-1
        wx.Dialog.__init__(self, id=-1, name='Delete', parent=parent,
              pos=wx.DefaultPosition, size=wx.Size(max(128,64+l*24), 87),
              style=wx.DEFAULT_DIALOG_STYLE, title='Delete Element')
        self.SetAutoLayout(True)
        self.SetHelpText('Select element to delete')
        self.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
        self.CentreOnParent(wx.BOTH)

        i = 0
        Elem = []
        for Elem in DeleteElement.Elems:
            name = Elem[0].lower().capitalize()
            self.ElButton(id=-1,name=name,pos=wx.Point(16+i*24, 16))
            i+=1
              
    def __init__(self, parent):
        DeleteElement.Elems = parent.Elems
        DeleteElement.El = ' '
        self._init_ctrls(parent)

    def ElButton(self, id, name, pos):
        White = wx.Colour(255, 255, 255)
        El = wscs.ColourSelect(label=name, parent=self, colour = White,
            pos=pos, size=wx.Size(24, 23), style=wx.RAISED_BORDER)
        El.Bind(wx.EVT_BUTTON, self.OnDeleteButton)
    
    def OnDeleteButton(self, event):
        DeleteElement.El=event.GetEventObject().GetLabel()
        self.EndModal(wx.ID_OK)
        
    def GetDeleteElement(self):
        return DeleteElement.El
        

