import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class TicketOrderAnalyzer:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.df = None
        self.total = 0

    def load_data(self, file_path):
        self.file_path = file_path
        self.df = pd.read_excel(file_path)
        self.total = len(self.df)
        return self.df

    def get_overview(self):
        if self.df is None:
            return {}
        total = len(self.df)
        profit = pd.to_numeric(self.df['利润'], errors='coerce')
        pay = pd.to_numeric(self.df['支付金额'], errors='coerce')
        return {
            '总订单数': total,
            '总支付金额': pay.sum(),
            '总利润': profit.sum(),
            '平均利润': profit.mean(),
            '最大利润': profit.max(),
            '最小利润': profit.min(),
        }

    def get_platform_stats(self):
        if self.df is None:
            return []
        return self.df['平台'].value_counts().to_dict()

    def get_airline_stats(self):
        if self.df is None:
            return []
        stats = self.df['航空公司列表'].value_counts()
        result = []
        total = len(self.df)
        for airline, count in stats.items():
            result.append({
                '航司': airline,
                '订单数': count,
                '占比': f"{count/total*100:.1f}%"
            })
        return result

    def get_airline_platform_cross(self):
        if self.df is None:
            return []
        cross = self.df.groupby(['航空公司列表', '平台']).size().reset_index(name='订单数')
        return cross.sort_values('订单数', ascending=False).to_dict('records')

    def get_route_stats(self):
        if self.df is None:
            return []
        self.df['航线'] = self.df['出发机场列表'] + ' → ' + self.df['到达机场列表']
        stats = self.df['航线'].value_counts()
        total = len(self.df)
        result = []
        for route, count in stats.items():
            result.append({
                '航线': route,
                '订单数': count,
                '占比': f"{count/total*100:.2f}%"
            })
        return result

    def get_trip_type_stats(self):
        if self.df is None:
            return {}
        self.df['航班数'] = self.df['航班号列表'].apply(
            lambda x: len(str(x).split(',')) if pd.notna(x) else 0
        )
        def classify_trip(seg_count):
            if seg_count == 1:
                return '单程'
            elif seg_count == 2:
                return '往返'
            else:
                return '多程'
        self.df['航程类型'] = self.df['航班数'].apply(classify_trip)
        return self.df['航程类型'].value_counts().to_dict()

    def get_airline_trip_type(self):
        if self.df is None:
            return []
        return self.df.groupby(['航空公司列表', '航程类型']).size().reset_index(name='订单数').to_dict('records')

    def get_platform_trip_type(self):
        if self.df is None:
            return []
        return self.df.groupby(['平台', '航程类型']).size().reset_index(name='订单数').to_dict('records')

    def get_finance_stats(self):
        if self.df is None:
            return {}
        profit = pd.to_numeric(self.df['利润'], errors='coerce')
        pay = pd.to_numeric(self.df['支付金额'], errors='coerce')
        return {
            '总支付金额': pay.sum(),
            '平均支付金额': pay.mean(),
            '总利润': profit.sum(),
            '平均利润': profit.mean(),
            '盈利订单数': len(profit[profit > 0]),
            '亏损订单数': len(profit[profit < 0]),
            '持平订单数': len(profit[profit == 0]),
        }

    def get_airline_profit(self):
        if self.df is None:
            return []
        profit = pd.to_numeric(self.df['利润'], errors='coerce')
        self.df['利润数值'] = profit
        stats = self.df.groupby('航空公司列表')['利润数值'].agg(['sum', 'mean', 'count'])
        stats = stats.reset_index()
        stats.columns = ['航司', '总利润', '平均利润', '订单数']
        stats = stats.sort_values('总利润', ascending=False)
        return stats.to_dict('records')

    def get_platform_profit(self):
        if self.df is None:
            return []
        profit = pd.to_numeric(self.df['利润'], errors='coerce')
        self.df['利润数值'] = profit
        stats = self.df.groupby('平台')['利润数值'].agg(['sum', 'mean', 'count'])
        stats = stats.reset_index()
        stats.columns = ['平台', '总利润', '平均利润', '订单数']
        stats = stats.sort_values('总利润', ascending=False)
        return stats.to_dict('records')

    def get_payment_stats(self):
        if self.df is None:
            return []
        return self.df['支付渠道'].value_counts().to_dict()

    def get_payment_amount(self):
        if self.df is None:
            return []
        pay = pd.to_numeric(self.df['支付金额'], errors='coerce')
        self.df['支付金额_数值'] = pay
        stats = self.df.groupby('支付渠道')['支付金额_数值'].sum().reset_index()
        stats.columns = ['支付渠道', '总金额']
        stats = stats.sort_values('总金额', ascending=False)
        return stats.to_dict('records')

    def get_failure_stats(self):
        if self.df is None:
            return []
        fail_counts = self.df['失败原因'].value_counts()
        result = []
        for reason, count in fail_counts.items():
            if pd.notna(reason) and str(reason).strip():
                result.append({
                    '失败原因': reason[:100],
                    '订单数': count
                })
        return result

    def get_hourly_stats(self):
        if self.df is None:
            return []
        self.df['创建时间_小时'] = pd.to_datetime(self.df['创建时间'], errors='coerce').dt.hour
        hour_counts = self.df['创建时间_小时'].value_counts().sort_index()
        result = []
        total = len(self.df)
        for hour, count in hour_counts.items():
            if pd.notna(hour):
                result.append({
                    '小时': int(hour),
                    '订单数': count,
                    '占比': f"{count/total*100:.1f}%"
                })
        return result

    def get_passenger_stats(self):
        if self.df is None:
            return []
        return self.df['乘客数量'].value_counts().sort_index().to_dict()

    def get_airline_passengers(self):
        if self.df is None:
            return []
        stats = self.df.groupby('航空公司列表')['乘客数量'].agg(['sum', 'mean', 'count'])
        stats = stats.reset_index()
        stats.columns = ['航司', '总乘客数', '平均乘客数', '订单数']
        stats = stats.sort_values('总乘客数', ascending=False)
        return stats.to_dict('records')

    def get_departure_city_stats(self):
        if self.df is None:
            return []
        dep_counts = self.df['出发机场列表'].value_counts().head(20)
        total = len(self.df)
        result = []
        for city, count in dep_counts.items():
            result.append({
                '城市': city,
                '订单数': count,
                '占比': f"{count/total*100:.1f}%"
            })
        return result

    def get_arrival_city_stats(self):
        if self.df is None:
            return []
        arr_counts = self.df['到达机场列表'].value_counts().head(20)
        total = len(self.df)
        result = []
        for city, count in arr_counts.items():
            result.append({
                '城市': city,
                '订单数': count,
                '占比': f"{count/total*100:.1f}%"
            })
        return result

    def get_platform_payment_distribution(self):
        if self.df is None:
            return []
        stats = self.df.groupby(['平台', '支付渠道']).size().reset_index(name='订单数')
        stats = stats.sort_values(['平台', '订单数'], ascending=[True, False])
        return stats.to_dict('records')

    def get_order_details(self, page=1, page_size=100):
        if self.df is None:
            return [], 0
        total = len(self.df)
        start = (page - 1) * page_size
        end = start + page_size
        data = self.df.iloc[start:end]
        return data.to_dict('records'), total