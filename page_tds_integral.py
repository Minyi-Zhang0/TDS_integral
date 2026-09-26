import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def read_time_metadata(file_obj, encoding="cp1252"):
    file_obj.seek(0)
    df = pd.read_csv(
        file_obj,
        sep="\t",
        nrows=1,      
        encoding=encoding,
    )

    file_obj.seek(0)
    df_raw = pd.read_csv(
        file_obj,
        sep="\t",
        skiprows=4,
        header=0,
        encoding=encoding,
    )
    
    return df,df_raw


def fit_line_fast(x, y):
    """
    Least-squares fit of a line: y = k * x + b
    Parameters
    ----------
    x : np.ndarray
        1D array of x values.
    y : np.ndarray
        1D array of y values.
    Returns
    -------
    k : float
        Slope of the fitted line.
    b : float
        Intercept of the fitted line.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = x.size
    sx = x.sum()
    sy = y.sum()
    sxx = np.dot(x, x)
    sxy = np.dot(x, y)
    k = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b = (sy - k * sx) / n
    return k, b

if 'pg_tds_integral' not in st.session_state:
    st.session_state.pg_tds_integral = {}
if 'data_tab_key' not in st.session_state.pg_tds_integral:
    st.session_state.pg_tds_integral['data_tab_key'] = 0
if 'time_tab_key' not in st.session_state.pg_tds_integral:
    st.session_state.pg_tds_integral['time_tab_key'] = 0
if 'bg_factor_k' not in st.session_state.pg_tds_integral:
    st.session_state.pg_tds_integral['bg_factor_k'] = 0.0
if 'bg_factor_b' not in st.session_state.pg_tds_integral:
    st.session_state.pg_tds_integral['bg_factor_b'] = 0.0
if 'auto_bg_switch' not in st.session_state.pg_tds_integral:
    st.session_state.pg_tds_integral['auto_bg_switch'] = False
if 'data_with_temp' not in st.session_state.pg_tds_integral:
    st.session_state.pg_tds_integral['data_with_temp'] = False

st.title('TDS Integral')
time_file = st.file_uploader("Upload a TDS result file (.tab):",
                            accept_multiple_files=False,
                            type="tab",
                            key=f"time_tab_{st.session_state.pg_tds_integral['time_tab_key']}")

if time_file != None:
    if st.button('Clear uploaded files'):
        st.session_state.pg_tds_integral['data_tab_key'] += 1
        st.session_state.pg_tds_integral['time_tab_key'] += 1
        st.rerun()

if time_file != None:
    time_meta_df,data_df = read_time_metadata(time_file)
    if 'Internal Temperature [°C]' in data_df:
        st.session_state.pg_tds_integral['data_with_temp'] = True
    else:
        st.session_state.pg_tds_integral['data_with_temp'] = False
        st.write('No temperature data detected. Plot only time data')
    with st.expander('Show data frames'):
        st.write('Time metadata')
        st.write(time_meta_df)
        st.write(data_df)
    sample_weight = time_meta_df.loc[0,'Weight [g]']
    weight_factor = time_meta_df.loc[0,'Factor']
    col1, col2 = st.columns(2, border=True)
    with col1:
        weight_unit_select = st.selectbox('Select unit:', ['mg','g'])
        if weight_unit_select == 'mg':
            sample_weight *= 1e-3
        elif weight_unit_select == 'g':
            pass
        st.write(f'Sample Weight (g): {sample_weight}')
    with col2:
        st.write(f'Weight factor: {weight_factor}')
    if st.session_state.pg_tds_integral['data_with_temp']:
        process_df = data_df[['Time [s]','Raw Data','Internal Temperature [°C]']].copy()
    else:
        process_df = data_df[['Time [s]','Raw Data']].copy()
    process_df.rename(columns={'Time [s]': 'Time Hydrogen','Raw Data': 'Hydrogen'},inplace=True)
    process_df['Hydrogen Normalised'] = process_df['Hydrogen'] / sample_weight / weight_factor
    time_range = [process_df['Time Hydrogen'].min(), process_df['Time Hydrogen'].max()]
    with st.container(border=True):
        st.write('Auto detect background')
        auto_bg_radio = st.radio('Background Autodetect On/Off',
                                    ['on','off'], horizontal=True)
        if auto_bg_radio == 'on':
            bg_range_enable = True
        else: # auto_bg_radio == 'off' 
            bg_range_enable = False
        bg_range = st.slider("Select a time range for background", time_range[0],time_range[1], 
                                (time_range[0] + (time_range[1]-time_range[0])*0.7, time_range[0] + (time_range[1]-time_range[0])*0.95),
                                disabled = (not bg_range_enable))
        if bg_range_enable == True:
            auto_bg_df = process_df.loc[(process_df["Time Hydrogen"] >= bg_range[0]) & (process_df["Time Hydrogen"] <= bg_range[1]),
                                        ["Time Hydrogen", 'Hydrogen Normalised']]
            k, b = fit_line_fast(auto_bg_df['Time Hydrogen'], auto_bg_df['Hydrogen Normalised'])
            st.session_state.pg_tds_integral['bg_factor_k'] = k
            st.session_state.pg_tds_integral['bg_factor_b'] = b
        col_bg_k,col_bg_b = st.columns(2)
        with col_bg_k:
            bg_factor_k = st.number_input('K',step=1e-12, format='%0.12f',
                                          value=st.session_state.pg_tds_integral['bg_factor_k'],
                                          disabled=bg_range_enable)
        with col_bg_b:
            bg_factor_b = st.number_input('B',step=1e-12, format='%0.12f',
                                          value=st.session_state.pg_tds_integral['bg_factor_b'],
                                          disabled=bg_range_enable)
    col_start_time, col_filter = st.columns(2,border=True)
    with col_start_time:
        st.write('Set start time')
        start_time = st.number_input('Set a start time')
    with col_filter:
        filter_radio = st.radio('Filter on/off', ['on','off'], horizontal=True)
        if filter_radio == 'on':
            filter_enable = True
        else:
            filter_enable = False
        filter_kernel_half_size = st.number_input('Filter kernel half length',step=1,
                                             min_value=1, max_value=50,
                                             disabled=(not filter_enable))
    # remove background
    process_df['Background'] = process_df['Time Hydrogen'] * bg_factor_k + bg_factor_b
    process_df['Hydrogen Norm. Bg Rm'] = process_df['Hydrogen Normalised'] - process_df['Background']
    if filter_enable == True:
        filter_kernel_size = filter_kernel_half_size*2 + 1
        filter_kernel = np.ones(filter_kernel_size) / filter_kernel_size
        pad = filter_kernel_size // 2
        x_pad = np.pad(process_df['Hydrogen Normalised'].to_numpy(), pad_width=pad, mode='edge')
        process_df['Hydrogen Norm. Flt.'] = np.convolve(x_pad, filter_kernel, mode='valid')
    integral_df = process_df.loc[process_df["Time Hydrogen"] > start_time,["Time Hydrogen", 'Hydrogen Norm. Bg Rm','Internal Temperature [°C]']].copy()
    integral_df['Time Hydrogen'] -= integral_df['Time Hydrogen'].min()
    t = integral_df["Time Hydrogen"].to_numpy()
    h = integral_df['Hydrogen Norm. Bg Rm'].to_numpy()
    integral_df["Hydrogen Integral"] = np.concatenate([[0],np.cumsum((h[:-1] + h[1:]) / 2 * np.diff(t))])
    if st.session_state.pg_tds_integral['data_with_temp']:
        plot_num = 3
    else:
        plot_num = 2
    fig,axs = plt.subplots(plot_num,1)
    fig.set_size_inches([6,8])
    fig.set_dpi(100)
    fig.subplots_adjust(hspace=0.3)
    ax = axs[0]
    ax.plot(process_df['Time Hydrogen'], process_df['Hydrogen Normalised'], label='H Norm.')
    if filter_enable == True:
        ax.plot(process_df['Time Hydrogen'], process_df['Hydrogen Norm. Flt.'], label='H Norm. Flt.')
    ax.plot(process_df['Time Hydrogen'], process_df['Background'], label='Bg')
    ax.vlines(x=start_time, ymin=process_df['Hydrogen Normalised'].min(), ymax=process_df['Hydrogen Normalised'].max(),
              label='T start',color='red')
    if bg_range_enable == True:
        ax.vlines(x=bg_range, ymin=process_df['Hydrogen Normalised'].min(), ymax=process_df['Hydrogen Normalised'].max(),label='Bg est. range',
                linestyles=':',color='black')
    ax.set_ylabel('Hydrogen Norm. (ppm)')
    ax.set_xlabel('time (s)')
    ax.legend()
    ax = axs[1]
    ax.plot(integral_df['Time Hydrogen'], integral_df['Hydrogen Integral'])
    ax.set_ylabel('Hydrogen Inte. (ppm)')
    ax.set_xlabel('time (s)')
    if plot_num == 3:
        ax = axs[2]
        ax.plot(process_df['Internal Temperature [°C]'],process_df['Hydrogen Normalised'])
        ax.set_ylabel('Hydrogen Norm. (ppm)')
        ax.set_xlabel('Internal Temperature [°C]')
    st.pyplot(fig)
    with st.expander('Show result dataframe'):
        st.write('Integral result (hover mouse on the table to download csv)')
        st.write(integral_df)
        para_dict = {
            'sample_weight_g':sample_weight,
            'weight_factor': weight_factor,
            'bg_k': bg_factor_k,
            'bg_b': bg_factor_b,
            't_start': start_time,
                     }
        if bg_range_enable == True:
            para_dict['auto_bg'] = True
            para_dict['auto_bg_time_range'] = bg_range
        if filter_enable == True:
            para_dict['filter_enable'] = True
            para_dict['filter_kernel_half_size'] = filter_kernel_half_size
        st.write('Parameters used for process')
        st.write(para_dict)
        st.write('Processed results with normalisation and background removal (before integral)')
        st.write(process_df)

else: #data_file == None or time_file == None:
    st.write('Please upload a tab file')