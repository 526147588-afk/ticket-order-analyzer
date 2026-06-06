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
        SELECT id, upload_date, file_name, order_count, total_profit, total_amount, created_at, data_json
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
    "🛫 航线运营",
    "💰 利润分析",
"🤖 自动出票",
    "📊 数据对比",
    "📈 趋势分析",
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

# ========== 航线运营分析 ==========
elif page == "🛫 航线运营":
    st.title("🛫 航线运营分析")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        # ========== 航司分析部分 ==========
        st.subheader("✈️ 航司分析")
        airline_stats = df['航空公司列表'].value_counts().reset_index()
        airline_stats.columns = ['航司', '订单数']

        col_airline1, col_airline2 = st.columns(2)
        with col_airline1:
            fig_airline = px.bar(
                airline_stats.head(10),
                x='航司',
                y='订单数',
                color='订单数',
                color_continuous_scale='blues',
                text='订单数'
            )
            fig_airline.update_traces(textposition='outside')
            fig_airline.update_layout(
                height=350,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=14),
                title_font=dict(color='#00bfff'),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12), tickangle=45),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12))
            )
            st.plotly_chart(fig_airline, use_container_width=True)

        with col_airline2:
            fig_pie = px.pie(
                airline_stats.head(8),
                values='订单数',
                names='航司',
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textfont=dict(color='white', size=12))
            fig_pie.update_layout(
                height=350,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=14),
                title_font=dict(color='#00bfff')
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # ========== 航线分析部分 ==========
        st.subheader("🛫 航线分布")
        df['航线'] = df['出发机场列表'] + ' → ' + df['到达机场列表']

        col_route1, col_route2 = st.columns(2)
        with col_route1:
            st.markdown("**热门出发城市 TOP10**")
            dep_counts = df['出发机场列表'].value_counts().head(10).reset_index()
            dep_counts.columns = ['城市', '订单数']
            fig_dep = px.bar(dep_counts, x='城市', y='订单数', color='订单数', color_continuous_scale='blues', text='订单数')
            fig_dep.update_traces(textposition='outside')
            fig_dep.update_layout(height=300, plot_bgcolor='rgba(10,15,25,0.8)', paper_bgcolor='rgba(10,15,25,0.8)', font=dict(color='#b0d4e6', size=14), title_font=dict(color='#00bfff'), xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)), yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)))
            st.plotly_chart(fig_dep, use_container_width=True)

        with col_route2:
            st.markdown("**热门到达城市 TOP10**")
            arr_counts = df['到达机场列表'].value_counts().head(10).reset_index()
            arr_counts.columns = ['城市', '订单数']
            fig_arr = px.bar(arr_counts, x='城市', y='订单数', color='订单数', color_continuous_scale='oranges', text='订单数')
            fig_arr.update_traces(textposition='outside')
            fig_arr.update_layout(height=300, plot_bgcolor='rgba(10,15,25,0.8)', paper_bgcolor='rgba(10,15,25,0.8)', font=dict(color='#b0d4e6', size=14), title_font=dict(color='#00bfff'), xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)), yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)))
            st.plotly_chart(fig_arr, use_container_width=True)

        st.markdown("**热门航线 TOP15**")
        route_counts = df['航线'].value_counts().head(15).reset_index()
        route_counts.columns = ['航线', '订单数']
        fig_route = px.bar(route_counts, x='航线', y='订单数', color='订单数', color_continuous_scale='viridis', text='订单数')
        fig_route.update_traces(textposition='outside')
        fig_route.update_layout(height=350, plot_bgcolor='rgba(10,15,25,0.8)', paper_bgcolor='rgba(10,15,25,0.8)', font=dict(color='#b0d4e6', size=14), title_font=dict(color='#00bfff'), xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12), tickangle=30), yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickfont=dict(color='#b0d4e6', size=12)))
        st.plotly_chart(fig_route, use_container_width=True)

        st.divider()

        # ========== 航程类型分析 ==========
        st.subheader("🔀 航程类型分析（单程/往返/多程）")
        df['航班数'] = df['航班号列表'].apply(lambda x: len(str(x).split(',')) if pd.notna(x) else 0)
        def classify_trip(seg):
            if seg == 1: return '单程'
            elif seg == 2: return '往返'
            else: return '多程'
        df['航程类型'] = df['航班数'].apply(classify_trip)
        trip_counts = df['航程类型'].value_counts().reset_index()
        trip_counts.columns = ['航程类型', '订单数']

        col_trip1, col_trip2 = st.columns(2)
        with col_trip1:
            fig_trip = px.pie(trip_counts, values='订单数', names='航程类型', hole=0.5, color='航程类型', color_discrete_map={'单程': '#00bfff', '往返': '#ff6b6b', '多程': '#ffd93d'})
            fig_trip.update_traces(textposition='inside', textfont=dict(color='white', size=14))
            fig_trip.update_layout(height=300, plot_bgcolor='rgba(10,15,25,0.8)', paper_bgcolor='rgba(10,15,25,0.8)', font=dict(color='#b0d4e6', size=14), title_font=dict(color='#00bfff'))
            st.plotly_chart(fig_trip, use_container_width=True)

        with col_trip2:
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
elif page == "🤖 自动出票":
    st.title("🤖 今日自动出票概况")

    datafile = get_current_datafile()
    if not datafile:
        st.info("👈 请先上传Excel文件开始分析")
    else:
        df = pd.read_excel(datafile)

        # 失败订单判断：第一次失败原因或失败原因有内容，或有最后锁定人（人工介入）
        df['是否有失败'] = (
            (df['第一次失败原因'].fillna('').str.strip() != '') |
            (df['失败原因'].fillna('').str.strip() != '') |
            (df['最后锁定人'].fillna('').str.strip() != '')
        )

        total_orders = len(df)
        fail_count = df['是否有失败'].sum()
        auto_count = total_orders - fail_count
        auto_rate = (auto_count / total_orders * 100) if total_orders > 0 else 0

        # 判断是否全自动：最后锁定人为空
        df['是否全自动'] = df['最后锁定人'].isna() | (df['最后锁定人'] == '')

        # ========== KPI卡片 ==========
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 总订单", f"{total_orders:,}")
        col2.metric("✅ 自动成功", f"{auto_count:,}")
        col3.metric("❌ 自动失败", f"{fail_count:,}")
        col4.metric("🎯 自动成功率", f"{auto_rate:.1f}%")

        st.divider()

        # ========== 分类函数 ==========
        def classify_failure_stage(reason1, reason2):
            """按业务流程环节分类失败原因 - 优先判断第一次失败原因"""
            r1 = str(reason1).lower()
            r2 = str(reason2).lower()
            if r1:
                if '预定失败' in r1 or '未找到出票规则' in r1 or '自家价格请重新选择出票渠道' in r1 or '春秋官网利润大于' in r1 or '春秋官网 亏损大于' in r1 or '亏损拦截' in r1 or '亏损大于' in r1 or '订单存在重复' in r1 or '获取agoda账号为空' in r1 or '初筛没有匹配出票规则' in r1 or '采购渠道为空' in r1 or '重复预订' in r1:
                    return '📝 预定环节'
                elif '支付失败' in r1 or '支付异常' in r1 or '不支持此类型' in r1 or '不支持该证件类型' in r1 or 'issue card error' in r1:
                    return '💳 支付环节'
                elif '取票失败' in r1 or '出票中' in r1 or '待出票' in r1 or '暂无票号' in r1 or '未发行票证' in r1:
                    return '🎫 取票环节'
                elif '验真失败' in r1 or '验真异常' in r1:
                    return '✅ 验真环节'
                elif '回贴失败' in r1 or '回填原平台失败' in r1:
                    return '📝 回贴环节'
                elif '手工政策' in r1 or '辅营行李订单,人工处理' in r1 or '订单取消' in r1 or '订单处理超时' in r1:
                    return '👤 人工环节'
                elif '原平台状态检测失败' in r1 or '获取userid失败' in r1 or 'ip异常' in r1 or '账号登录状态失效' in r1 or '订单已完结' in r1 or '出票费审核失败' in r1:
                    return '🖥️ 平台环节'
                elif '辅营订单处理失败' in r1:
                    return '📦 辅营环节'
                elif 'cannot invoke' in r1 or 'read timed out' in r1 or '自动扫码未成功' in r1:
                    return '🖥️ 系统环节'
            if r2:
                if '预定失败' in r2 or '未找到出票规则' in r2 or '自家价格请重新选择出票渠道' in r2 or '春秋官网利润大于' in r2 or '春秋官网 亏损大于' in r2 or '亏损拦截' in r2 or '亏损大于' in r2 or '订单存在重复' in r2 or '获取agoda账号为空' in r2 or '初筛没有匹配出票规则' in r2 or '采购渠道为空' in r2 or '重复预订' in r2:
                    return '📝 预定环节'
                elif '支付失败' in r2 or '支付异常' in r2 or '不支持此类型' in r2 or '不支持该证件类型' in r2 or 'issue card error' in r2:
                    return '💳 支付环节'
                elif '取票失败' in r2 or '出票中' in r2 or '待出票' in r2 or '暂无票号' in r2 or '未发行票证' in r2:
                    return '🎫 取票环节'
                elif '验真失败' in r2 or '验真异常' in r2:
                    return '✅ 验真环节'
                elif '回贴失败' in r2 or '回填原平台失败' in r2:
                    return '📝 回贴环节'
                elif '手工政策' in r2 or '辅营行李订单,人工处理' in r2 or '订单取消' in r2 or '订单处理超时' in r2:
                    return '👤 人工环节'
                elif '原平台状态检测失败' in r2 or '获取userid失败' in r2 or 'ip异常' in r2 or '账号登录状态失效' in r2 or '订单已完结' in r2 or '出票费审核失败' in r2:
                    return '🖥️ 平台环节'
                elif '辅营订单处理失败' in r2:
                    return '📦 辅营环节'
                elif 'cannot invoke' in r2 or 'read timed out' in r2 or '自动扫码未成功' in r2:
                    return '🖥️ 系统环节'
            return '❓ 其他'

        df['失败环节'] = df.apply(lambda x: classify_failure_stage(x['第一次失败原因'], x['失败原因']), axis=1)
        failed_df = df[df['是否有失败']].copy()

        # ========== 航司自动成功率 ==========
        st.subheader("✈️ 不同航司的自动成功率（<75%标红）")

        auto_by_airline = df.groupby('航空公司列表').agg(
            总订单=('是否全自动', 'count'),
            自动订单=('是否全自动', 'sum')
        ).reset_index()
        auto_by_airline['成功率'] = (auto_by_airline['自动订单'] / auto_by_airline['总订单'] * 100).round(1)
        auto_by_airline = auto_by_airline.sort_values('成功率', ascending=False)

        def get_color(rate):
            if rate >= 75: return '#2ecc71'
            return '#e74c3c'

        airline_data = auto_by_airline.copy()
        airline_data['颜色'] = airline_data['成功率'].apply(get_color)

        fig_airline = go.Figure()
        fig_airline.add_trace(go.Bar(
            x=airline_data['航空公司列表'],
            y=airline_data['成功率'],
            marker_color=airline_data['颜色'],
            text=airline_data['成功率'].apply(lambda x: f'{x:.1f}%'),
            hovertemplate='<b>%{x}</b><br>成功率: %{y:.1f}%<extra></extra>'
        ))
        fig_airline.add_hline(y=75, line_dash='dash', line_color='gray', line_width=1.5, annotation_text='行业平均 75%')
        fig_airline.update_traces(textposition='inside', textfont=dict(color='white', size=10))
        fig_airline.update_layout(
            height=300,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=12),
            title=dict(text='各航司自动出票成功率', font=dict(color='#00bfff', size=14)),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 105]),
            showlegend=False
        )
        st.plotly_chart(fig_airline, use_container_width=True, config={'displayModeBar': 'hover'})

        st.divider()

        # ========== 采购渠道自动成功率 ==========
        st.subheader("📡 不同采购渠道的自动成功率（<75%标红）")

        auto_by_channel = df.groupby('采购渠道').agg(
            总订单=('是否全自动', 'count'),
            自动订单=('是否全自动', 'sum')
        ).reset_index()
        auto_by_channel['成功率'] = (auto_by_channel['自动订单'] / auto_by_channel['总订单'] * 100).round(1)
        auto_by_channel = auto_by_channel.sort_values('成功率', ascending=False)

        channel_data = auto_by_channel.copy()
        channel_data['颜色'] = channel_data['成功率'].apply(get_color)

        fig_channel = go.Figure()
        fig_channel.add_trace(go.Bar(
            x=channel_data['采购渠道'],
            y=channel_data['成功率'],
            marker_color=channel_data['颜色'],
            text=channel_data['成功率'].apply(lambda x: f'{x:.1f}%'),
            hovertemplate='<b>%{x}</b><br>成功率: %{y:.1f}%<extra></extra>'
        ))
        fig_channel.add_hline(y=75, line_dash='dash', line_color='gray', line_width=1.5, annotation_text='行业平均 75%')
        fig_channel.update_traces(textposition='inside', textfont=dict(color='white', size=10))
        fig_channel.update_layout(
            height=300,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=12),
            title=dict(text='各采购渠道自动出票成功率', font=dict(color='#00bfff', size=14)),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 105]),
            showlegend=False
        )
        st.plotly_chart(fig_channel, use_container_width=True, config={'displayModeBar': 'hover'})

        st.divider()

        # ========== 平台自动出票成功率 ==========
        st.subheader("🖥️ 不同平台的自动出票成功率（<75%标红）")

        auto_by_platform = df.groupby('平台').agg(
            总订单=('是否全自动', 'count'),
            自动订单=('是否全自动', 'sum')
        ).reset_index()
        auto_by_platform['成功率'] = (auto_by_platform['自动订单'] / auto_by_platform['总订单'] * 100).round(1)
        auto_by_platform = auto_by_platform.sort_values('成功率', ascending=False)

        platform_data = auto_by_platform.copy()
        platform_data['颜色'] = platform_data['成功率'].apply(get_color)

        fig_platform = go.Figure()
        fig_platform.add_trace(go.Bar(
            x=platform_data['平台'],
            y=platform_data['成功率'],
            marker_color=platform_data['颜色'],
            text=platform_data['成功率'].apply(lambda x: f'{x:.1f}%'),
            hovertemplate='<b>%{x}</b><br>成功率: %{y:.1f}%<extra></extra>'
        ))
        fig_platform.add_hline(y=75, line_dash='dash', line_color='gray', line_width=1.5, annotation_text='行业平均 75%')
        fig_platform.update_traces(textposition='inside', textfont=dict(color='white', size=10))
        fig_platform.update_layout(
            height=300,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=12),
            title=dict(text='各平台自动出票成功率', font=dict(color='#00bfff', size=14)),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 105]),
            showlegend=False
        )
        st.plotly_chart(fig_platform, use_container_width=True, config={'displayModeBar': 'hover'})

        st.divider()

        # ========== 采购类型自动出票成功率 ==========
        st.subheader("🛒 不同采购类型的自动出票成功率（<75%标红）")

        auto_by_purchase_type = df.groupby('采购类型').agg(
            总订单=('是否全自动', 'count'),
            自动订单=('是否全自动', 'sum')
        ).reset_index()
        auto_by_purchase_type['成功率'] = (auto_by_purchase_type['自动订单'] / auto_by_purchase_type['总订单'] * 100).round(1)
        auto_by_purchase_type = auto_by_purchase_type.sort_values('成功率', ascending=False)

        purchase_type_data = auto_by_purchase_type.copy()
        purchase_type_data['颜色'] = purchase_type_data['成功率'].apply(get_color)

        fig_purchase_type = go.Figure()
        fig_purchase_type.add_trace(go.Bar(
            x=purchase_type_data['采购类型'],
            y=purchase_type_data['成功率'],
            marker_color=purchase_type_data['颜色'],
            text=purchase_type_data['成功率'].apply(lambda x: f'{x:.1f}%'),
            hovertemplate='<b>%{x}</b><br>成功率: %{y:.1f}%<extra></extra>'
        ))
        fig_purchase_type.add_hline(y=75, line_dash='dash', line_color='gray', line_width=1.5, annotation_text='行业平均 75%')
        fig_purchase_type.update_traces(textposition='inside', textfont=dict(color='white', size=10))
        fig_purchase_type.update_layout(
            height=300,
            plot_bgcolor='rgba(10,15,25,0.8)',
            paper_bgcolor='rgba(10,15,25,0.8)',
            font=dict(color='#b0d4e6', size=12),
            title=dict(text='各采购类型自动出票成功率', font=dict(color='#00bfff', size=14)),
            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 105]),
            showlegend=False
        )
        st.plotly_chart(fig_purchase_type, use_container_width=True, config={'displayModeBar': 'hover'})

        st.divider()

        # ========== 失败订单的多维分布分析 ==========
        st.subheader("🔍 失败订单的多维分布分析")

        # 失败订单按航司分布
        fail_by_airline = failed_df['航空公司列表'].value_counts().head(10).reset_index()
        fail_by_airline.columns = ['航司', '失败订单数']

        # 失败订单按平台分布
        fail_by_platform = failed_df['平台'].value_counts().head(10).reset_index()
        fail_by_platform.columns = ['平台', '失败订单数']

        # 失败订单按采购渠道分布
        fail_by_channel = failed_df['采购渠道'].value_counts().head(10).reset_index()
        fail_by_channel.columns = ['采购渠道', '失败订单数']

        col_fail1, col_fail2, col_fail3 = st.columns(3)

        with col_fail1:
            st.markdown("**📋 失败订单航司分布 TOP10**")
            fig_fail_airline = px.bar(
                fail_by_airline,
                x='航司',
                y='失败订单数',
                color='失败订单数',
                color_continuous_scale='redor',
                text='失败订单数'
            )
            fig_fail_airline.update_traces(textposition='outside')
            fig_fail_airline.update_layout(
                height=300,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=11),
                title_font=dict(color='#00bfff', size=12),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
            )
            st.plotly_chart(fig_fail_airline, use_container_width=True)

        with col_fail2:
            st.markdown("**🖥️ 失败订单平台分布 TOP10**")
            fig_fail_platform = px.bar(
                fail_by_platform,
                x='平台',
                y='失败订单数',
                color='失败订单数',
                color_continuous_scale='redor',
                text='失败订单数'
            )
            fig_fail_platform.update_traces(textposition='outside')
            fig_fail_platform.update_layout(
                height=300,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=11),
                title_font=dict(color='#00bfff', size=12),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
            )
            st.plotly_chart(fig_fail_platform, use_container_width=True)

        with col_fail3:
            st.markdown("**📡 失败订单采购渠道分布 TOP10**")
            fig_fail_channel = px.bar(
                fail_by_channel,
                x='采购渠道',
                y='失败订单数',
                color='失败订单数',
                color_continuous_scale='redor',
                text='失败订单数'
            )
            fig_fail_channel.update_traces(textposition='outside')
            fig_fail_channel.update_layout(
                height=300,
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=11),
                title_font=dict(color='#00bfff', size=12),
                xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
                yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
            )
            st.plotly_chart(fig_fail_channel, use_container_width=True)

        st.divider()

        # ========== 失败环节分布 ==========
        st.subheader("🔄 失败环节分布")

        stage_counts = failed_df['失败环节'].value_counts().reset_index()
        stage_counts.columns = ['环节', '订单数']

        col_pie, col_tbl = st.columns([1, 1])
        with col_pie:
            fig_pie = px.pie(
                stage_counts,
                values='订单数',
                names='环节',
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textfont=dict(color='white', size=12))
            fig_pie.update_layout(
                plot_bgcolor='rgba(10,15,25,0.8)',
                paper_bgcolor='rgba(10,15,25,0.8)',
                font=dict(color='#b0d4e6', size=12),
                title=dict(text='失败环节占比', font=dict(color='#00bfff', size=14))
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_tbl:
            st.dataframe(stage_counts, use_container_width=True)

        st.divider()

        # ========== 各环节失败原因详情 ==========
        st.subheader("📋 各环节失败原因详情（🔽按数量排序，可导出）")

        stage_options = ['全部'] + list(stage_counts['环节'])
        selected_stage = st.selectbox("选择环节", options=stage_options)

        if selected_stage == '全部':
            detail_df = failed_df[['订单号', '航空公司列表', '平台', '第一次失败原因', '失败原因', '失败环节']].copy()
        else:
            detail_df = failed_df[failed_df['失败环节'] == selected_stage][['订单号', '航空公司列表', '平台', '第一次失败原因', '失败原因', '失败环节']].copy()

        detail_df.columns = ['订单号', '航司', '平台', '第一次失败原因', '失败原因', '环节']
        detail_df = detail_df.sort_values('环节')

        st.dataframe(detail_df, use_container_width=True)

        # 导出按钮
        if len(detail_df) > 0:
            buffer = BytesIO()
            detail_df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button(
                label="📥 导出环节详情",
                data=buffer,
                file_name="环节失败详情.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.divider()

        # ========== TOP失败原因 ==========
        st.subheader("❌ TOP失败原因（可导出）")

        df['失败原因组合'] = df['第一次失败原因'].fillna('') + ' + ' + df['失败原因'].fillna('')
        df['失败原因组合'] = df['失败原因组合'].apply(lambda x: x if x != ' + ' else '')
        fail_reason_df = df[df['失败原因组合'].str.strip() != ''].copy()
        fail_reason = fail_reason_df['失败原因组合'].value_counts().head(20).reset_index()
        fail_reason.columns = ['失败原因', '订单数']

        st.dataframe(fail_reason, use_container_width=True)

        if len(fail_reason) > 0:
            buffer2 = BytesIO()
            fail_reason.to_excel(buffer2, index=False, engine='openpyxl')
            buffer2.seek(0)
            st.download_button(
                label="📥 导出TOP失败原因",
                data=buffer2,
                file_name="TOP失败原因.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.divider()

        # ========== 出票时长分析（可折叠） ==========
        with st.expander("⏱️ 出票时长分析（点击展开）"):
            df['创建时间_dt'] = pd.to_datetime(df['创建时间'], errors='coerce')
            df['获取票号时间_dt'] = pd.to_datetime(df['上一次获取票号时间'], errors='coerce')
            df['出票时长_小时'] = (df['获取票号时间_dt'] - df['创建时间_dt']).dt.total_seconds() / 3600
            valid_duration = df[df['出票时长_小时'].notna() & (df['出票时长_小时'] > 0)]

            if len(valid_duration) > 0:
                # ========== 基础统计 ==========
                st.markdown("**📊 基础统计**")
                col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                col_t1.metric("📊 平均", f"{valid_duration['出票时长_小时'].mean():.1f}h")
                col_t2.metric("⚡ 最快", f"{valid_duration['出票时长_小时'].min():.1f}h")
                col_t3.metric("🐢 最慢", f"{valid_duration['出票时长_小时'].max():.1f}h")
                col_t4.metric("📈 中位数", f"{valid_duration['出票时长_小时'].median():.1f}h")

                # ========== 出票时长分布直方图 ==========
                st.markdown("**📈 出票时长分布**")
                # 自定义分桶
                bins = [0, 0.1, 0.25, 0.5, 1, 2, 5, 10, float('inf')]
                labels = ['0-6min', '6-15min', '15-30min', '30-60min', '1-2h', '2-5h', '5-10h', '>10h']
                valid_duration['时长区间'] = pd.cut(valid_duration['出票时长_小时'], bins=bins, labels=labels, right=False)
                duration_dist = valid_duration['时长区间'].value_counts().sort_index().reset_index()
                duration_dist.columns = ['时长区间', '订单数']

                col_hist, col_pie = st.columns([1, 1])
                with col_hist:
                    fig_duration_hist = px.bar(
                        duration_dist,
                        x='时长区间',
                        y='订单数',
                        color='订单数',
                        color_continuous_scale='blues',
                        text='订单数'
                    )
                    fig_duration_hist.update_traces(textposition='outside')
                    fig_duration_hist.update_layout(
                        height=280,
                        plot_bgcolor='rgba(10,15,25,0.8)',
                        paper_bgcolor='rgba(10,15,25,0.8)',
                        font=dict(color='#b0d4e6', size=11),
                        title_font=dict(color='#00bfff', size=12),
                        xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
                        yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                    )
                    st.plotly_chart(fig_duration_hist, use_container_width=True)

                with col_pie:
                    fig_duration_pie = px.pie(
                        duration_dist,
                        values='订单数',
                        names='时长区间',
                        hole=0.4
                    )
                    fig_duration_pie.update_traces(textposition='inside', textfont=dict(color='white', size=10))
                    fig_duration_pie.update_layout(
                        height=280,
                        plot_bgcolor='rgba(10,15,25,0.8)',
                        paper_bgcolor='rgba(10,15,25,0.8)',
                        font=dict(color='#b0d4e6', size=11),
                        title_font=dict(color='#00bfff', size=12)
                    )
                    st.plotly_chart(fig_duration_pie, use_container_width=True)

                st.divider()

                # ========== 按航司分析出票时长 ==========
                st.markdown("**✈️ 各航司平均出票时长 TOP10**")
                airline_duration = valid_duration.groupby('航空公司列表')['出票时长_小时'].agg(['mean', 'count']).reset_index()
                airline_duration.columns = ['航司', '平均时长(h)', '样本数']
                airline_duration = airline_duration[airline_duration['样本数'] >= 5]  # 至少5个样本
                airline_duration = airline_duration.sort_values('平均时长(h)', ascending=True).head(10)
                airline_duration['平均时长(h)'] = airline_duration['平均时长(h)'].round(2)

                fig_airline_duration = px.bar(
                    airline_duration,
                    x='航司',
                    y='平均时长(h)',
                    color='平均时长(h)',
                    color_continuous_scale='rdylgn_r',  # 时间越短越绿
                    text=airline_duration['平均时长(h)'].apply(lambda x: f'{x:.2f}h')
                )
                fig_airline_duration.update_traces(textposition='outside')
                fig_airline_duration.update_layout(
                    height=280,
                    plot_bgcolor='rgba(10,15,25,0.8)',
                    paper_bgcolor='rgba(10,15,25,0.8)',
                    font=dict(color='#b0d4e6', size=11),
                    title_font=dict(color='#00bfff', size=12),
                    xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
                    yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                )
                st.plotly_chart(fig_airline_duration, use_container_width=True)

                st.divider()

                # ========== 按采购渠道分析出票时长 ==========
                st.markdown("**📡 各采购渠道平均出票时长**")
                channel_duration = valid_duration.groupby('采购渠道')['出票时长_小时'].agg(['mean', 'count']).reset_index()
                channel_duration.columns = ['采购渠道', '平均时长(h)', '样本数']
                channel_duration = channel_duration[channel_duration['样本数'] >= 3]  # 至少3个样本
                channel_duration = channel_duration.sort_values('平均时长(h)', ascending=True)
                channel_duration['平均时长(h)'] = channel_duration['平均时长(h)'].round(2)

                fig_channel_duration = px.bar(
                    channel_duration,
                    x='采购渠道',
                    y='平均时长(h)',
                    color='平均时长(h)',
                    color_continuous_scale='rdylgn_r',
                    text=channel_duration['平均时长(h)'].apply(lambda x: f'{x:.2f}h')
                )
                fig_channel_duration.update_traces(textposition='outside')
                fig_channel_duration.update_layout(
                    height=280,
                    plot_bgcolor='rgba(10,15,25,0.8)',
                    paper_bgcolor='rgba(10,15,25,0.8)',
                    font=dict(color='#b0d4e6', size=11),
                    title_font=dict(color='#00bfff', size=12),
                    xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=45),
                    yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                )
                st.plotly_chart(fig_channel_duration, use_container_width=True)

                st.divider()

                # ========== 超时订单筛选 ==========
                st.markdown("**⏰ 超时订单筛选**")
                threshold_hours = st.slider("超时筛选（小时）", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
                overtime = valid_duration[valid_duration['出票时长_小时'] > threshold_hours].head(50)
                if len(overtime) > 0:
                    overtime_list = overtime[['订单号', '航空公司列表', '采购渠道', '出票时长_小时']].copy()
                    overtime_list.columns = ['订单号', '航司', '采购渠道', '出票时长(小时)']
                    overtime_list['出票时长(小时)'] = overtime_list['出票时长(小时)'].round(2)
                    st.dataframe(overtime_list, use_container_width=True)
                    st.info(f"共 {len(overtime)} 条超时订单（>{threshold_hours}小时）")
                else:
                    st.success(f"✅ 暂无超时订单")
            else:
                st.warning("⚠️ 暂无有效数据")

# ========== 数据对比 ==========
elif page == "📊 数据对比":
    st.title("📊 数据对比")

    # 获取历史记录
    history = get_all_history()

    if len(history) < 2:
        st.info("⚠️ 需要至少2条历史记录才能进行对比，请先上传更多数据")
    else:
        # 时间维度筛选
        st.subheader("⏱️ 选择时间维度")
        time_filter = st.radio(
            "时间维度",
            options=["天", "周", "月"],
            horizontal=True,
            index=0,
            key="time_filter"
        )
        st.divider()

        # 从文件名中提取日期
        def get_period_key(file_name, time_filter):
            from datetime import datetime
            import re
            try:
                # 匹配文件名中的日期格式 YYYY-MM-DD 或 YYYYMMDD
                match = re.search(r'(\d{4})-?(\d{2})-?(\d{2})', str(file_name))
                if match:
                    dt = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                    if time_filter == '天':
                        return dt.strftime('%Y-%m-%d')
                    elif time_filter == '周':
                        year, week, _ = dt.isocalendar()
                        return f"{year}-W{week:02d}"
                    else:  # 月
                        return dt.strftime('%Y-%m')
                # 如果没匹配到日期，返回文件名作为唯一标识
                return file_name or '未知'
            except:
                return file_name or '未知'

        # 按周期聚合历史记录
        def aggregate_by_period(history_records, time_filter):
            import json
            period_data = {}
            for r in history_records:
                file_name = r[2] if len(r) > 2 else ''  # file_name 在 index 2
                period_key = get_period_key(file_name, time_filter)
                if period_key not in period_data:
                    period_data[period_key] = {
                        'record': r,
                        'file_names': [r[2] or '未命名']
                    }
                else:
                    # 合并数据
                    existing_record = period_data[period_key]['record']
                    new_record = list(existing_record)
                    new_record[3] = (existing_record[3] or 0) + (r[3] or 0)  # order_count
                    new_record[4] = (existing_record[4] or 0) + (r[4] or 0)  # total_profit
                    new_record[5] = (existing_record[5] or 0) + (r[5] or 0)  # total_amount
                    # 合并data_json
                    existing_json = existing_record[7] if len(existing_record) > 7 else '[]'
                    new_json = r[7] if len(r) > 7 else '[]'
                    try:
                        existing_list = json.loads(existing_json) if existing_json else []
                        new_list = json.loads(new_json) if new_json else []
                        merged = existing_list + new_list
                        new_record[7] = json.dumps(merged, ensure_ascii=False)
                    except:
                        pass
                    period_data[period_key]['record'] = tuple(new_record)
                    period_data[period_key]['file_names'].append(r[2] or '未命名')

            return period_data

        # 执行聚合
        period_data = aggregate_by_period(history, time_filter)

        # 构建选项（显示周期名称）
        history_options = {}
        for period, data in period_data.items():
            file_name = data['file_names'][0] if len(data['file_names']) == 1 else f"{data['file_names'][0]} 等"
            history_options[data['record'][0]] = f"{period} - {file_name}"

        if len(history_options) < 2:
            st.info(f"⚠️ 当前时间维度「{time_filter}」下只有 {len(history_options)} 条记录，需要至少2条才能对比")
        else:
            st.subheader("📋 选择对比批次")

            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                baseline_id = st.selectbox(
                    "选择基线批次（参考）",
                    options=list(history_options.keys()),
                    format_func=lambda x: history_options[x],
                    key="baseline_select"
                )
            with col_sel2:
                compare_id = st.selectbox(
                    "选择对比批次",
                    options=list(history_options.keys()),
                    format_func=lambda x: history_options[x],
                    key="compare_select"
                )

            st.divider()

            # 加载数据
            df_baseline = get_history_data(baseline_id)
            df_compare = get_history_data(compare_id)

            if df_baseline is not None and df_compare is not None:
                # ========== KPI 对比 ==========
                st.subheader("📊 核心KPI对比")

                # 计算基线数据
                b_total = len(df_baseline)
                b_profit = pd.to_numeric(df_baseline['利润'], errors='coerce').sum()
                b_avg_profit = pd.to_numeric(df_baseline['利润'], errors='coerce').mean()
                b_is_auto = df_baseline['最后锁定人'].isna() | (df_baseline['最后锁定人'] == '')
                b_auto_count = b_is_auto.sum()
                b_auto_rate = (b_auto_count / b_total * 100) if b_total > 0 else 0

                # 计算对比数据
                c_total = len(df_compare)
                c_profit = pd.to_numeric(df_compare['利润'], errors='coerce').sum()
                c_avg_profit = pd.to_numeric(df_compare['利润'], errors='coerce').mean()
                c_is_auto = df_compare['最后锁定人'].isna() | (df_compare['最后锁定人'] == '')
                c_auto_count = c_is_auto.sum()
                c_auto_rate = (c_auto_count / c_total * 100) if c_total > 0 else 0

                # 对比卡片 - 订单总数
                def delta_icon(v1, v2):
                    if v1 > v2: return "↑"
                    elif v1 < v2: return "↓"
                    return "→"

                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                with col_kpi1:
                    st.metric("📦 订单总数", f"{c_total:,}", delta=f"{delta_icon(c_total, b_total)}{abs(c_total - b_total):,}")
                with col_kpi2:
                    st.metric("💰 总利润", f"¥{c_profit:,.0f}", delta=f"{delta_icon(c_profit, b_profit)}{abs(c_profit - b_profit):,.0f}")
                with col_kpi3:
                    st.metric("📊 平均利润", f"¥{c_avg_profit:.2f}", delta=f"{delta_icon(c_avg_profit, b_avg_profit)}{abs(c_avg_profit - b_avg_profit):.2f}")
                with col_kpi4:
                    st.metric("🤖 自动出票成功率", f"{c_auto_rate:.1f}%", delta=f"{delta_icon(c_auto_rate, b_auto_rate)}{abs(c_auto_rate - b_auto_rate):.1f}%")

                st.divider()

                # ========== 自动出票成功率详细对比 ==========
                st.subheader("🤖 自动出票成功率详细对比")

                col_auto1, col_auto2 = st.columns(2)
                with col_auto1:
                    # 全自动成功数 vs 需人工介入
                    auto_compare_data = pd.DataFrame({
                        '类型': ['全自动成功', '需人工介入'],
                        '基线批次': [b_auto_count, b_total - b_auto_count],
                        '对比批次': [c_auto_count, c_total - c_auto_count]
                    })
                    fig_auto_compare = go.Figure()
                    fig_auto_compare.add_trace(go.Bar(
                        name='基线批次', x=auto_compare_data['类型'],
                        y=auto_compare_data['基线批次'],
                        marker_color='#00bfff', text=auto_compare_data['基线批次']
                    ))
                    fig_auto_compare.add_trace(go.Bar(
                        name='对比批次', x=auto_compare_data['类型'],
                        y=auto_compare_data['对比批次'],
                        marker_color='#ff6b6b', text=auto_compare_data['对比批次']
                    ))
                    fig_auto_compare.update_layout(
                        barmode='group', height=350,
                        plot_bgcolor='rgba(10,15,25,0.8)',
                        paper_bgcolor='rgba(10,15,25,0.8)',
                        font=dict(color='#b0d4e6', size=14),
                        title_font=dict(color='#00bfff'),
                        xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff'),
                        yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                    )
                    st.plotly_chart(fig_auto_compare, use_container_width=True)

                with col_auto2:
                    # 成功率对比
                    rate_compare_data = pd.DataFrame({
                        '批次': ['基线批次', '对比批次'],
                        '成功率': [b_auto_rate, c_auto_rate]
                    })
                    colors = ['#00bfff', '#ff6b6b']
                    fig_rate_compare = px.bar(
                        rate_compare_data, x='批次', y='成功率',
                        color='批次', color_discrete_map={'基线批次': '#00bfff', '对比批次': '#ff6b6b'},
                        text=[f'{r:.1f}%' for r in rate_compare_data['成功率']]
                    )
                    fig_rate_compare.update_traces(textposition='outside')
                    fig_rate_compare.update_layout(
                        height=350,
                        plot_bgcolor='rgba(10,15,25,0.8)',
                        paper_bgcolor='rgba(10,15,25,0.8)',
                        font=dict(color='#b0d4e6', size=14),
                        title_font=dict(color='#00bfff'),
                        xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff'),
                        yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 100])
                    )
                    st.plotly_chart(fig_rate_compare, use_container_width=True)

                st.divider()

                # ========== 航司分布对比 ==========
                st.subheader("✈️ 航司订单分布对比（TOP 5）")

                b_airline = df_baseline['航空公司列表'].value_counts().head(5).reset_index()
                b_airline.columns = ['航司', '基线订单']
                c_airline = df_compare['航空公司列表'].value_counts().head(5).reset_index()
                c_airline.columns = ['航司', '对比订单']

                # 合并两个航司分布
                all_airlines = set(b_airline['航司'].tolist() + c_airline['航司'].tolist())
                airline_merge = pd.DataFrame({'航司': list(all_airlines)})
                airline_merge = airline_merge.merge(b_airline, on='航司', how='left').fillna(0)
                airline_merge = airline_merge.merge(c_airline, on='航司', how='left').fillna(0)
                airline_merge = airline_merge.sort_values('对比订单', ascending=False).head(5)

                col_airline_chart, col_airline_table = st.columns([2, 1])

                with col_airline_chart:
                    fig_airline_compare = go.Figure()
                    fig_airline_compare.add_trace(go.Bar(
                        name='基线批次', x=airline_merge['航司'],
                        y=airline_merge['基线订单'],
                        marker_color='#00bfff', text=airline_merge['基线订单'].astype(int)
                    ))
                    fig_airline_compare.add_trace(go.Bar(
                        name='对比批次', x=airline_merge['航司'],
                        y=airline_merge['对比订单'],
                        marker_color='#ff6b6b', text=airline_merge['对比订单'].astype(int)
                    ))
                    fig_airline_compare.update_layout(
                        barmode='group', height=350,
                        plot_bgcolor='rgba(10,15,25,0.8)',
                        paper_bgcolor='rgba(10,15,25,0.8)',
                        font=dict(color='#b0d4e6', size=14),
                        title_font=dict(color='#00bfff'),
                        xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=30),
                        yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                    )
                    st.plotly_chart(fig_airline_compare, use_container_width=True)

                with col_airline_table:
                    airline_merge['基线订单'] = airline_merge['基线订单'].astype(int)
                    airline_merge['对比订单'] = airline_merge['对比订单'].astype(int)
                    airline_merge['差异'] = airline_merge['对比订单'] - airline_merge['基线订单']
                    airline_merge['差异'] = airline_merge['差异'].apply(lambda x: f"{'+' if x > 0 else ''}{x}")
                    st.dataframe(airline_merge.rename(columns={'航司': '航司'}), use_container_width=True)

                st.divider()

                # ========== 平台分布对比 ==========
                st.subheader("🖥️ 平台订单分布对比（TOP 5）")

                b_platform = df_baseline['平台'].value_counts().head(5).reset_index()
                b_platform.columns = ['平台', '基线订单']
                c_platform = df_compare['平台'].value_counts().head(5).reset_index()
                c_platform.columns = ['平台', '对比订单']

                all_platforms = set(b_platform['平台'].tolist() + c_platform['平台'].tolist())
                platform_merge = pd.DataFrame({'平台': list(all_platforms)})
                platform_merge = platform_merge.merge(b_platform, on='平台', how='left').fillna(0)
                platform_merge = platform_merge.merge(c_platform, on='平台', how='left').fillna(0)
                platform_merge = platform_merge.sort_values('对比订单', ascending=False).head(5)

                col_platform_chart, col_platform_table = st.columns([2, 1])

                with col_platform_chart:
                    fig_platform_compare = go.Figure()
                    fig_platform_compare.add_trace(go.Bar(
                        name='基线批次', x=platform_merge['平台'],
                        y=platform_merge['基线订单'],
                        marker_color='#00bfff', text=platform_merge['基线订单'].astype(int)
                    ))
                    fig_platform_compare.add_trace(go.Bar(
                        name='对比批次', x=platform_merge['平台'],
                        y=platform_merge['对比订单'],
                        marker_color='#ff6b6b', text=platform_merge['对比订单'].astype(int)
                    ))
                    fig_platform_compare.update_layout(
                        barmode='group', height=350,
                        plot_bgcolor='rgba(10,15,25,0.8)',
                        paper_bgcolor='rgba(10,15,25,0.8)',
                        font=dict(color='#b0d4e6', size=14),
                        title_font=dict(color='#00bfff'),
                        xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=30),
                        yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                    )
                    st.plotly_chart(fig_platform_compare, use_container_width=True)

                with col_platform_table:
                    platform_merge['基线订单'] = platform_merge['基线订单'].astype(int)
                    platform_merge['对比订单'] = platform_merge['对比订单'].astype(int)
                    platform_merge['差异'] = platform_merge['对比订单'] - platform_merge['基线订单']
                    platform_merge['差异'] = platform_merge['差异'].apply(lambda x: f"{'+' if x > 0 else ''}{x}")
                    st.dataframe(platform_merge.rename(columns={'平台': '平台'}), use_container_width=True)

