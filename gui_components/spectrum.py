"""
Raman Spectrum Analysis Tools (Biomod)
Dahlia Dry, 2022 | dahlia23@mit.edu
Physical Optics and Electronics Group
This file defines an class Spectrum and associated helper functions which can be used to analyze Raman data
"""
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import scipy.signal
import base64
import io
import json
from BaselineRemoval import BaselineRemoval
from sys import platform

class Spectrum(object):
    def __init__(self,data,power,log,meta,ref,noise):
        self.power= power
        self.data = data
        self.data['Spectrum'] = [np.array(x) for x in self.data['Spectrum']]
        self.data['Wavelength'] =np.array(self.data['Wavelength'])
        self.data['Raman_Shift'] =np.array(self.data['Raman_Shift'])
        self.log= log
        self.meta = meta
        self.ref =np.array(ref)
        self.noise =np.array(noise)
    def initlog(self):
        self.log='**Spectrum for ' + self.meta['filename'] + ' ('+self.meta['label']+')**      \n      Measurement Date: ' + self.meta['starttime'] + \
                    '       \n      Excitation Wavelength: ' + str(self.meta['excitation_wavelength']) + ' nm' + \
                    '       \n      Acquisition Time: '+str(self.meta['acquisition_time'])+ ' s' + \
                    '       \n      Sampling Interval: ' + str(self.meta['interval']) + '       \n'
        return self.log
    def meta(self):
        try:
            m =eval(json.loads(str(self.metajson)))
        except:
            m =json.loads(self.metajson)
        if type(m)!=dict:
            m= dict((a.strip(), b.strip())
                     for a, b in (element.split(': ')
                                  for element in m[1:-1].replace("\"","").replace("'","").split(', ')))
        return m
    def get_noise(self):
        return self.noise
    def edit_meta(self,key,value):
        self.meta[key] = value
    def power_normalize(self,weights=None):
        if weights is None:
            weights = [self.data['Avg_Power'][i] / max(self.data['Avg_Power']) for i in range(len(self.data['Avg_Power']))]
        for i in range(len(self.data['Spectrum'])):
            self.data['Spectrum'][i] = [x/weights[i] for x in self.data['Spectrum'][i]]
        self.ref = np.mean(np.array(self.data['Spectrum']),axis=0) #across cols
        self.noise= np.std(np.array(self.data['Spectrum']),axis=0) #across cols
    def cosmicray_medfilt(self):
        spec_arr = np.array([self.data['Spectrum'][i] for i in range(len(self.data['Spectrum']))])
        for j in range(len(spec_arr[0])):
            spec_arr[:,j] = scipy.signal.medfilt(spec_arr[:,j]) #default kernel size 3, same as matlab
        for i in range(len(self.data['Spectrum'])):
            self.data['Spectrum'][i] = spec_arr[i]
        self.ref = np.mean(np.array(self.data['Spectrum']),axis=0) #across cols
        self.noise= np.std(np.array(self.data['Spectrum']),axis=0) #across cols
    def savitsky_golay(self,window=11,degree=0):
        for i in range(len(self.data['Spectrum'])):
            self.data['Spectrum'][i]=scipy.signal.savgol_filter(self.data['Spectrum'][i],window,degree)
        self.ref = np.mean(np.array(self.data['Spectrum']),axis=0) #across cols
        self.noise= np.std(np.array(self.data['Spectrum']),axis=0) #across cols
    def lieber_baseline(self,order,maxiter,cutoff_wl=None):
        if cutoff_wl is not None:
            pass #figure this out
        for i in range(len(self.data['Spectrum'])):
            baseObj=BaselineRemoval(self.data['Spectrum'][i])
            Modpoly_output=baseObj.ModPoly(degree=6,repitition=200)
            self.data['Spectrum'][i] = Modpoly_output
        self.ref = np.mean(np.array(self.data['Spectrum']),axis=0) #across cols
        self.noise= np.std(np.array(self.data['Spectrum']),axis=0) #across cols
    def subtract_spec(self,spec):
        self.ref = self.ref-spec.ref
        self.noise=np.sqrt((self.noise)**2 + (spec.noise)**2)
    def get_local_max(self,selected_point,radius=5):
        center_index= (np.abs(self.data['Raman_Shift']-selected_point[0])).argmin()
        if radius != 0:
            return (self.data['Raman_Shift'][center_index],np.max(self.ref[center_index-radius:center_index+radius])),center_index
        else:
            return (self.data['Raman_Shift'][center_index],self.ref[center_index]),center_index
    def rescale(self,norm,weight):
        self.ref = self.ref*weight/norm[1]
        self.noise=self.noise*weight/norm[1]
    def plot(self,color=None,label='label',mode='lines',wavelength=False,solo=False,show=False):
        if wavelength:
            xaxis='Wavelength (nm)'
            xlabel = 'Wavelength'
        else:
            xaxis ='Raman Shift (cm^-1)'
            xlabel = 'Raman_Shift'
        #df = pd.DataFrame({'xdata':self.data[xlabel],'ydata':self.ref})
        #df.to_csv('spectrum.csv')
        if solo:
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=self.data[xlabel],y=self.ref,mode=mode,
                            line=dict(color=color),name=self.meta[label]))
            fig.update_layout(title=self.meta[label],xaxis_title=xaxis,yaxis_title='Count')
        else:
            if color is not None:
                fig=go.Scatter(x=self.data[xlabel],y=self.ref,mode=mode,
                                line=dict(color=color),name=self.meta[label])
            else:
                fig=go.Scatter(x=self.data[xlabel],y=self.ref,mode=mode,
                                name=self.meta[label])
        if show:
            fig.show()
        return fig
    def plot_all_traces(self,wavelength=False,show=False):
        if wavelength:
            xaxis='Wavelength (nm)'
            xlabel = 'Wavelength'
        else:
            xaxis ='Raman Shift (cm^-1)'
            xlabel = 'Raman_Shift'
        fig=go.Figure()
        for i in range(len(self.data['Spectrum'])):
            fig.add_trace(go.Scatter(x=self.data[xlabel],y=self.data['Spectrum'][i],mode='lines',
                                    name=self.meta['label']))
        fig.update_layout(title=self.meta['label'],xaxis_title=xaxis,yaxis_title='Count',showlegend=False)
        if show:
            fig.show()
        return fig

