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
    ["📊 数据概览", "📈 航司分析", "🛫 航线分析", "🔄 航程类型",
     "📅 时间分析", "💰 利润分析", "💳 支付分析", "✈️ 城市分析",
     "👥 乘客分析", "⚠️ 失败分析", "🤖 全自动出票", "📋 数据明细"]
)

# 文件上传
uploaded_file = st.sidebar.file_uploader("上传Excel文件", type=["xlsx", "xls"])

if uploaded_file:
    with open("temp_data.xlsx", "wb") as f:
        f.write(uploaded_file.getbuffer())

    analyzer = load_analyzer("temp_data.xlsx")
    st.sidebar.success(f"已加载: {uploaded_file.name}")
    st.sidebar.info(f"总订单: {analyzer.total:,}")

    # ========== 1. 数据概览 ==========
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

    # ========== 2. 航司分析 ==========
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

        st.subheader("航司订单量可视化")
        fig = px.bar(
            df_stats.head(10),
            x="航司",
            y="订单数",
            color="航司",
            title="TOP 10 航司订单量",
            text="订单数"
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    # ========== 3. 航线分析 ==========
    elif page == "🛫 航线分析":
        st.header("航线分析")

        stats = analyzer.get_route_stats()
        df_route = pd.DataFrame(stats[:50])

        st.dataframe(df_route, use_container_width=True)

        st.subheader("TOP 20 航线订单量")
        fig = px.bar(
            df_route.head(20),
            x="航线",
            y="订单数",
            title="TOP 20 航线",
            text="订单数"
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    # ========== 4. 航程类型 ==========
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

    # ========== 5. 时间分析 ==========
    elif page == "📅 时间分析":
        st.header("时间维度分析")

        hourly = analyzer.get_hourly_stats()
        df_hourly = pd.DataFrame(hourly)

        st.subheader("按小时统计订单量")
        fig = px.bar(
            df_hourly,
            x="小时",
            y="订单数",
            title="24小时订单分布",
            color="订单数",
            color_continuous_scale="blues",
            text="订单数"
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(xaxis_tickmode='linear', xaxis_dtick=1)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_hourly, use_container_width=True)

    # ========== 6. 利润分析 ==========
    elif page == "💰 利润分析":
        st.header("利润维度分析")

        finance = analyzer.get_finance_stats()
        airline_profit = analyzer.get_airline_profit()
        platform_profit = analyzer.get_platform_profit()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("总利润", f"¥{finance.get('总利润', 0):,.2f}")
        col2.metric("平均利润", f"¥{finance.get('平均利润', 0):.2f}")
        col3.metric("盈利订单", f"{finance.get('盈利订单数', 0):,} 单 ({finance.get('盈利订单数', 0)/analyzer.total*100:.1f}%)")
        col4.metric("亏损订单", f"{finance.get('亏损订单数', 0):,} 单 ({finance.get('亏损订单数', 0)/analyzer.total*100:.1f}%)")

        col5, col6 = st.columns(2)

        with col5:
            st.subheader("各航司利润统计 TOP 20")
            df_profit = pd.DataFrame(airline_profit[:20])
            st.dataframe(df_profit, use_container_width=True)

        with col6:
            st.subheader("各平台利润统计")
            df_platform_profit = pd.DataFrame(platform_profit)
            st.dataframe(df_platform_profit, use_container_width=True)

        st.subheader("航司利润对比")
        fig = px.bar(
            df_profit.head(15),
            x="航司",
            y="总利润",
            color="总利润",
            title="TOP 15 航司总利润（盈利为正，亏损为负）",
            color_continuous_scale="RdYlGn",
            text="总利润"
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    # ========== 7. 支付分析 ==========
    elif page == "💳 支付分析":
        st.header("支付分析")

        payment_stats = analyzer.get_payment_stats()
        payment_amount = analyzer.get_payment_amount()
        platform_payment = analyzer.get_platform_payment_distribution()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("支付渠道分布")
            df_payment = pd.DataFrame(list(payment_stats.items()), columns=['支付渠道', '订单数'])
            fig = px.pie(
                df_payment,
                names='支付渠道',
                values='订单数',
                title="支付渠道占比"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("各渠道支付金额")
            df_amount = pd.DataFrame(payment_amount)
            st.dataframe(df_amount, use_container_width=True)

        st.subheader("各平台支付渠道分布")
        df_platform_pay = pd.DataFrame(platform_payment)
        st.dataframe(df_platform_pay, use_container_width=True)

    # ========== 8. 城市分析 ==========
    elif page == "✈️ 城市分析":
        st.header("出发/到达城市分析")

        dep_city = analyzer.get_departure_city_stats()
        arr_city = analyzer.get_arrival_city_stats()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("热门出发城市 TOP 20")
            df_dep = pd.DataFrame(dep_city)
            st.dataframe(df_dep, use_container_width=True)
            fig = px.bar(
                df_dep.head(15),
                x="城市",
                y="订单数",
                title="TOP 15 出发城市",
                color="订单数",
                color_continuous_scale="Oranges",
                text="订单数"
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("热门到达城市 TOP 20")
            df_arr = pd.DataFrame(arr_city)
            st.dataframe(df_arr, use_container_width=True)
            fig = px.bar(
                df_arr.head(15),
                x="城市",
                y="订单数",
                title="TOP 15 到达城市",
                color="订单数",
                color_continuous_scale="Greens",
                text="订单数"
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

    # ========== 9. 乘客分析 ==========
    elif page == "👥 乘客分析":
        st.header("乘客维度分析")

        passenger_stats = analyzer.get_passenger_stats()
        airline_passengers = analyzer.get_airline_passengers()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("乘客数量分布")
            df_pass = pd.DataFrame(list(passenger_stats.items()), columns=['乘客数', '订单数'])
            fig = px.pie(
                df_pass,
                names='乘客数',
                values='订单数',
                title="乘客数量占比"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("各航司乘客数量")
            df_airline_pass = pd.DataFrame(airline_passengers[:15])
            st.dataframe(df_airline_pass, use_container_width=True)

        st.subheader("航司乘客量对比")
        fig = px.bar(
            df_airline_pass.head(15),
            x="航司",
            y="总乘客数",
            color="平均乘客数",
            title="TOP 15 航司乘客数量",
            text="总乘客数"
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    # ========== 10. 失败分析 ==========
    elif page == "⚠️ 失败分析":
        st.header("失败订单分析")

        failure = analyzer.get_failure_stats()
        df_failure = pd.DataFrame(failure[:50])

        st.dataframe(df_failure, use_container_width=True, height=400)

        if len(df_failure) > 0:
            fig = px.bar(
                df_failure.head(20),
                x="失败原因",
                y="订单数",
                title="TOP 20 失败原因",
                color="订单数",
                color_continuous_scale="Reds",
                text="订单数"
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    # ========== 11. 全自动出票分析 ==========
    elif page == "🤖 全自动出票":
        st.header("全自动出票成功率分析")
        st.caption("最后锁定人为空 = 全自动成功（无人工干预）")

        auto_stats = analyzer.get_auto_ticket_success_stats()
        platform_auto = analyzer.get_auto_ticket_by_platform()
        channel_auto = analyzer.get_auto_ticket_by_purchase_channel()
        type_auto = analyzer.get_auto_ticket_by_purchase_type()
        trend_auto = analyzer.get_auto_ticket_trend()

        col1, col2 = st.columns(2)
        with col1:
            total_orders = sum(s['总订单数'] for s in auto_stats)
            auto_orders = sum(s['全自动订单数'] for s in auto_stats)
            success_rate = auto_orders / total_orders * 100 if total_orders > 0 else 0
            st.metric("总订单数", f"{total_orders:,}")
        with col2:
            st.metric("全自动成功率", f"{success_rate:.1f}%")

        col3, col4 = st.columns(2)
        with col3:
            st.metric("全自动订单数", f"{auto_orders:,}")
        with col4:
            manual_orders = total_orders - auto_orders
            st.metric("人工介入订单数", f"{manual_orders:,}")

        col5, col6 = st.columns(2)
        with col5:
            st.subheader("各航司全自动出票成功率 TOP 20")
            df_auto = pd.DataFrame(auto_stats[:20])
            st.dataframe(df_auto, use_container_width=True)

        with col6:
            st.subheader("各平台全自动出票成功率")
            df_platform = pd.DataFrame(platform_auto)
            st.dataframe(df_platform, use_container_width=True)

        col7, col8 = st.columns(2)
        with col7:
            st.subheader("各采购渠道全自动出票成功率")
            df_channel = pd.DataFrame(channel_auto)
            st.dataframe(df_channel, use_container_width=True)

        with col8:
            st.subheader("各采购类型全自动出票成功率")
            df_type = pd.DataFrame(type_auto)
            st.dataframe(df_type, use_container_width=True)

        st.subheader("全自动成功率趋势（按小时）")
        if trend_auto:
            df_trend = pd.DataFrame(trend_auto)
            fig = px.line(
                df_trend,
                x="小时",
                y="成功率",
                title="24小时全自动出票成功率",
                markers=True
            )
            fig.update_layout(xaxis_tickmode='linear', xaxis_dtick=1)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_trend, use_container_width=True)
        else:
            st.info("暂无趋势数据")

        st.subheader("TOP 10 航司全自动率对比")
        fig = px.bar(
            df_auto.head(10),
            x="航司",
            y="全自动成功率",
            color="全自动成功率",
            title="TOP 10 航司全自动出票成功率",
            color_continuous_scale="Greens",
            text="全自动成功率"
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("各航司最后锁定人订单分布")
        lock_person = analyzer.get_lock_person_by_airline()
        if lock_person:
            df_lock = pd.DataFrame(lock_person)
            st.dataframe(df_lock, use_container_width=True)

            # 按锁定人统计汇总
            lock_summary = df_lock.groupby('最后锁定人')['订单数'].sum().reset_index()
            lock_summary.columns = ['最后锁定人', '总订单数']
            lock_summary = lock_summary.sort_values('总订单数', ascending=False)
            st.subheader("锁定人订单量汇总")
            fig_lock = px.bar(
                lock_summary.head(15),
                x="最后锁定人",
                y="总订单数",
                color="总订单数",
                title="TOP 15 锁定人订单量",
                text="总订单数"
            )
            fig_lock.update_traces(textposition='outside')
            st.plotly_chart(fig_lock, use_container_width=True)
        else:
            st.info("暂无锁定人数据")

    # ========== 12. 数据明细 ==========
    elif page == "📋 数据明细":
        st.header("数据明细")

        page_num = st.number_input("页码", min_value=1, value=1, step=1)
        data, total = analyzer.get_order_details(int(page_num), 100)
        df_detail = pd.DataFrame(data)

        st.info(f"共 {total:,} 条记录，显示第 {int(page_num)} 页（每页100条）")
        st.dataframe(df_detail, use_container_width=True, height=600)

else:
    st.info("👈 请上传Excel文件开始分析")

    st.subheader("功能说明")
    st.markdown("""
    - **📊 数据概览**: 总订单数、总金额、利润统计、平台分布饼图
    - **📈 航司分析**: 航司订单排名、航司×平台交叉分析
    - **🛫 航线分析**: 航线订单量排名
    - **🔄 航程类型**: 单程/往返/多程分布
    - **📅 时间分析**: 24小时订单分布
    - **💰 利润分析**: 盈利/亏损、各航司平台利润
    - **💳 支付分析**: 支付渠道分布、支付金额
    - **✈️ 城市分析**: 热门出发/到达城市
    - **👥 乘客分析**: 乘客数量分布、各航司乘客量
    - **⚠️ 失败分析**: 失败原因统计
    - **📋 数据明细**: 分页查看原始数据
    """)