# 出票订单数据分析工具

基于 Streamlit 的数据统计分析工具，支持 Excel 文件上传和可视化分析。

## 功能模块

- 📊 数据概览 - 统计卡片、平台分布饼图
- 📈 航司分析 - 航司排名、航司×平台交叉分析
- 🛫 航线分析 - 航线订单量排名
- 🔄 航程类型 - 单程/往返/多程分布
- 💰 财务统计 - 利润分析
- ⚠️ 失败分析 - 失败原因统计
- 📋 数据明细 - 分页查看原始数据

## 部署到 Streamlit Cloud

1. 将此项目上传到 GitHub
2. 访问 https://streamlit.io/cloud
3. 连接 GitHub 仓库
4. 部署即可获得分享链接

## 本地运行

```bash
pip install -r requirements.txt
streamlit run main.py
```

## requirements.txt

```
pandas>=2.0.0
openpyxl>=3.1.0
streamlit==1.35.0
plotly==5.18.0
```

## 数据文件格式

支持 Excel 文件 (.xlsx)，需包含以下字段：
- 订单ID
- 平台
- 航空公司列表
- 出发机场列表
- 到达机场列表
- 利润
- 支付金额
- 失败原因
- 等63个字段