def biomod_spec_from_upload(contents,filename,label):
    meta={}
    meta['filename'] = filename
    meta['label'] = label
    meta['target_raman_shift'] =1049
    meta['meas_raman_shift'] =1033
    meta['pbuffer']=0
    meta['acquisition_time']=10
    meta['excitation_wavelength']=830
    meta['starttime']=''
    meta['interval']=1
    meta['concentration']=0
    s_content_type,s_content_string=contents['spec'].split(',')
    s_decoded = base64.b64decode(s_content_string)
    p_content_type,p_content_string=contents['power'].split(',')
    p_decoded=base64.b64decode(p_content_string)
    fspec = io.StringIO(s_decoded.decode('utf-8'))
    fpower = io.StringIO(p_decoded.decode('utf-8'))
    for i in range(14):
        line = fpower.readline()
        if i ==11:
            meta['excitation_wavelength']=line.split(',')[1].strip().split(' ')[0] #nm
        elif i ==4:
            meta['starttime'] = line.split(',')[1]
        elif i ==5:
            meta['interval']=line.split(',')[1]
    pixels=fspec.readline().strip().split('\t')[2:]
    wavelengths=fspec.readline().strip().split('\t')[2:]
    target_lambda = 1/(1/float(meta['excitation_wavelength']) - meta['target_raman_shift']/1e7) #nm
    meas_lambda = 1/(1/float(meta['excitation_wavelength']) - meta['meas_raman_shift']/1e7) # nm
    lambda_calib = target_lambda-meas_lambda
    calib_wavelengths = [float(x) + lambda_calib for x in wavelengths]
    data = {'Wavelength':wavelengths,
                'Raman_Shift':[(1/float(meta['excitation_wavelength'])-1/x)*1e7 for x in calib_wavelengths], #in cm^-1
                'Spectrum':[],
                'Avg_Power':[]}
    fspec.readline() #discard line
    power=pd.read_csv(fpower)
    p=meta['pbuffer']
    for line in fspec:
        spec= line.strip().split('\t')[2:]
        assert (len(spec) == len(pixels) ==len(wavelengths)),"length of spectrum"+len(data['Spectrum'])+1+"!= length of pixels or number of wavelengths"
        avg_power = sum(power['Power (W)'][p:p+meta['acquisition_time']])/meta['acquisition_time']
        p=p+meta['acquisition_time']
        data['Spectrum'].append(np.array([float(s) for s in spec]))
        data['Avg_Power'].append(avg_power)
    log ='**Spectrum for ' + filename + ' ('+label+')**      \n      Measurement Date: ' + meta['starttime'] + \
                '       \n      Excitation Wavelength: ' + str(meta['excitation_wavelength']) +' nm'+ \
                '       \n      Acquisition Time: '+str(meta['acquisition_time'])+ ' s'+ \
                '       \n      Sampling Interval: ' + meta['interval'] + '       \n'
    ref=np.mean(np.array(data['Spectrum']),axis=0) #across cols
    noise= np.std(np.array(data['Spectrum']),axis=0) #across cols
    return Spectrum(data,power.to_dict(orient='list'),log,meta,ref,noise)