# ========== 历史数据 ==========
elif page == "📚 历史数据":
    st.title("📚 历史数据")

    # 获取历史记录
    history = get_all_history()

    if len(history) == 0:
        st.info("暂无历史记录，上传Excel文件后会保存到历史记录")
    else:
        st.subheader("📋 历史记录列表")

        # 展示历史记录表格（只显示必要字段）
        # history 返回: id(0), upload_date(1), file_name(2), order_count(3), total_profit(4), total_amount(5), created_at(6), data_json(7)
        history_df = pd.DataFrame([(r[1], r[2], r[3], r[4], r[5]) for r in history],
                                columns=['上传日期', '文件名', '订单数', '总利润', '总金额'])
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
                    st.success(f"✅ 已加载 {len(df_hist)} 条订单数据")
                else:
                    st.error("❌ 加载失败")

        st.divider()

        # 删除历史记录
        st.subheader("🗑️ 删除历史数据")
        del_options = {r[0]: r[2] or '未命名' for r in history}
        del_id = st.selectbox("选择要删除的记录", options=list(del_options.keys()), format_func=lambda x: del_options[x])
        if st.button("删除该记录", type="secondary"):
            delete_history(del_id)
            st.success("已删除")
            st.rerun()

# ========== 趋势分析 ==========
elif page == "📈 趋势分析":
    st.title("📈 趋势分析")

    # 获取历史记录
    history = get_all_history()

    if len(history) < 2:
        st.info("⚠️ 需要至少2条历史记录才能进行趋势分析，请先上传更多数据")
    else:
        # 时间维度筛选
        st.subheader("⏱️ 选择时间维度")
        time_filter = st.radio(
            "时间维度",
            options=["天", "周", "月"],
            horizontal=True,
            index=0,
            key="trend_time_filter"
        )
        st.divider()

        # 从文件名中提取日期
        def get_period_key(file_name, time_filter):
            from datetime import datetime
            import re
            try:
                # 匹配文件名中的日期格式 YYYY-MM-DD 或 YYYYMMDD
                match = re.search(r'(\d{4})-?(\d{2})-?(\d{2})', str(file_name))
                if match:
                    dt = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                    if time_filter == '天':
                        return dt.strftime('%Y-%m-%d')
                    elif time_filter == '周':
                        year, week, _ = dt.isocalendar()
                        return f"{year}-W{week:02d}"
                    else:  # 月
                        return dt.strftime('%Y-%m')
                # 如果没匹配到日期，返回文件名作为唯一标识
                return file_name or '未知'
            except:
                return file_name or '未知'

        # 按周期聚合历史记录
        def aggregate_by_period(history_records, time_filter):
            import json
            period_data = {}
            for r in history_records:
                file_name = r[2] if len(r) > 2 else ''  # file_name 在 index 2
                period_key = get_period_key(file_name, time_filter)
                if period_key not in period_data:
                    period_data[period_key] = {
                        'record': r,
                        'file_names': [r[2] or '未命名']
                    }
                else:
                    existing_record = period_data[period_key]['record']
                    new_record = list(existing_record)
                    new_record[3] = (existing_record[3] or 0) + (r[3] or 0)
                    new_record[4] = (existing_record[4] or 0) + (r[4] or 0)
                    new_record[5] = (existing_record[5] or 0) + (r[5] or 0)
                    existing_json = existing_record[7] if len(existing_record) > 7 else '[]'
                    new_json = r[7] if len(r) > 7 else '[]'
                    try:
                        existing_list = json.loads(existing_json) if existing_json else []
                        new_list = json.loads(new_json) if new_json else []
                        merged = existing_list + new_list
                        new_record[7] = json.dumps(merged, ensure_ascii=False)
                    except:
                        pass
                    period_data[period_key]['record'] = tuple(new_record)
                    period_data[period_key]['file_names'].append(r[2] or '未命名')
            return period_data

        # 执行聚合
        period_data = aggregate_by_period(history, time_filter)

        # 按时间排序
        sorted_periods = sorted(period_data.keys(), reverse=True)

        if len(sorted_periods) < 2:
            st.info(f"⚠️ 当前时间维度「{time_filter}」下只有 {len(sorted_periods)} 条记录，需要至少2条才能分析趋势")
        else:
            # 选择要分析的批次（多选）
            st.subheader("📋 选择要分析的批次")
            default_selected = sorted_periods[:min(5, len(sorted_periods))]
            selected_periods = st.multiselect(
                "选择批次（按时间倒序，默认最近5个）",
                options=sorted_periods,
                default=default_selected,
                format_func=lambda x: f"{x} - {period_data[x]['file_names'][0]}"
            )

            if len(selected_periods) < 2:
                st.warning("⚠️ 请至少选择2个批次进行趋势分析")
            else:
                # 计算每个批次的指标
                trend_data = []
                for period in selected_periods:
                    record = period_data[period]['record']
                    data_json = record[7] if len(record) > 7 else '[]'
                    import json
                    try:
                        df = pd.read_json(data_json, orient='records')
                    except:
                        continue

                    total = len(df)
                    profit = pd.to_numeric(df['利润'], errors='coerce').sum()
                    avg_profit = pd.to_numeric(df['利润'], errors='coerce').mean()
                    is_auto = df['最后锁定人'].isna() | (df['最后锁定人'] == '')
                    auto_count = is_auto.sum()
                    auto_rate = (auto_count / total * 100) if total > 0 else 0

                    trend_data.append({
                        '周期': period,
                        '订单总数': total,
                        '总利润': profit,
                        '平均利润': avg_profit,
                        '自动出票成功率': auto_rate
                    })

                if len(trend_data) < 2:
                    st.error("❌ 数据不足，无法生成趋势图")
                else:
                    trend_df = pd.DataFrame(trend_data)
                    trend_df = trend_df.sort_values('周期', ascending=True)

                    # ========== KPI 趋势折线图 ==========
                    st.subheader("📊 核心指标趋势")

                    col_chart1, col_chart2 = st.columns(2)

                    with col_chart1:
                        # 订单总数趋势
                        fig_orders = px.line(
                            trend_df,
                            x='周期',
                            y='订单总数',
                            markers=True,
                            text=trend_df['订单总数']
                        )
                        fig_orders.update_traces(
                            line_color='#00bfff',
                            marker_color='#00ffff',
                            textposition='top center',
                            textfont=dict(color='#b0d4e6', size=12)
                        )
                        fig_orders.update_layout(
                            height=350,
                            plot_bgcolor='rgba(10,15,25,0.8)',
                            paper_bgcolor='rgba(10,15,25,0.8)',
                            font=dict(color='#b0d4e6', size=14),
                            title_font=dict(color='#00bfff'),
                            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=30),
                            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                        )
                        st.plotly_chart(fig_orders, use_container_width=True)

                    with col_chart2:
                        # 自动出票成功率趋势
                        fig_auto_rate = px.line(
                            trend_df,
                            x='周期',
                            y='自动出票成功率',
                            markers=True,
                            text=[f'{r:.1f}%' for r in trend_df['自动出票成功率']]
                        )
                        fig_auto_rate.update_traces(
                            line_color='#ff6b6b',
                            marker_color='#ff9999',
                            textposition='top center',
                            textfont=dict(color='#b0d4e6', size=12)
                        )
                        fig_auto_rate.update_layout(
                            height=350,
                            plot_bgcolor='rgba(10,15,25,0.8)',
                            paper_bgcolor='rgba(10,15,25,0.8)',
                            font=dict(color='#b0d4e6', size=14),
                            title_font=dict(color='#00bfff'),
                            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=30),
                            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', range=[0, 100])
                        )
                        st.plotly_chart(fig_auto_rate, use_container_width=True)

                    col_chart3, col_chart4 = st.columns(2)

                    with col_chart3:
                        # 总利润趋势
                        fig_profit = px.line(
                            trend_df,
                            x='周期',
                            y='总利润',
                            markers=True,
                            text=[f'¥{p:,.0f}' for p in trend_df['总利润']]
                        )
                        fig_profit.update_traces(
                            line_color='#ffd93d',
                            marker_color='#ffe066',
                            textposition='top center',
                            textfont=dict(color='#b0d4e6', size=12)
                        )
                        fig_profit.update_layout(
                            height=350,
                            plot_bgcolor='rgba(10,15,25,0.8)',
                            paper_bgcolor='rgba(10,15,25,0.8)',
                            font=dict(color='#b0d4e6', size=14),
                            title_font=dict(color='#00bfff'),
                            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=30),
                            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                        )
                        st.plotly_chart(fig_profit, use_container_width=True)

                    with col_chart4:
                        # 平均利润趋势
                        fig_avg_profit = px.line(
                            trend_df,
                            x='周期',
                            y='平均利润',
                            markers=True,
                            text=[f'¥{p:.2f}' for p in trend_df['平均利润']]
                        )
                        fig_avg_profit.update_traces(
                            line_color='#4ecdc4',
                            marker_color='#7ee8e0',
                            textposition='top center',
                            textfont=dict(color='#b0d4e6', size=12)
                        )
                        fig_avg_profit.update_layout(
                            height=350,
                            plot_bgcolor='rgba(10,15,25,0.8)',
                            paper_bgcolor='rgba(10,15,25,0.8)',
                            font=dict(color='#b0d4e6', size=14),
                            title_font=dict(color='#00bfff'),
                            xaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff', tickangle=30),
                            yaxis=dict(gridcolor='rgba(0,191,255,0.1)', linecolor='#00bfff')
                        )
                        st.plotly_chart(fig_avg_profit, use_container_width=True)

                    st.divider()

                    # ========== 数据汇总表格 ==========
                    st.subheader("📋 趋势数据汇总")

                    summary_df = trend_df.copy()
                    summary_df['总利润'] = summary_df['总利润'].apply(lambda x: f"¥{x:,.2f}")
                    summary_df['平均利润'] = summary_df['平均利润'].apply(lambda x: f"¥{x:.2f}")
                    summary_df['自动出票成功率'] = summary_df['自动出票成功率'].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(summary_df, use_container_width=True)