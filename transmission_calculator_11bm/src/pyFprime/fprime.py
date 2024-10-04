#!/usr/bin/env python

"""main Fprime routines
   Copyright: 2008, Robert B. Von Dreele (Argonne National Laboratory)
"""
import os
import math
import wx
import Element
import numpy as np
import matplotlib as mpl
import pylab
import sys

__version__ = '0.2.0'
# print versions
print ("Installed python module versions in use in pyFprime v.",__version__,":")
print ("python:     ",sys.version[:5])
print ("wxpython:   ",wx.__version__)
print ("matplotlib: ",mpl.__version__)
print ("numpy:      ",np.__version__)
print(wx.version())

def create(parent):
    return Fprime(parent)

[wxID_FPRIMECHOICE1, wxID_FPRIMECHOICE2, wxID_SPINTEXT1, wxID_SPINTEXT2,
 wxID_FPRIMERESULTS,wxID_FPRIMESLIDER1, wxID_SPINBUTTON,
] = [wx.NewId() for _init_ctrls in range(7)]

[wxID_FPRIMEEXIT, wxID_FPRIMEDELETE, wxID_FPRIMENEW, 
] = [wx.NewId() for _init_coll_FPRIME_Items in range(3)]

[wxID_FPRIMEKALPHAAGKA, wxID_FPRIMEKALPHACOKA, wxID_FPRIMEKALPHACRKA, 
 wxID_FPRIMEKALPHACUKA, wxID_FPRIMEKALPHAFEKA, wxID_FPRIMEKALPHAMNKA, 
 wxID_FPRIMEKALPHAMOKA, wxID_FPRIMEKALPHANIKA, wxID_FPRIMEKALPHAZNKA, 
] = [wx.NewId() for _init_coll_KALPHA_Items in range(9)]

[wxID_FPRIMEABOUT] = [wx.NewId() for _init_coll_ABOUT_Items in range(1)]

