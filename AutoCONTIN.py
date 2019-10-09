import os
import numpy as np
import matplotlib.pyplot as plt
from CONTINWrapper import runCONTINfit

class autoContin:

    def __init__(self, filename, filetype='brookhaven dat file', full_auto=False, rename=False, addTimeStamp=True):
        # set the program folder as working folder, and use absolute path for data file !
        contin_path = os.path.dirname(__file__)
        os.chdir(contin_path)

        filepath = os.path.abspath(filename)  # convert to absolute path
        dirname, fname = os.path.split(filepath)
        self.dir = dirname

        if filetype == 'brookhaven dat file':

            self.readBrookhavenRawFile(filepath)

            # rename raw file with sample ID (+ date + time)
            if rename:  
                oldname = os.path.join(self.dir, fname)
                
                # add time stamp to avoid duplication of name
                if addTimeStamp:
                    newfname = '{}_{}{}_{}{}.dat'.format(
                        self.sampleInfo['SampleID'],
                        self.sampleInfo['Date'].split('/')[0],
                        self.sampleInfo['Date'].split('/')[1],
                        self.sampleInfo['Time'].split(':')[0],
                        self.sampleInfo['Time'].split(':')[1]
                    )
                    newname = os.path.join(self.dir, newfname)
                else:
                    newname = os.path.join(self.dir, self.sampleInfo['SampleID']+'.dat')
                self.fname = newname
                os.rename(oldname, newname)
            else:
                self.fname = fname

            self.calcCtau()
            if full_auto:
                self.doCONTIN()
                self.readCONTINOutput()
                self.calcRhDistribution()
                self.plotCONTINReport(show=False, save=True)


    def readBrookhavenRawFile(self, filename):
        '''
        read params and data from .dat raw file generated by Brookhaven BI-200SM light scattering instrument
        '''

        with open(filename, 'r') as f:
            alldata = list(f.readlines())
        self.sampleInfo = {
            'SampleID': alldata[-4][:-1],
            'OperatorID': alldata[-3][:-1],
            'Date': alldata[-2][:-1],
            'Time': alldata[-1][:-1]
        }
        self.testParams = {
            'First Delay': float(alldata[5][:-1]), # in microseconds
            'Last Delay': float(alldata[23][:-1]), # in microseconds
            'Time Unit': 'microsecond',
            'Angles': float(alldata[8][:-1]), # in degree
            'Wavelength': float(alldata[9][:-1]), # in nanometer
            'Temperature': float(alldata[10][:-1]), # in degrees Kelvin
            'Viscosity': float(alldata[11][:-1]), # in centipoise
            'Refractive index of liquid': float(alldata[13][:-1]),
            'Refractive index of particle, real part': float(alldata[14][:-1]),
            'Refractive index of particle, imaginary part': float(alldata[14][:-1]),
            'Calculated Baseline': float(alldata[21][:-1]),
            'Measured Baseline': float(alldata[22][:-1])
        }
        
        #load raw correlation function (G2)
        G2_list = []
        for line in alldata[37:-4]:
            if ',' in line:
                temp = line.strip().split(', ') # for new version of Brookhaven dls software
            else:
                temp = line.split() # for old version of Brookhaven dls software
            G2_list.append([float(temp[0]), float(temp[1])])
        self.G2 = np.array(G2_list)
    

    def calcCtau(self, baseline='Measured Baseline'):
        '''
        # C(tau) is the normalized raw correlation function
        # C(tau) = G2(tau)/Baseline - 1 = beta * exp(-2*gamma*tau) = beta * g1(tau)**2
        '''

        B = self.testParams[baseline]
        self.Ctau = np.zeros_like(self.G2)
        self.Ctau[:,0] = self.G2[:,0]
        self.Ctau[:,1] = self.G2[:,1] /B - 1
    

    def doCONTIN(self, gamma_min=1, gamma_max=1E6):
        '''
        run CONTIN program using module pyCONTIN
        generate an input file and an output file
        pyCONTIN: https://github.com/kanhua/pyCONTIN
        '''

        # genetate paramTemplate file for pyCONTIN module
        content = '''  TEST DATA SET 1 (inverse laplace transform)                             
LAST,,1        
GMNMX,1,{}                                             
GMNMX,2,{}                                                
IWT,,1                                                
NERFIT,,0                                                
NINTT,,-1
NLINF,,1
IFORMY,,(1E11.4)
IFORMT,,(1E11.4)                                                                  
DOUSNQ,,1                                                
IUSER,10,2                                                
RUSER,10,-1
NONNEG,,1'''.format(str(gamma_min), str(gamma_max))
        with open('paramTemplate.txt', 'w') as f:
            f.write(content)
        self.paramTemplateFile = 'paramTemplate.txt'
        if self.testParams['Time Unit'] == 'microsecond':
            xdata = self.Ctau[:,0] * 1e-6  # in CONTIN, unit of delay time is sec
            ydata = self.Ctau[:,1]
        
        runCONTINfit(xdata, ydata, self.paramTemplateFile)
        self.CONTINOutputFile = 'CONTINOutput.txt'
        
    
    def readCONTINOutput(self):
        '''
        read CONTIN's output file and obtain chosen solution
        '''

        with open(self.CONTINOutputFile, 'r') as f:
            lastpage = '' # last page in CONTIN output is the chosen solution by CONTIN
            begin = False
            for line in f.readlines():
                if 'CHOSEN SOLUTION' in line:
                    begin = True
                if begin:
                    lastpage += line
        self.chosenSolutionPage = lastpage

        lastpage_list = lastpage.split('\n')

        # read the fitting data
        fitdata_list = []
        data_begin_index = -1
        data_end_index = -1
        for i in range(len(lastpage_list)):
            line = lastpage_list[i]
            if 'FIT VALUES' in line:
                data_begin_index = i+3
            elif data_begin_index > 0 and i > data_begin_index and 'CHOSEN SOLUTION' in line:
                data_end_index = i - 1
                break
        for line in lastpage_list[data_begin_index: data_end_index+1]:
            y = float(line.strip().split()[0])**2  # because Ctau data is 2gamma
            x = float(line.strip().split()[1].rstrip('X').rstrip('O')) * 1e6  # change the unit to microsecond
            fitdata_list.append([x, y])
        self.fitdata = np.array(fitdata_list)

        # read the gamma distribution and peak info
        gammaDis_list = []
        peakinfo = ''
        data_begin = False
        data_end = False
        peak_begin = False
        for line in lastpage_list:
            if 'LINEAR COEFFICIENTS' in line:
                data_end = True
                peak_begin = True

            if data_begin and not data_end:
                lst = line.rstrip().split()
                x = float('.'.join(lst[2].split('X')[0].split('.')[:2])) # read x value from this line, a little bit complicated...
                y = float(lst[0])
                error = float(lst[1].replace('D', 'E'))
                gammaDis_list.append([x, y, error])                
            elif peak_begin:
                peakinfo += line + '\n'

            if 'ORDINATE' in line and 'ERROR' in line and 'ABSCISSA' in line:
                data_begin = True #next line of this line is data
        
        self.gammaDistribution = np.array(gammaDis_list)
        #self.gammaDistribution[:,0] = self.gammaDistribution[:,0] / 2
        self.peakinfo = peakinfo

    def calcRhDistribution(self):
        '''
        calculate Rh distribution function and calculate Rh value for each peak
        then save Rh file including these info
        '''

        kb = 1.38064852e-23  # Boltzmann Constant
        # all params normalized to SI
        angle = self.testParams['Angles'] / 180 * np.pi  # in rads
        wavelength = self.testParams['Wavelength'] * 1e-9 # in meter
        n = self.testParams['Refractive index of liquid']
        T = self.testParams['Temperature']
        mu = self.testParams['Viscosity'] * 1e-3  # in Ps.s
        q = 4 * np.pi * n * np.sin(angle/2) / wavelength
        D = self.gammaDistribution[:,0] / q**2
        Rh = (kb * T) / (6 * np.pi * mu * D)  # in meter

        Rh = Rh * 1e9 # convert to nanometer
        gammaGgamma = self.gammaDistribution[:,0] * self.gammaDistribution[:,1]

        self.RhDistribution = np.vstack((Rh, gammaGgamma)).T
        self._calcRhPeakValues()
        self._saveRhDistribution()


    def _saveRhDistribution(self):
            headertxt = 'Rh distribution data\n\n'
            headertxt += 'Rh peak values (nm)\n'
            for i in range(len(self.RhPeakValues)):
                headertxt += 'Rh peak {} = {}\n'.format(str(i+1), self.RhPeakValues[i])
            headertxt += '\nRh\tgamma*G(gamma)'
            fname = os.path.join(self.dir, self.fname[:-4] + '_Rh.txt')
            np.savetxt(fname, self.RhDistribution, header=headertxt, delimiter='\t')

    def _calcRhPeakValues(self):
        '''
        calculate all Rh peak values from CONTIN output
        '''

        peakinfo_list = self.peakinfo.split('\n')
        peakBeginIndex_list = []
        N = 1
        for i in range(len(peakinfo_list)):
            if 'PEAK '+ str(N) in peakinfo_list[i]:
                peakBeginIndex_list.append(i)
                N += 1
            elif peakinfo_list[i] == '':
                end = i - 1
                break
        peakEndIndex_list = [k-1 for k in peakBeginIndex_list[1:]]
        peakEndIndex_list.append(end)

        linewidth_list = []
        for i in range(len(peakBeginIndex_list)):
            for fullline in peakinfo_list[peakBeginIndex_list[i]+1: peakEndIndex_list[i]+1]:
                line = fullline.strip()
                if line[:2] != '-1' and line[-1] == '1':
                    linewidth = float(line.split()[-3])
                    linewidth_list.append(linewidth)
                    break
        
        self.RhPeakValues = [self._calcRhValue(l) for l in linewidth_list]
        return self.RhPeakValues


    def _calcRhValue(self, linewidth):
        '''
        calculate 1 Rh value for a given linewith
        '''

        kb = 1.38064852e-23  # Boltzmann Constant
        angle = self.testParams['Angles'] / 180 * np.pi  # in rads
        wavelength = self.testParams['Wavelength'] * 1e-9 # in meter
        n = self.testParams['Refractive index of liquid']
        T = self.testParams['Temperature']  # in Kelvin
        mu = self.testParams['Viscosity'] * 1e-3  # in Ps.s
        q = 4 * np.pi * n * np.sin(angle/2) / wavelength

        DivisionFunc = (q**2 * kb * T) / (6 * np.pi * mu)  # in meter
        DivisionFunc = DivisionFunc * 1e9  # in nanometer
        Rh = DivisionFunc / linewidth
        return Rh


    def plotDistribution(self, type='Rh'):
        figure = plt.figure()
        ax = plt.subplot(111)
        ax.set_xscale("log", nonposx='clip')

        if type == 'gamma':
            plt.plot(self.gammaDistribution[:,0], self.gammaDistribution[:,1], '.-', label='gamma distribution')
            plt.xlabel('gamma')
            plt.ylabel('G(gamma)')
        elif type == 'Rh':
            plt.plot(self.RhDistribution[:,0], self.RhDistribution[:,1], '.-', label='Rh distribution')
            plt.xlabel('Rh/nm')
            plt.ylabel('gamma*G(gamma)')

        plt.show()


    def plotFitData(self):
        figure = plt.figure()
        ax = plt.subplot(111)
        ax.set_xscale("log", nonposx='clip')
        plt.plot(self.Ctau[:,0], self.Ctau[:,1], 'o')
        plt.plot(self.fitdata[:,0], self.fitdata[:,1], '-')
        plt.xlabel('tau / ms')
        plt.show()
        
    
    def plotCONTINReport(self, save=True, show=False):
        '''
        give a report of CONTIN result
        including fitting of correlation function and Rh distribution with Rh values
        '''

        figure = plt.figure(figsize=plt.figaspect(1.))  # adjust aspect ratio of the whole figure
        plt.subplots_adjust(hspace=0.5)  # adjust the space between subplots

        plt.suptitle('{} at {} {}'.format(self.sampleInfo['SampleID'], self.sampleInfo['Date'], self.sampleInfo['Time']))

        ax1 = plt.subplot(211)
        ax1.set_xscale("log", nonposx='clip')
        ax1.plot(self.Ctau[:,0], self.Ctau[:,1], 'o')
        ax1.plot(self.fitdata[:,0], self.fitdata[:,1], '-')
        plt.xlabel('τ/ms')
        plt.ylabel('C(τ)')
        plt.title('Correlation Function')

        ax2 = plt.subplot(212)
        ax2.set_xscale("log", nonposx='clip')
        ax2.plot(self.RhDistribution[:,0], self.RhDistribution[:,1], '.-', label='Rh distribution')
        plt.ylim((-0.05, max(self.RhDistribution[:,1])+0.2))
        plt.title('Rh Distribution')
        plt.xlabel('Rh/nm')
        plt.ylabel('Γ*G(Γ)')
        for p in self.RhPeakValues:
            n = 0
            distance = abs(self.RhDistribution[0,0] - p)
            for i in range(len(self.RhDistribution)):
                if abs(self.RhDistribution[i,0] - p) < distance:
                    distance = abs(self.RhDistribution[i,0] - p)
                    n = i
            x_pos = self.RhDistribution[n, 0]
            y_pos = self.RhDistribution[n, 1] + 0.05
            ax2.text(x_pos, y_pos, '{:.2f}nm'.format(p), ha='center')

        if save:
            fname = os.path.join(self.dir, self.fname[:-4] + '_Report.png')
            plt.savefig(fname, dpi=300)
        if show:
            plt.show()


if __name__ == "__main__":
    test = autoContin('test_data/PW9-n-propyl.dat')
    test.doCONTIN()
    test.readCONTINOutput()
    test.calcRhDistribution()
    test.plotCONTINReport(show=True, save=True)
    #test.plotDistribution(type='Rh')