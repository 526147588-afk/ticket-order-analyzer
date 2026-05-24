import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analyzer import TicketOrderAnalyzer
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="出票订单数据分析工具", layout="wide")

# 颜色常量
PRIMARY_COLOR = "#1E3A5F"
SECONDARY_COLOR = "#3498DB"

@st.cache_data
def load_analyzer(file_path):
    analyzer = TicketOrderAnalyzer()
    analyzer.load_data(file_path)
    return analyzer

st.title("出票订单数据分析工具 v1.0")

# 侧边栏
st.sidebar.title("导航")
page = st.sidebar.radio(
    "选择功能",
    ["📊 数据概览", "📈 航司分析", "🛫 航线分析", "🔄 航程类型", "💰 财务统计", "⚠️ 失败分析", "📋 数据明细"]
)

# 文件上传
uploaded_file = st.sidebar.file_uploader("上传Excel文件", type=["xlsx", "xls"])

if uploaded_file:
    # 保存文件
    with open("temp_data.xlsx", "wb") as f:
        f.write(uploaded_file.getbuffer())

    analyzer = load_analyzer("temp_data.xlsx")
    st.sidebar.success(f"已加载: {uploaded_file.name}")
    st.sidebar.info(f"总订单: {analyzer.total:,}")

    if page == "📊 数据概览":
        st.header("数据概览")

        overview = analyzer.get_overview()
        platform_stats = analyzer.get_platform_stats()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("总订单数", f"{overview.get('总订单数', 0):,}")
        col2.metric("总支付金额", f"¥{overview.get('总支付金额', 0):,.2f}")
        col3.metric("总利润", f"¥{overview.get('总利润', 0):,.2f}")
        col4.metric("平均利润", f"¥{overview.get('平均利润', 0):.2f}")

        st.subheader("平台订单分布")
        fig = px.pie(
            names=list(platform_stats.keys()),
            values=list(platform_stats.values()),
            title="平台订单占比"
        )
        st.plotly_chart(fig, use_container_width=True)

    elif page == "📈 航司分析":
        st.header("航司分析")

        stats = analyzer.get_airline_stats()
        cross = analyzer.get_airline_platform_cross()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("航司订单排名 TOP 20")
            df_stats = pd.DataFrame(stats[:20])
            st.dataframe(df_stats, use_container_width=True)

        with col2:
            st.subheader("航司×平台 交叉分析 TOP 30")
            df_cross = pd.DataFrame(cross[:30])
            st.dataframe(df_cross, use_container_width=True)

        # 柱状图
        st.subheader("航司订单量可视化")
        fig = px.bar(
            df_stats.head(10),
            x="航司",
            y="订单数",
            color="航司",
            title="TOP 10 航司订单量"
        )
        st.plotly_chart(fig, use_container_width=True)

    elif page == "🛫 航线分析":
        st.header("航线分析")

        stats = analyzer.get_route_stats()
        df_route = pd.DataFrame(stats[:50])

        st.dataframe(df_route, use_container_width=True)

        # 柱状图
        st.subheader("TOP 20 航线订单量")
        fig = px.bar(
            df_route.head(20),
            x="航线",
            y="订单数",
            title="TOP 20 航线"
        )
        st.plotly_chart(fig, use_container_width=True)

    elif page == "🔄 航程类型":
        st.header("航程类型分析")

        trip_stats = analyzer.get_trip_type_stats()
        airline_trip = analyzer.get_airline_trip_type()
        platform_trip = analyzer.get_platform_trip_type()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("航程类型分布")
            fig = px.pie(
                names=list(trip_stats.keys()),
                values=list(trip_stats.values()),
                title="单程/往返/多程占比"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("各航司航程类型")
            df_at = pd.DataFrame(airline_trip)
            st.dataframe(df_at, use_container_width=True)

        st.subheader("各平台航程类型")
        df_pt = pd.DataFrame(platform_trip)
        st.dataframe(df_pt, use_container_width=True)

    elif page == "💰 财务统计":
        st.header("财务统计")

        finance = analyzer.get_finance_stats()
        airline_profit = analyzer.get_airline_profit()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("总支付金额", f"¥{finance.get('总支付金额', 0):,.2f}")
        col2.metric("盈利订单", f"{finance.get('盈利订单数', 0):,} 单")
        col3.metric("亏损订单", f"{finance.get('亏损订单数', 0):,} 单")
        col4.metric("平均利润", f"¥{finance.get('平均利润', 0):.2f}")

        st.subheader("各航司利润统计 TOP 20")
        df_profit = pd.DataFrame(airline_profit[:20])
        st.dataframe(df_profit, use_container_width=True)

        # 利润柱状图
        fig = px.bar(
            df_profit.head(10),
            x="航司",
            y="总利润",
            color="航司",
            title="TOP 10 航司总利润"
        )
        st.plotly_chart(fig, use_container_width=True)

    elif page == "⚠️ 失败分析":
        st.header("失败订单分析")

        failure = analyzer.get_failure_stats()
        df_failure = pd.DataFrame(failure[:30])

        st.dataframe(df_failure, use_container_width=True)

        # 图表
        if len(df_failure) > 0:
            fig = px.bar(
                df_failure.head(15),
                x="失败原因",
                y="订单数",
                title="TOP 15 失败原因"
            )
            st.plotly_chart(fig, use_container_width=True)

    elif page == "📋 数据明细":
        st.header("数据明细")

        page_num = st.number_input("页码", min_value=1, value=1, step=1)
        data, total = analyzer.get_order_details(int(page_num), 100)
        df_detail = pd.DataFrame(data)

        st.info(f"共 {total:,} 条记录，显示第 {int(page_num)} 页（每页100条）")
        st.dataframe(df_detail, use_container_width=True, height=600)

else:
    st.info("👈 请上传Excel文件开始分析")

    # 显示示例
    st.subheader("功能说明")
    st.markdown("""
    - **📊 数据概览**: 总订单数、总金额、利润统计、平台分布饼图
    - **📈 航司分析**: 航司订单排名、航司×平台交叉分析
    - **🛫 航线分析**: 航线订单量排名
    - **🔄 航程类型**: 单程/往返/多程分布
    - **💰 财务统计**: 利润分析、各航司利润
    - **⚠️ 失败分析**: 失败原因统计
    - **📋 数据明细**: 分页查看原始数据
    """)