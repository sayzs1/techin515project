import streamlit as st
import time
import pandas as pd
import plotly.express as px

# 初始化会话状态变量
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'end_time' not in st.session_state:
    st.session_state.end_time = None
if 'durations' not in st.session_state:
    st.session_state.durations = []
if 'paused_time' not in st.session_state:
    st.session_state.paused_time = 0
if 'is_paused' not in st.session_state:
    st.session_state.is_paused = False

# 设置页面标题
st.title("Data dashboard")

# 说明文字
st.write("""
Joint Motion state report
""")

# 嵌入Power BI报表1
embed_link = "https://app.powerbi.com/reportEmbed?reportId=33a64403-3192-43d1-a9dc-19d41d2a7ddd&autoAuth=true&ctid=f6b6dd5b-f02f-441a-99a0-162ac5060bd2"
st.markdown(f"""
<iframe width="800" height="600" src="{embed_link}" frameborder="0" allowFullScreen="true"></iframe>
""", unsafe_allow_html=True)

# 说明文字
st.write("""
Pulse report
""")

# 嵌入Power BI报表1
embed_link = "https://app.powerbi.com/reportEmbed?reportId=aad04226-3fc3-4856-8a99-1412742682ad&autoAuth=true&ctid=f6b6dd5b-f02f-441a-99a0-162ac5060bd2"
st.markdown(f"""
<iframe width="800" height="600" src="{embed_link}" frameborder="0" allowFullScreen="true"></iframe>
""", unsafe_allow_html=True)

# 计时功能
st.write("## Sport Timer")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button('Start'):
        if st.session_state.is_paused:
            st.session_state.start_time += time.time() - st.session_state.paused_time
            st.session_state.is_paused = False
        else:
            st.session_state.start_time = time.time()
        st.session_state.end_time = None
        st.session_state.paused_time = 0

with col2:
    if st.button('Pause'):
        if st.session_state.start_time is not None and not st.session_state.is_paused:
            st.session_state.paused_time = time.time()
            st.session_state.is_paused = True

with col3:
    if st.button('End'):
        if st.session_state.start_time is not None:
            if st.session_state.is_paused:
                duration = st.session_state.paused_time - st.session_state.start_time
            else:
                st.session_state.end_time = time.time()
                duration = st.session_state.end_time - st.session_state.start_time
            st.session_state.durations.append(duration)
            st.session_state.start_time = None
            st.session_state.end_time = None
            st.session_state.paused_time = 0
            st.session_state.is_paused = False

# 显示当前计时状态
st.write("### Time Elapsed")
timer_placeholder = st.empty()

def format_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{int(minutes):02}:{int(seconds):02}"

if st.session_state.start_time is not None:
    while st.session_state.start_time is not None:
        if st.session_state.is_paused:
            elapsed_time = int(st.session_state.paused_time - st.session_state.start_time)
        else:
            elapsed_time = int(time.time() - st.session_state.start_time)
        timer_placeholder.markdown(f"""
        <div style="font-size: 72px; text-align: center;">
            {format_time(elapsed_time)}
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1)
elif st.session_state.end_time is not None:
    last_duration = int(st.session_state.durations[-1])
    timer_placeholder.markdown(f"""
    <div style="font-size: 72px; text-align: center;">
        {format_time(last_duration)}
    </div>
    """, unsafe_allow_html=True)
else:
    timer_placeholder.markdown("""
    <div style="font-size: 72px; text-align: center;">
        00:00
    </div>
    """, unsafe_allow_html=True)

# 统计表格
st.write("## Recorded Durations")
durations_df = pd.DataFrame(st.session_state.durations, columns=["Duration (seconds)"])
st.table(durations_df)

# 绘制柱状图
if not durations_df.empty:
    fig = px.bar(durations_df, x=durations_df.index + 1, y="Duration (seconds)", labels={'x': 'Session', 'Duration (seconds)': 'Duration (seconds)'}, title="Duration of Each Exercise Session")
    st.plotly_chart(fig)