class Fprime(wx.Frame):
    ''' '''
    Elems = []
    Wave = 1.5405      #CuKa default
    Kev = 12.397639    #keV for 1A x-rays
    for arg in sys.argv:
        if '-w' in arg:
            Wave = float(arg.split('-w')[1])
        elif '-e' in arg:
            E = float(arg.split('-e')[1])
            Wave = Kev/E
        elif '-h' in arg:
            print( '''
fprime.py can take the following arguments:
-h   -  this help listing
-wv  -  set default wavelength to v, e.g. -w1.54 sets wavelength to 1.54A
-ev  -  set default energy to v, e.g. -e27 sets energy to 27keV
without arguments fprime uses CuKa as default (Wave=1.54052A, E=8.0478keV)
''')
            sys.exit()
    Wmin = 0.05        #wavelength range
    Wmax = 3.0
    Wres = 0.004094    #plot resolution step size as const delta-lam/lam - gives 1000 steps for Wmin to Wmax
    Eres = 1.5e-4      #typical energy resolution for synchrotron x-ray sources
    ffpfignum = 1
    fppfignum = 2
    Energy = Kev/Wave
    ifWave = True
    FFxaxis = 'S'      #default form factor plot is vs sin(theta)/lambda
    def _init_coll_ABOUT_Items(self, parent):

        parent.Append(wxID_FPRIMEABOUT, 'About')
        self.Bind(wx.EVT_MENU, self.OnABOUTItems0Menu, id=wxID_FPRIMEABOUT)

    def _init_coll_menuBar1_Menus(self, parent):

        parent.Append(menu=self.FPRIME, title='Fprime')
        parent.Append(menu=self.KALPHA, title='Kalpha')
        parent.Append(menu=self.ABOUT, title='About')

    def _init_coll_KALPHA_Items(self, parent):
        "Set of characteristic radiation from sealed tube sources"

        parent.Append(wxID_FPRIMEKALPHACRKA,'CrKa')
        parent.Append(wxID_FPRIMEKALPHAMNKA,'MnKa')
        parent.Append(wxID_FPRIMEKALPHAFEKA,'FeKa')
        parent.Append(wxID_FPRIMEKALPHACOKA,'CoKa')
        parent.Append(wxID_FPRIMEKALPHANIKA,'NiKa')
        parent.Append(wxID_FPRIMEKALPHACUKA,'CuKa')
        parent.Append(wxID_FPRIMEKALPHAZNKA,'ZnKa')
        parent.Append(wxID_FPRIMEKALPHAMOKA,'MoKa')
        parent.Append(wxID_FPRIMEKALPHAAGKA,'AgKa')
        self.Bind(wx.EVT_MENU, self.OnKALPHACrkaMenu, id=wxID_FPRIMEKALPHACRKA)
        self.Bind(wx.EVT_MENU, self.OnKALPHAMnkaMenu, id=wxID_FPRIMEKALPHAMNKA)
        self.Bind(wx.EVT_MENU, self.OnKALPHAFekaMenu, id=wxID_FPRIMEKALPHAFEKA)
        self.Bind(wx.EVT_MENU, self.OnKALPHACokaMenu, id=wxID_FPRIMEKALPHACOKA)
        self.Bind(wx.EVT_MENU, self.OnKALPHANikaMenu, id=wxID_FPRIMEKALPHANIKA)
        self.Bind(wx.EVT_MENU, self.OnKALPHACukaMenu, id=wxID_FPRIMEKALPHACUKA)
        self.Bind(wx.EVT_MENU, self.OnKALPHAZnkaMenu, id=wxID_FPRIMEKALPHAZNKA)
        self.Bind(wx.EVT_MENU, self.OnKALPHAMokaMenu, id=wxID_FPRIMEKALPHAMOKA)
        self.Bind(wx.EVT_MENU, self.OnKALPHAAgkaMenu, id=wxID_FPRIMEKALPHAAGKA)

    def _init_coll_FPRIME_Items(self, parent):
        parent.Append(wxID_FPRIMENEW,'&New Element','Add new element')
        self.Delete = parent.Append(wxID_FPRIMEDELETE,'&Delete Element','Delete an element')
        self.Delete.Enable(False)
        parent.Append(wxID_FPRIMEEXIT,'&Exit','Exit Fprime')
        self.Bind(wx.EVT_MENU, self.OnFPRIMEExitMenu, id=wxID_FPRIMEEXIT)
        self.Bind(wx.EVT_MENU, self.OnFPRIMENewMenu, id=wxID_FPRIMENEW)
        self.Bind(wx.EVT_MENU, self.OnFPRIMEDeleteMenu, id=wxID_FPRIMEDELETE)

    def _init_utils(self):
        self.FPRIME = wx.Menu(title='')

        self.KALPHA = wx.Menu(title='')
        self.KALPHA.SetEvtHandlerEnabled(True)

        self.ABOUT = wx.Menu(title='')

        self.menuBar1 = wx.MenuBar()

        self._init_coll_FPRIME_Items(self.FPRIME)
        self._init_coll_KALPHA_Items(self.KALPHA)
        self._init_coll_ABOUT_Items(self.ABOUT)
        self._init_coll_menuBar1_Menus(self.menuBar1)

    def _init_ctrls(self, parent):
        Gktheta = unichr(0x3b8)
        Gklambda = unichr(0x3bb)

        wx.Frame.__init__(self, parent=parent,
              size=wx.Size(500, 300),style=wx.DEFAULT_FRAME_STYLE, title='Fprime')              
        self._init_utils()
        self.SetMenuBar(self.menuBar1)
        panel = wx.Panel(self)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.Results = wx.TextCtrl( parent=panel,style=wx.TE_MULTILINE|wx.TE_DONTWRAP )
        self.Results.SetEditable(False)
        mainSizer.Add(self.Results,1,wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND)
        mainSizer.Add((10,15),0)

        selSizer = wx.BoxSizer(wx.HORIZONTAL)
        selSizer.Add((5,10),0)
        selSizer.Add(wx.StaticText(parent=panel, label='Wavelength:'),0,
            wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        selSizer.Add((5,10),0)
        self.SpinText1 = wx.TextCtrl(id=wxID_SPINTEXT1, parent=panel, 
              size=wx.Size(100,20), value = "%6.4f" % (self.Wave),style=wx.TE_PROCESS_ENTER )
        selSizer.Add(self.SpinText1,0)
        selSizer.Add((5,10),0)
        self.SpinText1.Bind(wx.EVT_TEXT_ENTER, self.OnSpinText1, id=wxID_SPINTEXT1)
        
        selSizer.Add(wx.StaticText(parent=panel, label='Energy:'),0,
            wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        selSizer.Add((5,10),0)
        self.SpinText2 = wx.TextCtrl(id=wxID_SPINTEXT2, parent=panel, 
              size=wx.Size(100,20), value = "%7.4f" % (self.Energy),style=wx.TE_PROCESS_ENTER) 
        selSizer.Add(self.SpinText2,0)
        self.SpinText2.Bind(wx.EVT_TEXT_ENTER, self.OnSpinText2, id=wxID_SPINTEXT2)
        mainSizer.Add(selSizer,0)
        mainSizer.Add((10,10),0)
        
        slideSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SpinButton = wx.SpinButton(id=wxID_SPINBUTTON, parent=panel, 
              size=wx.Size(25,24), style=wx.SP_VERTICAL | wx.SP_ARROW_KEYS)
        slideSizer.Add(self.SpinButton,0,wx.ALIGN_RIGHT)
        self.SpinButton.SetRange(int(10000.*self.Wmin),int(10000.*self.Wmax))
        self.SpinButton.SetValue(int(10000.*self.Wave))
        self.SpinButton.Bind(wx.EVT_SPIN, self.OnSpinButton, id=wxID_SPINBUTTON)

        self.slider1 = wx.Slider(id=wxID_FPRIMESLIDER1, maxValue=int(1000.*self.Wmax),
            minValue=int(1000.*self.Wmin), parent=panel,style=wx.SL_HORIZONTAL,
            value=int(self.Wave*1000.), )
        slideSizer.Add(self.slider1,1,wx.EXPAND|wx.ALIGN_RIGHT)
        self.slider1.Bind(wx.EVT_SLIDER, self.OnSlider1, id=wxID_FPRIMESLIDER1)
        mainSizer.Add(slideSizer,0,wx.EXPAND)
        mainSizer.Add((10,10),0)
        
        choiceSizer = wx.BoxSizer(wx.HORIZONTAL)
        choiceSizer.Add((5,10),0)
        choiceSizer.Add(wx.StaticText(parent=panel, label='Plot scales:'),
            0,wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        choiceSizer.Add((5,10),0)

        self.choice1 = wx.ComboBox(id=wxID_FPRIMECHOICE1, parent=panel, value='Wavelength',
             choices=['Wavelength','Energy'],style=wx.CB_READONLY|wx.CB_DROPDOWN)
        choiceSizer.Add(self.choice1,0)
        choiceSizer.Add((10,10),0)
        self.choice1.Bind(wx.EVT_COMBOBOX, self.OnChoice1, id=wxID_FPRIMECHOICE1)

        def OnChoice2(event):
            if event.GetString() == ' sin('+Gktheta+')/'+Gklambda:
                self.FFxaxis = 'S'
            elif event.GetString() == ' Q':
                self.FFxaxis = 'Q'
            else:
                self.FFxaxis = 'T'
            self.UpDateFPlot(self.Wave,rePlot=False)
            
        self.choice2 = wx.ComboBox(id=wxID_FPRIMECHOICE2, value=' sin('+Gktheta+')/'+Gklambda,
            choices=[' sin('+Gktheta+')/'+Gklambda,' 2'+Gktheta,' Q'],
            parent=panel, style=wx.CB_READONLY|wx.CB_DROPDOWN)
        choiceSizer.Add(self.choice2,0)
        self.choice2.Bind(wx.EVT_COMBOBOX, OnChoice2, id=wxID_FPRIMECHOICE2)
        mainSizer.Add(choiceSizer,0)
        mainSizer.Add((10,10),0)
        panel.SetSizer(mainSizer)

    def __init__(self, parent):
        self._init_ctrls(parent)
        mpl.rcParams['axes.grid'] = True
        mpl.rcParams['legend.fontsize'] = 10
        self.Bind(wx.EVT_CLOSE, self.ExitMain)
        self.Lines = []
        self.linePicked = None

    def ExitMain(self, event):
        sys.exit()
        
    def OnFPRIMEExitMenu(self, event):
        pylab.close('all')
        self.Close()

    def OnFPRIMENewMenu(self, event):
        ElList = []
        for Elem in self.Elems: ElList.append(Elem[0])
        PE = Element.PickElement(self,ElList)
        if PE.ShowModal() == wx.ID_OK:
            for El in PE.Elem:
                ElemSym = El.strip().upper()
                if ElemSym not in ElList:
                    FormFactors = Element.GetFormFactorCoeff(ElemSym)
                    for FormFac in FormFactors:
                        FormSym = FormFac['Symbol'].strip()
                        if FormSym == ElemSym:
                            Z = FormFac['Z']                #At. No.
                            Orbs = Element.GetXsectionCoeff(ElemSym)
                            Elem = (ElemSym,Z,FormFac,Orbs)
                    Fprime.Elems.append(Elem)
            self.Delete.Enable(True)
            self.CalcFPPS()
            self.SetWaveEnergy(self.Wave)
        PE.Destroy()
            
    def OnFPRIMEDeleteMenu(self, event):
        if len(self.Elems):
            ElList = []
            for Elem in self.Elems: ElList.append(Elem[0])
            S = []
            DE = Element.DeleteElement(self)
            if DE.ShowModal() == wx.ID_OK:
                El = DE.GetDeleteElement().strip().upper()
                for Elem in self.Elems:
                    if Elem[0] != El:
                        S.append(Elem)
                self.Elems = S
                self.CalcFPPS()
                if not self.Elems:
                    self.Delete.Enable(False)
                self.SetWaveEnergy(self.Wave)
        
    def OnKALPHACrkaMenu(self, event):
        self.SetWaveEnergy(2.28962)

    def OnKALPHAMnkaMenu(self, event):
        self.SetWaveEnergy(2.10174)

    def OnKALPHAFekaMenu(self, event):
        self.SetWaveEnergy(1.93597)

    def OnKALPHACokaMenu(self, event):
        self.SetWaveEnergy(1.78896)

    def OnKALPHANikaMenu(self, event):
        self.SetWaveEnergy(1.65784)

    def OnKALPHACukaMenu(self, event):
        self.SetWaveEnergy(1.54052)

    def OnKALPHAZnkaMenu(self, event):
        self.SetWaveEnergy(1.43510)

    def OnKALPHAMokaMenu(self, event):
        self.SetWaveEnergy(0.70926)

    def OnKALPHAAgkaMenu(self, event):
        self.SetWaveEnergy(0.55936)
        
    def OnSpinText1(self, event):
        self.SetWaveEnergy(float(self.SpinText1.GetValue()))
        
    def OnSpinText2(self, event):
        self.SetWaveEnergy(self.Kev/(float(self.SpinText2.GetValue())))
       
    def OnSpinButton(self, event):
        if self.ifWave:
            Wave = float(self.SpinButton.GetValue())/10000.
        else:
            Wave = self.Kev/(float(self.SpinButton.GetValue())/10000.)
        self.SetWaveEnergy(Wave)

    def OnSlider1(self, event):
        if self.ifWave:
            Wave = float(self.slider1.GetValue())/1000.
        else:
            Wave = self.Kev/(float(self.slider1.GetValue())/1000.)
        self.SetWaveEnergy(Wave)
        
    def UpDateFPlot(self,Wave,rePlot=True):
        """Plot f' & f" vs wavelength 0.05-3.0A"""
        "generate a set of form factor curves & plot them vs sin-theta/lambda or q or 2-theta"
        axylim = []
        bxylim = []
        try:
            self.fplot.canvas.set_window_title('X-Ray Resonant Scattering')
            if rePlot:
                asb,bsb = self.fplot.get_children()[1:]
                axylim = asb.get_xlim(),asb.get_ylim()
                bxylim = bsb.get_xlim(),bsb.get_ylim()
            newPlot = False
        except:
            self.fplot = pylab.figure(facecolor='white',figsize=(8,8))  #BTW: default figsize is (8,6)
            self.fplot.canvas.set_window_title('X-Ray Resonant Scattering')
            self.fplot.canvas.mpl_connect('pick_event', self.OnPick)
            self.fplot.canvas.mpl_connect('button_release_event', self.OnRelease)
            self.fplot.canvas.mpl_connect('motion_notify_event', self.OnMotion)
            newPlot = True
        ax = self.fplot.add_subplot(211)
        ax.clear()
        ax.set_title('Resonant Scattering Factors',x=0,ha='left')
        ax.set_ylabel("f ',"+' f ", e-',fontsize=14)
        Ymin = 0.0
        Ymax = 0.0
        colors=['r','b','g','c','m','k']
        if self.FPPS: 
            for i,Fpps in enumerate(self.FPPS):
                Color = colors[i%6]
                Ymin = min(Ymin,min(Fpps[2]),min(Fpps[3]))
                Ymax = max(Ymax,max(Fpps[2]),max(Fpps[3]))
                fppsP1 = np.array(Fpps[1])
                fppsP2 = np.array(Fpps[2])
                fppsP3 = np.array(Fpps[3])
                ax.plot(fppsP1,fppsP2,Color,label=Fpps[0]+" f '")
                ax.plot(fppsP1,fppsP3,Color,label=Fpps[0]+' f "')
        if self.ifWave: 
            ax.set_xlabel(r'$\mathsf{\lambda, \AA}$',fontsize=14)
            ax.axvline(x=Wave,picker=3,color='black')
        else:
            ax.set_xlabel(r'$\mathsf{E, keV}$',fontsize=14)
            ax.set_xscale('log')
            ax.axvline(x=self.Kev/Wave,picker=3,color='black')
        ax.set_ylim(Ymin,Ymax)
        if self.FPPS:
            legend = ax.legend(loc='best')
        bx = self.fplot.add_subplot(212)
        self.fplot.subplots_adjust(hspace=0.25)
        bx.clear()
        if self.ifWave:
            bx.set_title('%s%s%6.4f%s'%('Form factors (',r'$\lambda=$',self.Wave,r'$\AA)$'),x=0,ha='left')
        else:
            bx.set_title('%s%6.2f%s'%('Form factors  (E =',self.Energy,'keV)'),x=0,ha='left')
        if self.FFxaxis == 'S':
            bx.set_xlabel(r'$\mathsf{sin(\theta)/\lambda}$',fontsize=14)
        elif self.FFxaxis == 'T':
            bx.set_xlabel(r'$\mathsf{2\theta}$',fontsize=14)
        else:
            bx.set_xlabel(r'$Q, \AA$',fontsize=14)
        bx.set_ylabel("f+f ', e-",fontsize=14)
        E = self.Energy
        DE = E*self.Eres                         #smear by defined source resolution
        StlMax = min(2.0,math.sin(80.0*math.pi/180.)/Wave)
        Stl = pylab.arange(0.,StlMax,.01)
        Ymax = 0.0
        for i,Elem in enumerate(self.Elems):
            Els = Elem[0]
            Els = Els = Els.ljust(2).lower().capitalize()
            Ymax = max(Ymax,Elem[1])
            res1 = Element.FPcalc(Elem[3],E+DE)
            res2 = Element.FPcalc(Elem[3],E-DE)
            res = (res1[0]+res2[0])/2.0
            if Elem[1] > 78 and self.Energy > self.Kev/0.16: res = 0.0
            if Elem[1] > 94 and self.Energy < self.Kev/2.67: res = 0.0
            Els = Elem[0]
            Els = Els.ljust(2).lower().capitalize()
            X = []
            ff = []
            ffo = []
            for S in Stl: 
                ff.append(Element.ScatFac(Elem[2],S)+res)
                ffo.append(Element.ScatFac(Elem[2],S))
                if self.FFxaxis == 'S':
                    X.append(S)
                elif self.FFxaxis == 'T':
                    X.append(360.0*math.asin(S*self.Wave)/math.pi)
                else:
                    X.append(4.0*S*math.pi)
            Color = colors[i%6]
            Xp = np.array(X)
            ffop = np.array(ffo)
            ffp = np.array(ff)
            bx.plot(Xp,ffop,Color+'--',label=Els+" f")
            bx.plot(Xp,ffp,Color,label=Els+" f+f'")
        if self.Elems:
            legend = bx.legend(loc='best')
        bx.set_ylim(0.0,Ymax+1.0)
        
        if newPlot:
            newPlot = False
            pylab.show()
        else:
            if rePlot:
                tb = self.fplot.canvas.toolbar
                tb.push_current()
                ax.set_xlim(axylim[0])
                ax.set_ylim(axylim[1])
                axylim = []
                tb.push_current()
                bx.set_xlim(bxylim[0])
                bx.set_ylim(bxylim[1])
                bxylim = []
                tb.push_current()
            pylab.draw()
        
    def OnPick(self, event):
        self.linePicked = event.artist
        
    def OnMotion(self,event):
        if self.linePicked:
            xpos = event.xdata
            if xpos:
                if self.ifWave:
                    Wave = xpos
                else:
                    Wave = self.Kev/xpos               
                self.SetWaveEnergy(Wave)
                
    def OnRelease(self, event):
        if self.linePicked is None: return
        self.linePicked = None
        xpos = event.xdata
        if xpos:
            if self.ifWave:
                Wave = xpos
            else:
                Wave = self.Kev/xpos               
            self.SetWaveEnergy(Wave)
            

    def SetWaveEnergy(self,Wave):
        Gkmu = unichr(0x3bc)
        self.Wave = Wave
        self.Energy = self.Kev/self.Wave
        self.Energy = round(self.Energy,4)
        E = self.Energy
        DE = E*self.Eres                         #smear by defined source resolution
        self.SpinText1.SetValue("%6.4f" % (self.Wave))
        self.SpinText2.SetValue("%7.4f" % (self.Energy))
        self.SpinText1.Update()
        self.SpinText2.Update()
        if self.ifWave:
            self.slider1.SetValue(int(1000.*self.Wave))
            self.SpinButton.SetValue(int(10000.*self.Wave))
        else:
            self.slider1.SetValue(int(1000.*self.Energy))
            self.SpinButton.SetValue(int(10000.*self.Energy))
        Text = ''
        for Elem in self.Elems:
            r1 = Element.FPcalc(Elem[3],E+DE)
            r2 = Element.FPcalc(Elem[3],E-DE)
            Els = Elem[0]
            Els = Els.ljust(2).lower().capitalize()
            if Elem[1] > 78 and self.Energy+DE > self.Kev/0.16:
                Text += "%s\t%s%6s\t%s%6.3f  \t%s%10.2f %s\n" %    (
                    'Element= '+str(Els)," f'=",'not valid',
                    ' f"=',(r1[1]+r2[1])/2.0,' '+Gkmu+'=',(r1[2]+r2[2])/2.0,'barns/atom')
            elif Elem[1] > 94 and self.Energy-DE < self.Kev/2.67:
                Text += "%s\t%s%6s\t%s%6s\t%s%10s%s\n" %    (
                    'Element= '+str(Els)," f'=",'not valid',
                    ' f"=','not valid',' '+Gkmu+'=','not valid')
            else:
                Text += "%s\t%s%6.3f   \t%s%6.3f  \t%s%10.2f %s\n" %    (
                    'Element= '+str(Els)," f'=",(r1[0]+r2[0])/2.0,
                    ' f"=',(r1[1]+r2[1])/2.0,' '+Gkmu+'=',(r1[2]+r2[2])/2.0,'barns/atom')
        self.Results.SetValue(Text)
        self.Results.Update()
        self.UpDateFPlot(Wave)

    def CalcFPPS(self):
        """generate set of f' & f" curves for selected elements
           does constant delta-lambda/lambda steps over defined range
        """
        FPPS = []
        if self.Elems:
            wx.BeginBusyCursor()
            try:
                for Elem in self.Elems:
                    Els = Elem[0]
                    Els = Els = Els.ljust(2).lower().capitalize()
                    Wmin = self.Wmin
                    Wmax = self.Wmax
                    Z = Elem[1]
                    if Z > 78: Wmin = 0.16        #heavy element high energy failure of Cromer-Liberman
                    if Z > 94: Wmax = 2.67        #heavy element low energy failure of Cromer-Liberman
                    lWmin = math.log(Wmin)
                    N = int(round(math.log(Wmax/Wmin)/self.Wres))    #number of constant delta-lam/lam steps
                    I = range(N+1)
                    Ws = []
                    for i in I: Ws.append(math.exp(i*self.Wres+lWmin))
                    fps = []
                    fpps = []
                    Es = []
                    for W in Ws:
                        E = self.Kev/W
                        DE = E*self.Eres                         #smear by defined source resolution
                        res1 = Element.FPcalc(Elem[3],E+DE)
                        res2 = Element.FPcalc(Elem[3],E-DE)
                        fps.append((res1[0]+res2[0])/2.0)
                        fpps.append((res1[1]+res2[1])/2.0)
                        Es.append(E)
                    if self.ifWave:
                        Fpps = (Els,Ws,fps,fpps)
                    else:
                        Fpps = (Els,Es,fps,fpps)
                    FPPS.append(Fpps)
            finally:
                wx.EndBusyCursor()
        self.FPPS = FPPS

    def OnChoice1(self, event):
        if event.GetString() == "Wavelength":
            self.ifWave = True
            self.NewFPPlot = True
            self.Wave = round(self.Wave,4)
            self.slider1.SetRange(int(1000.*self.Wmin),int(1000.*self.Wmax))
            self.slider1.SetValue(int(1000.*self.Wave))
            self.SpinButton.SetRange(int(10000.*self.Wmin),int(10000.*self.Wmax))
            self.SpinButton.SetValue(int(10000.*self.Wave))
            self.SpinText1.SetValue("%6.4f" % (self.Wave))
            self.SpinText2.SetValue("%7.4f" % (self.Energy))
        else:
            self.ifWave = False
            self.NewFPPlot = True
            Emin = self.Kev/self.Wmax
            Emax = self.Kev/self.Wmin
            self.Energy = round(self.Energy,4)
            self.slider1.SetRange(int(1000.*Emin),int(1000.*Emax))
            self.slider1.SetValue(int(1000.*self.Energy))
            self.SpinButton.SetRange(int(10000.*Emin),int(10000.*Emax))
            self.SpinButton.SetValue(int(10000.*self.Energy))
            self.SpinText1.SetValue("%6.4f" % (self.Wave))
            self.SpinText2.SetValue("%7.4f" % (self.Energy))
        self.CalcFPPS()
        self.UpDateFPlot(self.Wave,rePlot=False)

    def OnABOUTItems0Menu(self, event):
        ''' '''
        info = wx.AboutDialogInfo()
        info.Name = 'pyFprime'
        info.Version = __version__
        info.Copyright = '''
Robert B. Von Dreele, 2008(C)
Argonne National Laboratory
This product includes software developed 
by the UChicago Argonne, LLC, as 
Operator of Argonne National Laboratory.        '''
        info.Description = '''
For calculating real and resonant X-ray scattering factors to 250keV;       
based on Fortran program of Cromer & Liberman corrected for 
Kissel & Pratt energy term; Jensen term not included
        '''
        wx.AboutBox(info)

class FprimeApp(wx.App):
    ''' '''
    def OnInit(self):
        self.main = Fprime(None)
        self.main.Show()
        self.SetTopWindow(self.main)
        self.main.OnFPRIMENewMenu(None)
        return True

def main():
    ''' '''
    application = FprimeApp(0)
    application.MainLoop()

if __name__ == '__main__':
    main()