def spec_from_file(filename, label, meta=None):
    if meta is None:
        meta={}
        meta['filename'] = filename
        meta['label'] = label
        meta['target_raman_shift'] =1049
        meta['meas_raman_shift'] =1033
        meta['pbuffer']=0
        meta['acquisition_time']=10
        meta['excitation_wavelength']=830
        meta['starttime']=''
        meta['interval']=1
        meta['concentration']=0
    fspec = open(filename+'.txt') #infer from filepath without extension
    try:
        fpower = open(filename+'.csv')
    except:
        fpower=None
    else:
        for i in range(14):
            line = fpower.readline()
            if i ==11:
                meta['excitation_wavelength']=line.split(',')[1].strip().split(' ')[0] #nm
            elif i ==4:
                meta['starttime'] = line.split(',')[1]
            elif i ==5:
                meta['interval']=line.split(',')[1]
    pixels=fspec.readline().strip().split('\t')[2:]
    wavelengths=fspec.readline().strip().split('\t')[2:]
    target_lambda = 1/(1/float(meta['excitation_wavelength']) - meta['target_raman_shift']/1e7) #nm
    meas_lambda = 1/(1/float(meta['excitation_wavelength']) - meta['meas_raman_shift']/1e7) # nm
    lambda_calib = target_lambda-meas_lambda
    calib_wavelengths = [float(x) + lambda_calib for x in wavelengths]
    data = {'Wavelength':[float(x) for x in wavelengths],
                'Raman_Shift':[(1/float(meta['excitation_wavelength'])-1/x)*1e7 for x in calib_wavelengths], #in cm^-1
                'Spectrum':[],
                'Avg_Power':[]}
    fspec.readline() #discard extra line
    if fpower is not None:
        power=pd.read_csv(fpower)
    p=meta['pbuffer']
    for line in fspec:
        spec= line.strip().split('\t')[2:]
        assert (len(spec) == len(pixels) ==len(wavelengths)),"length of spectrum"+len(data['Spectrum'])+1+"!= length of pixels or number of wavelengths"
        data['Spectrum'].append(np.array([float(s) for s in spec]))
        if fpower is not None:
            avg_power = sum(power['Power (W)'][p:p+meta['acquisition_time']])/meta['acquisition_time']
            p=p+meta['acquisition_time']
            data['Avg_Power'].append(avg_power)
    log ='**Spectrum for ' + filename + ' ('+label+')**      \n      Measurement Date: ' + str(meta['starttime']) + \
                '       \n      Excitation Wavelength: ' + str(meta['excitation_wavelength']) + \
                '       \n      Acquisition Time: '+str(meta['acquisition_time'])+ \
                '       \n      Sampling Interval: ' + str(meta['interval']) + '       \n'
    ref=np.mean(np.array(data['Spectrum']),axis=0) #across cols
    noise= np.std(np.array(data['Spectrum']),axis=0) #across cols
    if fpower is not None:
        return Spectrum(data,power.to_dict(orient='list'),log,meta,ref,noise)
    else:
        return Spectrum(data,None,log,meta,ref,noise)

def spec_from_json(json_spectra,multiple_spad=False):
    spectra_raw= json.loads(json_spectra)
    #print(spectra_raw)
    spectra = []
    buf=[]
    if multiple_spad:
        for exp in spectra_raw:
            for s in exp:
                #print(s.keys())
                buf.append(Spectrum(s['data'],
                                        s['power'],
                                        s['log'],
                                        s['meta'],
                                        s['ref'],
                                        s['noise']))
            spectra.append(buf)
            buf=[]
    else:
        for s in spectra_raw:
            #print(s.keys())
            spectra.append(Spectrum(s['data'],
                                    s['power'],
                                    s['log'],
                                    s['meta'],
                                    s['ref'],
                                    s['noise']))
    return spectra

def jsonify(spectra):
    dictlist = []
    buf=[]
    for spec in spectra:
        objdict=  spec.__dict__
        objdict['data']['Spectrum'] = [x.tolist() for x in objdict['data']['Spectrum']]
        objdict['data']['Raman_Shift']=objdict['data']['Raman_Shift'].tolist()
        objdict['data']['Wavelength']=objdict['data']['Wavelength'].tolist()
        objdict['ref'] = objdict['ref'].tolist()
        objdict['noise']=objdict['noise'].tolist()
        dictlist.append(objdict)
    return json.dumps(dictlist)