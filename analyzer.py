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

    def get_payment_stats(self):
        if self.df is None:
            return []
        return self.df['支付渠道'].value_counts().to_dict()

    def get_failure_stats(self):
        if self.df is None:
            return []
        fail_counts = self.df['失败原因'].value_counts()
        result = []
        for reason, count in fail_counts.items():
            if pd.notna(reason) and str(reason).strip():
                result.append({
                    '失败原因': reason,
                    '订单数': count
                })
        return result

    def get_order_details(self, page=1, page_size=100):
        if self.df is None:
            return [], 0
        total = len(self.df)
        start = (page - 1) * page_size
        end = start + page_size
        data = self.df.iloc[start:end]
        return data.to_dict('records'), total