"""
Biomod Raman Dash App
Dahlia Dry, 2022 | dahlia23@mit.edu
Physical Optics and Electronics Group
Running this file launches the Dash GUI for Biomod Raman data analysis
"""
#file imports
from gui_components.spectrum import *
from gui_components.gui_layout import *
#package imports
import dash
from dash import callback_context
import pandas as pd
import numpy as np
from dash.dependencies import Input,Output,State
from dash_extensions.enrich import MultiplexerTransform,DashProxy
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from scipy import stats

#_______________________________________________________________________________
#INITIALIZE VARIABLES___________________________________________________________
fontawesome="https://maxcdn.bootstrapcdn.com/font-awesome/4.4.0/css/font-awesome.min.css"
app = DashProxy(__name__,prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                external_stylesheets=[dbc.themes.BOOTSTRAP,fontawesome],
                suppress_callback_exceptions=True)
mathjax = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
app.scripts.append_script({ 'external_url' : mathjax })
buffer='      \n'
#LAYOUT_________________________________________________________________________
#create a dynamic layout that wipes global variables when page is reloaded
def app_layout():
    print('redefining app layout')
    structure=html.Div([
                html.H1('Biomod Raman Spectra Analysis',style={'padding':10}),
                html.A(html.Button([html.I(className="fa fa-github fa-5x"), ""],
                            style={'position':'fixed','right':10,'top':0,
                                    'border':'none','border-radius':12,'font-size':14,
                                    }),
                        href="https://github.com/Dahlia-Dry/RLE-Biomod-Raman",
                        target='_blank',
                        id="github",
                        title="Documentation here"),
        html.Div(id='page-content',children=tab)
    ])
    return structure
app.layout = app_layout

#HELPER FUNCTIONS________________________________________________________________
def preprocess_biomod(s):
    s.power_normalize()
    s.cosmicray_medfilt()
    s.savitsky_golay()
    s.log = s.log + ' - Applied preprocessing routine      \n'
    return s

def batch_process_uploads(list_of_contents,list_of_names,list_of_dates):
    spectra = []
    paths = [x.split('.')[0] for x in list_of_names]
    contentdict = {key:{'spec':None,'power':None} for key in list(set(paths))}
    for i in range(len(list_of_names)):
        if list_of_names[i].endswith('.txt'):
            contentdict[list_of_names[i].split('.')[0]]['spec']=list_of_contents[i]
        elif list_of_names[i].endswith('.csv'):
            contentdict[list_of_names[i].split('.')[0]]['power']=list_of_contents[i]
        else:
            raise Exception('unrecognized file extension:'+list_of_names[i])
    for key in list(contentdict.keys()):
        if None in contentdict[key]:
            raise Exception(key + 'lacks either a spec file or a power file')
        else:
            spec =biomod_spec_from_upload(contentdict[key],key,key.split('/')[-1])
            spectra.append(spec)
    return spectra

def closest_point(selected_point,x,y):
    msx = selected_point[0]
    msy = selected_point[1]
    dist = np.sqrt((np.array(x)-msx)**2 + (np.array(y)-msy)**2)
    return np.argmin(dist)

#DATA ANALYSIS CALLBACKS________________________________________________________
@app.callback([Output('file-list', 'data'),
                Output('file-list','style_data_conditional'),
              Output('spectra','children'),
              Output('log','children')],
              Input('upload-data', 'contents'),
              [State('upload-data', 'filename'),
              State('upload-data', 'last_modified')])
