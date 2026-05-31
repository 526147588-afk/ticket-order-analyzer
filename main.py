import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
from datetime import datetime
from io import BytesIO
from analyzer import TicketOrderAnalyzer
import warnings
warnings.filterwarnings('ignore')

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_date TEXT NOT NULL,
            file_name TEXT,
            order_count INTEGER,
            total_profit REAL,
            total_amount REAL,
            data_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_data(df, file_name=None):
    conn = get_connection()
    upload_date = datetime.now().strftime('%Y-%m-%d')
    order_count = len(df)
    total_profit = pd.to_numeric(df['利润'], errors='coerce').sum()
    total_amount = pd.to_numeric(df['支付金额'], errors='coerce').sum()
    data_json = df.to_json(orient='records', force_ascii=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (upload_date, file_name, order_count, total_profit, total_amount, data_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (upload_date, file_name, order_count, total_profit, total_amount, data_json))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id

def get_all_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, upload_date, file_name, order_count, total_profit, total_amount, created_at
        FROM history ORDER BY created_at DESC
    ''')
    records = cursor.fetchall()
    conn.close()
    return records

def get_history_data(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT data_json FROM history WHERE id = ?', (record_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        df = pd.read_json(row[0], orient='records')
        return df
    return None

def delete_history(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM history WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()

# 初始化数据库
init_db()
st.set_page_config(
    page_title="机票数据分析平台",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 科技风 CSS
st.markdown("""
<style>
/* 标题霓虹蓝发光效果 */
h1, h2, h3, h4 {
    color: #00bfff !important;
    text-shadow: 0 0 8px #00bfff, 0 0 16px #00bfff55;
    font-weight: 800 !important;
}

/* 按钮：霓虹边框 + 发光hover */
.stButton > button {
    border: 1px solid #00bfff66 !important;
    box-shadow: 0 0 6px #00bfff33;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    box-shadow: 0 0 12px #00bfff, 0 0 24px #00bfff44;
    transform: scale(1.02);
}

/* 表格表头：霓虹蓝高亮 */
div[data-testid="stDataFrame"] th {
    background-color: rgba(0, 191, 255, 0.15) !important;
    color: #00bfff !important;
    font-weight: bold !important;
}

/* 卡片/容器：霓虹蓝边框 + 悬浮效果 */
div[data-testid="stVerticalBlock"] > div {
    border: 1px solid rgba(0, 191, 255, 0.3) !important;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0, 191, 255, 0.15);
    padding: 15px;
    margin-bottom: 15px;
    transition: all 0.3s ease;
}
div[data-testid="stVerticalBlock"] > div:hover {
    border: 1px solid #00bfff !important;
    box-shadow: 0 0 20px rgba(0, 191, 255, 0.5);
    transform: translateY(-3px);
}

/* DataFrame 表格宽度限制 */
[data-testid="stDataFrame"] {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}
[data-testid="stDataFrame"] .dvn-scroller {
    max-width: 100% !important;
}

/* Plotly图表宽度限制 */
div[data-testid="stPlotlyChart"] {
    width: 100% !important;
    max-width: 100% !important;
}
div[data-testid="stPlotlyChart"] > div {
    width: 100% !important;
    max-width: 100% !important;
}

/* 强制图表SVG容器宽度 */
div[data-testid="stPlotlyChart"] svg {
    width: 100% !important;
    max-width: 100% !important;
}

/* JS渲染后的图表容器 */
.js-plotly-plot .plotly {
    width: 100% !important;
}

/* 输入框宽度限制 */
.stTextInput {
    width: 100% !important;
}
.stTextInput > div {
    max-width: 100% !important;
}

/* 选择框宽度限制 */
[data-testid="stSelectbox"] {
    width: 100% !important;
}

/* 文件上传组件：图标和按钮霓虹蓝 */
[data-testid="stFileUploader"] svg {
    fill: #00bfff !important;
}
[data-testid="stFileUploader"] button {
    border: 1px solid #00bfff66 !important;
    color: #00bfff !important;
}

/* 信息卡片样式 */
.info-card {
    background: rgba(0, 191, 255, 0.05);
    border-left: 3px solid #00bfff;
    padding: 15px;
    margin: 10px 0;
    border-radius: 0 8px 8px 0;
}

/* 功能模块卡片 */
.module-card {
    background: rgba(0, 191, 255, 0.08);
    border: 1px solid rgba(0, 191, 255, 0.3);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
}
.module-card h3 {
    margin-top: 0 !important;
    color: #00bfff !important;
}

/* Metric 卡片样式 */
[data-testid="stMetric"] {
    background: rgba(13, 21, 37, 0.8) !important;
    border: 1px solid rgba(0, 191, 255, 0.3) !important;
    border-radius: 12px !important;
    padding: 15px !important;
}

/* 表格居中对齐 - 支持横向滚动 */
div[data-testid="stDataFrame"] {
    width: 100% !important;
    overflow-x: auto !important;
}
div[data-testid="stDataFrame"] .dvn-scroller {
    overflow-x: auto !important;
}
div[data-testid="stDataFrame"] table {
    text-align: center !important;
    min-width: 100% !important;
}
div[data-testid="stDataFrame"] thead tr th {
    text-align: center !important;
    background-color: rgba(0, 191, 255, 0.15) !important;
    color: #00bfff !important;
    font-weight: bold !important;
}
div[data-testid="stDataFrame"] tbody tr td {
    text-align: center !important;
    color: #b0d4e6 !important;
}
div[data-testid="stDataFrame"] tbody tr:hover {
    background-color: rgba(0, 191, 255, 0.08) !important;
}

/* 图表容器 */
div[data-testid="stPlotlyChart"] {
    background: rgba(10, 15, 25, 0.8);
    border: 1px solid rgba(0, 191, 255, 0.2);
    border-radius: 12px;
    padding: 10px;
}
/* 侧边栏导航样式 */
.st-cn {
    padding: 0 !important;
}

/* 导航按钮样式 */
.nav-button > button {
    width: 100% !important;
    text-align: left !important;
    padding: 10px 15px !important;
    margin: 3px 0 !important;
    border: 1px solid rgba(0, 191, 255, 0.2) !important;
    background: rgba(0, 191, 255, 0.05) !important;
    color: #b0d4e6 !important;
    transition: all 0.3s ease !important;
}
.nav-button > button:hover {
    background: rgba(0, 191, 255, 0.15) !important;
    border-color: #00bfff !important;
    box-shadow: 0 0 10px rgba(0, 191, 255, 0.3) !important;
}

/* 选中状态的导航按钮 */
.nav-button > button:focus:not(:active) {
    background: rgba(0, 191, 255, 0.2) !important;
}
</style>
""", unsafe_allow_html=True)

# 页面状态管理
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 首页"

# 侧边栏导航
st.sidebar.header("🎯 导航")

pages = [
    "🏠 首页",
    "📊 数据概览",
    "✈️ 航司分析",
    "🛫 航线分析",
    "💰 利润分析",
    "⚠️ 异常监控",
    "⏱️ 出票时长",
    "🤖 自动出票",
    "📚 历史数据"
]

# 1列，每个按钮独立一行
for i, p in enumerate(pages):
    col = st.sidebar.columns(1)
    with col[0]:
        if st.button(p, key=f"nav_{i}", use_container_width=True):
            st.session_state.current_page = p
            st.rerun()

page = st.session_state.current_page

# 文件上传
st.sidebar.divider()
uploaded_file = st.sidebar.file_uploader("上传Excel文件", type=["xlsx", "xls"])

# 会话状态管理
if 'current_data' not in st.session_state:
    st.session_state.current_data = None
    st.session_state.current_file = None

# 当上传文件时，保存到历史记录
if uploaded_file is not None:
    with open("temp_data.xlsx", "wb") as f:
        f.write(uploaded_file.getbuffer())
    df_upload = pd.read_excel("temp_data.xlsx")
    # 保存到历史记录
    record_id = save_data(df_upload, uploaded_file.name)
    st.session_state.current_data = "temp_data.xlsx"
    st.session_state.current_file = uploaded_file.name
    st.sidebar.success(f"已加载: {uploaded_file.name}")
    st.sidebar.info(f"总订单: {len(df_upload):,}")

# 获取当前数据文件路径
def get_current_datafile():
    if st.session_state.current_data:
        return st.session_state.current_data
    elif uploaded_file:
        return "temp_data.xlsx"
    return None

# ========== 首页 ==========
if page == "🏠 首页":
    st.title("🎫 机票数据分析平台")

    # 平台简介
    st.markdown("""
    <div class="info-card">
        <h3>📌 平台简介</h3>
        <p>机票数据分析平台是一款专为机票代理业务设计的可视化分析工具。通过上传订单数据，平台会自动进行多维度分析，帮助您快速掌握业务运营状况、优化决策效率、提升自动化处理成功率。</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 数据分析规则简介
    st.subheader("📊 数据分析规则")

    col_rule1, col_rule2 = st.columns(2)

    with col_rule1:
        st.markdown("""
        <div class="module-card">
            <h3>📈 航司分析</h3>
            <p>分析各航司的订单量、成功率、利润等指标，支持TOP排名和交叉分析。</p>
            <p><i>预留空间：航司偏好分析、航司异常监控...</i></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="module-card">
            <h3>🛫 航线分析</h3>
            <p>分析各航线的订单分布、热门程度、利润情况，支持城市对分析。</p>
            <p><i>预留空间：航线趋势预测、航线优化建议...</i></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="module-card">
            <h3>💰 利润分析</h3>
            <p>追踪每笔订单的利润情况，分析盈利/亏损分布，支持按航司、平台等维度查看。</p>
            <p><i>预留空间：利润预测、成本分析...</i></p>
        </div>
        """, unsafe_allow_html=True)

    with col_rule2:
        st.markdown("""
        <div class="module-card">
            <h3>⚠️ 异常监控</h3>
            <p>监控出票失败、超时等异常情况，分析失败原因占比，支持按渠道/航司查看。</p>
            <p><i>预留空间：异常告警、自动化处理规则...</i></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="module-card">
            <h3>🤖 自动出票成功率</h3>
            <p>追踪全自动出票成功率，按航司、平台、渠道等维度分析，识别人工介入点。</p>
            <p><i>预留空间：成功率趋势、预测模型...</i></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="module-card">
            <h3>⏱️ 出票时长分析</h3>
            <p>分析出票耗时分布，识别超时订单，支持按渠道/航司统计。</p>
            <p><i>预留空间：时效预警、自动催票...</i></p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 操作指南
    st.subheader("📖 操作指南")

    st.markdown("""
    <div class="info-card">
        <h4>📂 如何上传数据</h4>
        <ol>
            <li>点击左侧「上传Excel文件」按钮</li>
            <li>选择您的订单数据文件（支持 .xlsx 和 .xls 格式）</li>
            <li>等待系统解析数据并自动加载分析页面</li>
        </ol>
        <p><b>注意：</b>上传的文件会保存在本地历史记录中，方便后续查询。</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #00bfff88; padding: 20px;">
        <p>🚀 准备好后，点击左侧「上传Excel文件」开始您的数据分析之旅</p>
    </div>
    """, unsafe_allow_html=True)

# ========== 数据概览 ==========
elif page == "📊 数据概览":
    st.title("📊 数据概览")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        # 计算核心指标
        total_orders = len(df)
        total_profit = pd.to_numeric(df['利润'], errors='coerce').sum()
        avg_profit = pd.to_numeric(df['利润'], errors='coerce').mean()

        # 自动出票成功率
        is_auto = df['最后锁定人'].isna() | (df['最后锁定人'] == '')
        auto_rate = is_auto.sum() / total_orders * 100 if total_orders > 0 else 0

        # ========== 4个KPI卡片 ==========
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 订单总数", f"{total_orders:,}")
        col2.metric("💰 订单总利润", f"¥{total_profit:,.2f}")
        col3.metric("📊 平均利润", f"¥{avg_profit:.2f}")
        col4.metric("🤖 自动出票成功率", f"{auto_rate:.1f}%")

        st.divider()

        # ========== 航司和平台柱状图 ==========
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("📊 航司订单TOP10")
            airline_counts = df['航空公司列表'].value_counts().head(10).reset_index()
            airline_counts.columns = ['航司', '订单数']
            fig_airline = px.bar(
                airline_counts,
                x='航司',
                y='订单数',
                color='订单数',
                color_continuous_scale='blues',
                text='订单数'
            )
            fig_airline.update_traces(textposition='outside')
            fig_airline.update_layout(
                height=400,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=14),
                title_font=dict(color='#00bfff'),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                dragmode=False
            )
            st.plotly_chart(fig_airline, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        with col_chart2:
            st.subheader("📊 平台订单TOP10")
            platform_counts = df['平台'].value_counts().head(10).reset_index()
            platform_counts.columns = ['平台', '订单数']
            fig_platform = px.bar(
                platform_counts,
                x='平台',
                y='订单数',
                color='订单数',
                color_continuous_scale='blues',
                text='订单数'
            )
            fig_platform.update_traces(textposition='outside')
            fig_platform.update_layout(
                height=400,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=14),
                title_font=dict(color='#00bfff'),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                dragmode=False
            )
            st.plotly_chart(fig_platform, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        st.divider()

        # ========== 自动出票成功率折线图 ==========
        st.subheader("📈 自动出票成功率24小时趋势")

        df['小时'] = pd.to_datetime(df['创建时间'], errors='coerce').dt.hour
        df['是否自动'] = df['最后锁定人'].isna() | (df['最后锁定人'] == '')
        hourly_stats = df.groupby('小时').agg(
            总订单=('是否自动', 'count'),
            自动订单=('是否自动', 'sum')
        ).reset_index()
        hourly_stats['成功率'] = (hourly_stats['自动订单'] / hourly_stats['总订单'] * 100).round(0)

        max_idx = hourly_stats['成功率'].idxmax()
        min_idx = hourly_stats['成功率'].idxmin()

        fig_trend = px.line(
            hourly_stats,
            x='小时',
            y='成功率',
            markers=True,
            text=hourly_stats['成功率'].astype(int).astype(str) + '%'
        )
        fig_trend.update_traces(
            line_color='#00bfff',
            marker_color='#00ffff',
            marker_size=8,
            textposition='top center',
            textfont=dict(color='#b0d4e6', size=12)
        )

        # 最高点 - 红色星形
        fig_trend.add_trace(go.Scatter(
            x=[hourly_stats.iloc[max_idx]['小时']],
            y=[hourly_stats.iloc[max_idx]['成功率']],
            mode='markers',
            marker=dict(size=18, color='red', symbol='star', line=dict(width=2, color='darkred')),
            showlegend=False
        ))

        # 最低点 - 橙色星形
        fig_trend.add_trace(go.Scatter(
            x=[hourly_stats.iloc[min_idx]['小时']],
            y=[hourly_stats.iloc[min_idx]['成功率']],
            mode='markers',
            marker=dict(size=18, color='orange', symbol='star', line=dict(width=2, color='darkorange')),
            showlegend=False
        ))

        fig_trend.update_layout(
            height=400,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=14),
            title_font=dict(color='#00bfff'),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', dtick=1, tickfont=dict(color='#b0d4e6', size=12)),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 100], tickfont=dict(color='#b0d4e6', size=12))
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

# ========== 航司分析 ==========
elif page == "✈️ 航司分析":
    st.title("✈️ 航司分析")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        airline_stats = df['航空公司列表'].value_counts().reset_index()
        airline_stats.columns = ['航司', '订单数']

        st.subheader("📊 航司订单量")
        fig_airline = px.bar(
            airline_stats,
            x='航司',
            y='订单数',
            color='订单数',
            color_continuous_scale='blues',
            text='订单数'
        )
        fig_airline.update_traces(textposition='outside')
        fig_airline.update_layout(
            height=500,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=14),
            title_font=dict(color='#00bfff'),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12), tickangle=45),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
        )
        st.plotly_chart(fig_airline, use_container_width=True)

        st.divider()

        st.subheader("📊 航司订单占比")
        fig_pie = px.pie(
            airline_stats,
            values='订单数',
            names='航司',
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textfont=dict(color='white', size=12))
        fig_pie.update_layout(
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=14),
            title_font=dict(color='#00bfff')
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# ========== 航线分析 ==========
elif page == "🛫 航线分析":
    st.title("🛫 航线分析")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        df['航线'] = df['出发机场列表'] + ' → ' + df['到达机场列表']

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🛫 热门出发城市TOP10")
            dep_counts = df['出发机场列表'].value_counts().head(10).reset_index()
            dep_counts.columns = ['城市', '订单数']
            fig_dep = px.bar(
                dep_counts,
                x='城市',
                y='订单数',
                color='订单数',
                color_continuous_scale='blues',
                text='订单数'
            )
            fig_dep.update_traces(textposition='outside')
            fig_dep.update_layout(
                height=400,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=14),
                title_font=dict(color='#00bfff'),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
            )
            st.plotly_chart(fig_dep, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        with col2:
            st.subheader("🛬 热门到达城市TOP10")
            arr_counts = df['到达机场列表'].value_counts().head(10).reset_index()
            arr_counts.columns = ['城市', '订单数']
            fig_arr = px.bar(
                arr_counts,
                x='城市',
                y='订单数',
                color='订单数',
                color_continuous_scale='oranges',
                text='订单数'
            )
            fig_arr.update_traces(textposition='outside')
            fig_arr.update_layout(
                height=400,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=14),
                title_font=dict(color='#00bfff'),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
            )
            st.plotly_chart(fig_arr, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        st.divider()

        st.subheader("🛫 热门航线TOP15")
        route_counts = df['航线'].value_counts().head(15).reset_index()
        route_counts.columns = ['航线', '订单数']

        fig_route = px.bar(
            route_counts,
            x='航线',
            y='订单数',
            color='订单数',
            color_continuous_scale='viridis',
            text='订单数'
        )
        fig_route.update_traces(textposition='outside')
        fig_route.update_layout(
            height=400,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=14),
            title_font=dict(color='#00bfff'),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12), tickangle=30),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
        )
        st.plotly_chart(fig_route, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        st.divider()

        st.subheader("🔀 航程类型分析（单程/往返/多程）")
        df['航班数'] = df['航班号列表'].apply(lambda x: len(str(x).split(',')) if pd.notna(x) else 0)
        def classify_trip(seg):
            if seg == 1: return '单程'
            elif seg == 2: return '往返'
            else: return '多程'
        df['航程类型'] = df['航班数'].apply(classify_trip)
        trip_counts = df['航程类型'].value_counts().reset_index()
        trip_counts.columns = ['航程类型', '订单数']

        col5, col6 = st.columns(2)
        with col5:
            fig_trip = px.pie(
                trip_counts,
                values='订单数',
                names='航程类型',
                hole=0.5,
                color='航程类型',
                color_discrete_map={'单程': '#00bfff', '往返': '#ff6b6b', '多程': '#ffd93d'}
            )
            fig_trip.update_traces(textposition='inside', textfont=dict(color='white', size=14))
            fig_trip.update_layout(
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=14),
                title_font=dict(color='#00bfff')
            )
            st.plotly_chart(fig_trip, use_container_width=True)

        with col6:
            st.dataframe(trip_counts, use_container_width=True)

# ========== 利润分析 ==========
elif page == "💰 利润分析":
    st.title("💰 利润分析")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        profit = pd.to_numeric(df['利润'], errors='coerce')

        col1, col2, col3 = st.columns(3)
        col1.metric("📦 总订单", f"{len(df):,}")
        col2.metric("💰 总利润", f"¥{profit.sum():,.2f}")
        col3.metric("📊 平均利润", f"¥{profit.mean():.2f}")

        st.divider()

        df['利润数值'] = pd.to_numeric(df['利润'], errors='coerce')

        st.subheader("✈️ 航司利润排名")
        airline_profit = df.groupby('航空公司列表')['利润数值'].agg(['sum', 'mean', 'count']).reset_index()
        airline_profit.columns = ['航司', '总利润', '平均利润', '订单数']
        airline_profit = airline_profit.sort_values('总利润', ascending=False)

        fig_profit_airline = px.bar(
            airline_profit,
            x='航司',
            y='总利润',
            color='总利润',
            color_continuous_scale='rdylgn',
            text=airline_profit['总利润'].round(0).astype(int)
        )
        fig_profit_airline.update_traces(textposition='outside')
        fig_profit_airline.update_layout(
            height=400,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=14),
            title_font=dict(color='#00bfff'),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12), tickangle=45),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
        )
        st.plotly_chart(fig_profit_airline, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        st.dataframe(airline_profit, use_container_width=True)

        st.divider()

        st.subheader("🖥️ 平台利润排名")
        platform_profit = df.groupby('平台')['利润数值'].agg(['sum', 'mean', 'count']).reset_index()
        platform_profit.columns = ['平台', '总利润', '平均利润', '订单数']
        platform_profit = platform_profit.sort_values('总利润', ascending=False)

        fig_profit_platform = px.bar(
            platform_profit,
            x='平台',
            y='总利润',
            color='总利润',
            color_continuous_scale='rdylgn',
            text=platform_profit['总利润'].round(0).astype(int)
        )
        fig_profit_platform.update_traces(textposition='outside')
        fig_profit_platform.update_layout(
            height=400,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=14),
            title_font=dict(color='#00bfff'),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
        )
        st.plotly_chart(fig_profit_platform, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        st.dataframe(platform_profit, use_container_width=True)

# ========== 异常监控 ==========
elif page == "⚠️ 异常监控":
    st.title("⚠️ 异常监控")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        # 失败订单判断：第一次失败原因或失败原因有内容，或有最后锁定人（人工介入）
        # 全自动成功 = 第一次失败原因为空 AND 失败原因为空 AND 最后锁定人为空
        df['是否有失败'] = (
            (df['第一次失败原因'].fillna('').str.strip() != '') |
            (df['失败原因'].fillna('').str.strip() != '') |
            (df['最后锁定人'].fillna('').str.strip() != '')
        )

        total_orders = len(df)
        fail_count = df['是否有失败'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("📦 总订单数", f"{total_orders:,}")
        col2.metric("⚠️ 失败订单数", f"{fail_count:,}")
        col3.metric("✅ 成功率", f"{(total_orders - fail_count) / total_orders * 100:.1f}%")

        st.divider()

        st.subheader("❌ 失败原因（第一次+最后一次）")
        # 创建失败原因组合用于展示
        df['失败原因组合'] = df['第一次失败原因'].fillna('') + ' + ' + df['失败原因'].fillna('')
        df['失败原因组合'] = df['失败原因组合'].apply(lambda x: x if x != ' + ' else '')
        fail_reason_df = df[df['失败原因组合'].str.strip() != ''].copy()
        fail_reason = fail_reason_df['失败原因组合'].value_counts().head(15).reset_index()
        fail_reason.columns = ['失败原因', '订单数']

        st.dataframe(fail_reason, use_container_width=True)

        st.divider()

        st.subheader("✈️ 航司失败分布")
        airline_fail = df[df['是否有失败']].groupby('航空公司列表').size().reset_index(name='失败订单数')
        airline_fail = airline_fail.sort_values('失败订单数', ascending=False)

        col6, col7 = st.columns(2)
        with col6:
            fig_airline_fail = px.bar(
                airline_fail.head(15),
                x='航空公司列表',
                y='失败订单数',
                color='失败订单数',
                color_continuous_scale='reds',
                text='失败订单数'
            )
            fig_airline_fail.update_traces(textposition='outside')
            fig_airline_fail.update_layout(
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=16),
                title_font=dict(color='#00bfff'),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
            )
            st.plotly_chart(fig_airline_fail, use_container_width=True)

        with col7:
            st.dataframe(airline_fail, use_container_width=True)

        st.divider()

        st.subheader("🖥️ 平台失败分布")
        platform_fail = df[df['是否有失败']].groupby('平台').size().reset_index(name='失败订单数')
        platform_fail = platform_fail.sort_values('失败订单数', ascending=False)

        col8, col9 = st.columns(2)
        with col8:
            fig_platform_fail = px.bar(
                platform_fail,
                x='平台',
                y='失败订单数',
                color='失败订单数',
                color_continuous_scale='reds',
                text='失败订单数'
            )
            fig_platform_fail.update_traces(textposition='outside')
            fig_platform_fail.update_layout(
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=16),
                title_font=dict(color='#00bfff'),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
            )
            st.plotly_chart(fig_platform_fail, use_container_width=True)

        with col9:
            st.dataframe(platform_fail, use_container_width=True)

# ========== 出票时长分析 ==========
elif page == "⏱️ 出票时长":
    st.title("⏱️ 出票时长分析")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        df['创建时间_dt'] = pd.to_datetime(df['创建时间'], errors='coerce')
        df['获取票号时间_dt'] = pd.to_datetime(df['上一次获取票号时间'], errors='coerce')
        df['出票时长_小时'] = (df['获取票号时间_dt'] - df['创建时间_dt']).dt.total_seconds() / 3600
        valid_duration = df[df['出票时长_小时'].notna() & (df['出票时长_小时'] > 0)]

        if len(valid_duration) > 0:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📊 平均出票时长", f"{valid_duration['出票时长_小时'].mean():.1f}h")
            col2.metric("⚡ 最快出票", f"{valid_duration['出票时长_小时'].min():.1f}h")
            col3.metric("🐢 最慢出票", f"{valid_duration['出票时长_小时'].max():.1f}h")
            col4.metric("📈 中位数", f"{valid_duration['出票时长_小时'].median():.1f}h")

            st.divider()

            # 超时订单筛选
            st.subheader("⚠️ 超时订单筛选")
            threshold_hours = st.slider("筛选时长（小时）", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
            overtime = valid_duration[valid_duration['出票时长_小时'] > threshold_hours].head(100)
            if len(overtime) > 0:
                overtime_list = overtime[['订单号', '航空公司列表', '采购渠道', '出票时长_小时']].copy()
                overtime_list.columns = ['订单号', '航司', '采购渠道', '出票时长(小时)']
                overtime_list['出票时长(小时)'] = overtime_list['出票时长(小时)'].round(2)
                st.dataframe(overtime_list, use_container_width=True)
                st.info(f"共 {len(overtime)} 条超时订单（>{threshold_hours}小时）")
            else:
                st.success(f"✅ 暂无超时订单（>{threshold_hours}小时）")
        else:
            st.warning("⚠️ 暂无有效的出票时长数据")

# ========== 自动出票成功率 ==========
elif page == "🤖 自动出票":
    st.title("🤖 全自动出票成功率分析")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        df['是否全自动'] = df['最后锁定人'].isna() | (df['最后锁定人'] == '')
        total = len(df)
        auto_count = df['是否全自动'].sum()
        manual_count = total - auto_count
        auto_rate = (auto_count / total * 100) if total > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 总订单数", f"{total:,}")
        col2.metric("🤖 全自动成功", f"{auto_count:,}")
        col3.metric("👤 需人工介入", f"{manual_count:,}")
        col4.metric("🎯 全自动成功率", f"{auto_rate:.1f}%")

        st.divider()

        # ========== 航司全自动出票成功率 ==========
        st.subheader("✈️ 航司全自动出票成功率")
        auto_by_airline = df.groupby('航空公司列表').agg(
            总订单=('是否全自动', 'count'),
            自动订单=('是否全自动', 'sum')
        ).reset_index()
        auto_by_airline['成功率'] = (auto_by_airline['自动订单'] / auto_by_airline['总订单'] * 100).round(1)
        auto_by_airline = auto_by_airline.sort_values('成功率', ascending=False)

        fig_auto = px.bar(
            auto_by_airline,
            x='航空公司列表',
            y='成功率',
            color='成功率',
            color_continuous_scale='rdylgn',
            text='成功率'
        )
        fig_auto.update_traces(textposition='outside')
        fig_auto.update_layout(
            height=400,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=14),
            title_font=dict(color='#00bfff'),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12), tickangle=45),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 100], tickfont=dict(color='#b0d4e6', size=12))
        )
        st.plotly_chart(fig_auto, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        st.dataframe(auto_by_airline, use_container_width=True)

        st.divider()

        # ========== 平台全自动出票成功率 ==========
        st.subheader("🖥️ 平台全自动出票成功率")
        auto_by_platform = df.groupby('平台').agg(
            总订单=('是否全自动', 'count'),
            自动订单=('是否全自动', 'sum')
        ).reset_index()
        auto_by_platform['成功率'] = (auto_by_platform['自动订单'] / auto_by_platform['总订单'] * 100).round(1)
        auto_by_platform = auto_by_platform.sort_values('成功率', ascending=False)

        fig_platform_auto = px.bar(
            auto_by_platform,
            x='平台',
            y='成功率',
            color='成功率',
            color_continuous_scale='rdylgn',
            text='成功率'
        )
        fig_platform_auto.update_traces(textposition='outside')
        fig_platform_auto.update_layout(
            height=400,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=14),
            title_font=dict(color='#00bfff'),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 100], tickfont=dict(color='#b0d4e6', size=12))
        )
        st.plotly_chart(fig_platform_auto, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        st.dataframe(auto_by_platform, use_container_width=True)

        st.divider()

        # ========== 采购渠道全自动出票成功率 ==========
        st.subheader("📡 采购渠道全自动出票成功率")
        if '采购渠道' in df.columns:
            auto_by_channel = df.groupby('采购渠道').agg(
                总订单=('是否全自动', 'count'),
                自动订单=('是否全自动', 'sum')
            ).reset_index()
            auto_by_channel['成功率'] = (auto_by_channel['自动订单'] / auto_by_channel['总订单'] * 100).round(1)
            auto_by_channel = auto_by_channel.sort_values('成功率', ascending=False)

            fig_channel_auto = px.bar(
                auto_by_channel,
                x='采购渠道',
                y='成功率',
                color='成功率',
                color_continuous_scale='rdylgn',
                text='成功率'
            )
            fig_channel_auto.update_traces(textposition='outside')
            fig_channel_auto.update_layout(
                height=400,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=14),
                title_font=dict(color='#00bfff'),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 100], tickfont=dict(color='#b0d4e6', size=12))
            )
            st.plotly_chart(fig_channel_auto, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
            st.dataframe(auto_by_channel, use_container_width=True)

# ========== 历史数据 ==========
elif page == "📚 历史数据":
    st.title("📚 历史数据")

    # 获取历史记录
    history = get_all_history()

    if len(history) == 0:
        st.info("暂无历史记录，上传Excel文件后会保存到历史记录")
    else:
        st.subheader("📋 历史记录列表")

        # 展示历史记录表格
        history_df = pd.DataFrame(history, columns=['ID', '上传日期', '文件名', '订单数', '总利润', '总金额', '创建时间'])
        history_df['总利润'] = history_df['总利润'].apply(lambda x: f"¥{x:,.2f}" if pd.notna(x) else "-")
        history_df['总金额'] = history_df['总金额'].apply(lambda x: f"¥{x:,.2f}" if pd.notna(x) else "-")
        st.dataframe(history_df, use_container_width=True)

        st.divider()

        # 选择要加载的历史记录
        st.subheader("📂 加载历史数据")
        history_options = {r[0]: r[2] or '未命名' for r in history}
        selected_id = st.selectbox("选择记录", options=list(history_options.keys()), format_func=lambda x: history_options[x])

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("加载该历史数据", type="primary"):
                df_hist = get_history_data(selected_id)
                if df_hist is not None:
                    hist_file = f"history_{selected_id}.xlsx"
                    df_hist.to_excel(hist_file, index=False)
                    # 保存到session_state供其他页面使用
                    st.session_state.current_data = hist_file
                    st.session_state.current_file = history_options[selected_id]
                    st.success(f"已加载 {len(df_hist)} 条订单数据")

                    # 显示数据预览
                    st.subheader("📊 数据预览")
                    st.dataframe(df_hist.head(10), use_container_width=True)

                    # 提供下载链接
                    buffer = BytesIO()
                    df_hist.to_excel(buffer, index=False, engine='openpyxl')
                    buffer.seek(0)
                    st.download_button(
                        label="下载Excel文件",
                        data=buffer,
                        file_name=hist_file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("加载失败")

        st.divider()

        # 删除历史记录
        st.subheader("🗑️ 删除历史数据")
        del_options = {r[0]: r[2] or '未命名' for r in history}
        del_id = st.selectbox("选择要删除的记录", options=list(del_options.keys()), format_func=lambda x: del_options[x])
        if st.button("删除该记录", type="secondary"):
            delete_history(del_id)
            st.success("已删除")
            st.rerun()