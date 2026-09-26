import streamlit as st

pages = {'tool':[st.Page('page_tds_integral.py',title='TDS Integral')]}

pg = st.navigation(pages)

with st.sidebar:
    st.title('**TDS Integral**')
    st.write(' ')
    st.write('v1.0')
    st.write('__________________')
    
pg.run()