def show_files(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        #gen spectra from scratch
        spectra = batch_process_uploads(list_of_contents,list_of_names,list_of_dates)
        data=[{'Name':s.meta['filename'],
            'Nspec':len(s.data['Spectrum']),
            'Time(s)':s.meta['acquisition_time'],
            'Label':s.meta['label'],
            'Concentration':s.meta['concentration']} for s in spectra]
        #do preprocessing
        for i in range(len(spectra)):
            spectra[i] = preprocess_biomod(spectra[i])
        logstr = '\n'.join([x.log + \
            '\n________________________________________________________________' for x in spectra])
        #print(pd.Series(spectra).to_json(orient='records'))
        style_data_conditional = [
        {
            'if': {
                'row_index': i,
            },
            'color': colorlist[i]
        } for i in range(len(data))
        ]
        return data,style_data_conditional,jsonify(spectra),logstr

@app.callback([Output('spectra','children'),
                Output('log','children'),
                Output('graphnum','children')],
              [Input('file-list','data'),
              Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
              State('upload-data', 'last_modified')])
def update_spectra_source(rows,list_of_contents,list_of_names,list_of_dates): #re-init the spectra if changes to datatable occur
    spectra = batch_process_uploads(list_of_contents,list_of_names,list_of_dates)
    df = pd.DataFrame(rows)
    matched = []
    for i in range(len(df)):
        index = -1
        for j in range(len(spectra)):
            if spectra[j].meta['filename'] == df['Name'].iloc[i]:
                index=j
                matched.append(spectra[j])
                break
        if index==-1:
            #raise Exception('row filename does not match any spectra filenames')
            continue
        spectra[j].edit_meta('label',df['Label'].iloc[i])
        spectra[j].edit_meta('acquisition_time',int(df['Time(s)'].iloc[i]))
        spectra[j].edit_meta('concentration',(df['Concentration'].iloc[i]))
    spectra = [s for s in spectra if s in matched] #remove entires deleted by user from table
    #do preprocessing
    for i in range(len(spectra)):
        spectra[i].initlog()
        spectra[i] = preprocess_biomod(spectra[i])
    logstr = '\n'.join([x.log + \
        '\n________________________________________________________________' for x in spectra])
    return jsonify(spectra),logstr,'0'

@app.callback(Output('graphnum','children'),
            [Input('forward','n_clicks'),
            Input('back','n_clicks')],
            State('graphnum','children'))
def update_graphnum(forward,back,graphnum):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    g =int(str(graphnum).strip())
    if 'forward' in changed_id:
        g=g+1
    elif 'back' in changed_id:
        g = g-1
    return str(g)

@app.callback(Output('current','figure'),
                [Input('spectra','children'),
                Input('graphnum','children'),
                Input('current','clickData')])
def update_current(json_spectra,graphnum,clickData):
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger=None
    else:
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    spectra = spec_from_json(json_spectra)
    g =int(graphnum.strip()) % len(spectra)
    color=colorlist[g]
    #print(g,color)
    mode='lines'
    fig = spectra[g].plot(color=color,solo=True,mode=mode)
    if clickData is not None and trigger=='current':
        selected_point = [clickData['points'][0]['x'],clickData['points'][0]['y']]
        fig.add_trace(go.Scatter(x=[selected_point[0]],y=[selected_point[1]],marker_symbol='x',line=dict(color='#000000'),
                                name='selected point'))
        fig.update_layout(showlegend=False)
    return fig

@app.callback(Output('working','figure'),
                [Input('spectra','children'),
                Input('all-spec','n_clicks'),
                Input('working','clickData')])
def update_working(json_spectra,spec_clicks,clickData):
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger=None
    else:
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    spectra = spec_from_json(json_spectra)
    fig=go.Figure()
    for i in range(len(spectra)):
        color=colorlist[i]
        mode='lines'
        fig.add_trace(spectra[i].plot(color=color,mode=mode))
    if clickData is not None and trigger=='working':
        selected_point = [clickData['points'][0]['x'],clickData['points'][0]['y']]
        fig.add_shape(type="line",
                    x0=selected_point[0],x1=selected_point[0],
                    y0=0,y1=np.max(np.array([x.ref for x in spectra])),
                    line=dict(dash='dot',color="#000000"))
    fig.update_layout(title='Combined Spectra',xaxis_title='Raman Shift (cm^-1)',yaxis_title='Count')
    return fig

@app.callback(
    [Output('spectra','children'),
    Output('log','children')],
    [Input('lieber','n_clicks')],
    State('spectra','children')
)
def implement_lieber_baseline(lieber_clicks,json_spectra):
    spectra = spec_from_json(json_spectra)
    for i in range(len(spectra)):
        spectra[i].lieber_baseline(order=6,maxiter=200,cutoff_wl=400)
        spectra[i].log=spectra[i].log + ' - Applied lieber fit      \n'
    logstr = '\n'.join([x.log + \
        '\n________________________________________________________________' for x in spectra])
    return jsonify(spectra),logstr

@app.callback([Output('spectra','children'),
                Output('log','children')],
                [Input('subtract','n_clicks')],
                [State('graphnum','children'),
                State('spectra','children')])
def implement_subtraction(subtract_clicks,graphnum,json_spectra):
    spectra = spec_from_json(json_spectra)
    spec_index = int(str(graphnum).strip())% len(spectra)
    for i in range(len(spectra)):
        if i != spec_index:
            spectra[i].subtract_spec(spectra[spec_index])
            spectra[i].log=spectra[i].log + ' - Applied subtraction of '+spectra[spec_index].meta['label']+'      \n'
    logstr = '\n'.join([x.log + \
        '\n________________________________________________________________' for x in spectra])
    return jsonify(spectra),logstr

@app.callback([Output('spectra','children'),
                Output('log','children')],
                [Input('norm','n_clicks')],
                [State('graphnum','children'),
                State('current','clickData'),
                State('spectra','children')])
def implement_max_peak_normalize(norm,graphnum,clickData,json_spectra):
    spectra = spec_from_json(json_spectra)
    spec_index = int(str(graphnum).strip())% len(spectra)
    selected_point = [clickData['points'][0]['x'],clickData['points'][0]['y']]
    max_peak,max_index = spectra[spec_index].get_local_max(selected_point)
    for i in range(len(spectra)):
        weight = max_peak[1]/spectra[i].ref[max_index]
        spectra[i].rescale(max_peak,weight)
        spectra[i].log=spectra[i].log + ' - Normalized to max peak ('+"%.2f ,%.2f" %(max_peak[0],max_peak[1])+') of '+spectra[spec_index].meta['label']+'(x'+"%.5f" %(weight)+')      \n'
    logstr = '\n'.join([x.log + \
        '\n________________________________________________________________' for x in spectra])
    return jsonify(spectra),logstr

@app.callback([Output('working','figure'),
               Output('log','children')],
              [Input('lod','n_clicks')],
              [State('working','clickData'),
               State('spectra','children')])
def do_lod(lod_clicks,clickData,json_spectra):
    spectra = spec_from_json(json_spectra)
    selected_point = [clickData['points'][0]['x'],clickData['points'][0]['y']]
    max_peak,max_index = spectra[0].get_local_max(selected_point) #theoretically should all have same max_index, radius=0 to get exact point
    raman = spectra[0].data['Raman_Shift'][max_index]
    try:
        concentrations = np.array([float(x.meta['concentration']) for x in spectra])
    except:
        raise TypeError("all concentration values must be integer or float")
    refs = np.array([x.ref[max_index] for x in spectra])
    noise = np.array([x.noise[max_index] for x in spectra])
    sy = np.mean(noise)
    fig=go.Figure(data=go.Scatter(x=concentrations,y=refs,
                                  error_y=dict(
                                            type='data',
                                            array=noise,
                                            visible=True
                                  ),mode='markers'))
    res=stats.linregress(concentrations,refs)
    fig.add_trace(go.Scatter(x=concentrations,y=concentrations*res.slope+res.intercept,mode='lines',
                            hovertemplate='<i>y = %.5f * x + %.5f</i><br>'%(res.slope,res.intercept)+\
                                            '<b>R^2 </b>= %.3f' %(res.rvalue**2)))
    print(sy,res.slope,res.intercept)
    lod =(3*sy+np.min(refs)-res.intercept)/res.slope
    print(lod,np.min(refs),np.max(refs))
    fig.add_shape(type="line",
                x0=lod,x1=lod,
                y0=np.min(refs),y1=np.max(refs),
                line=dict(dash='dot',color="#000000"))
    fig.update_layout(title = "LOD Concentration for " + "%.2f" %(raman) + " Raman Peak is "+ "%.4f" %(lod)+ "ppm",
                        xaxis_title = "Concentration (ppm)",
                        yaxis_title = "Signal",showlegend=False)
    logstr = '\n'.join([x.log + \
        '\n________________________________________________________________' for x in spectra])
    logstr = logstr+'\n' + "LOD Concentration for " + "%.2f" %(raman) + " Raman Peak is "+ "%.4f" %(lod)+ "ppm      \n"
    logstr = logstr + 'y = %.5f * x + %.5f'%(res.slope,res.intercept) + '      \n'
    logstr = logstr + 'r-squared = ' + str(res.rvalue**2) + '      \n'
    logstr = logstr + '\n________________________________________________________________'
    return fig,logstr


#RUN APP_______________________________________________________________________
if __name__ == '__main__':
    app.run_server()
