import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import numpy as np
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fund_data import get_fund_data, get_fund_info
from src.fund_analysis import (
    calculate_max_drawdown,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_annual_return
)

# 设置页面配置
st.set_page_config(
    page_title="基金分析工具",
    page_icon="📊",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        background-color: white;
        padding: 1rem 0;
    }
    .fixed-top {
        position: sticky;
        top: 0;
        background-color: white;
        z-index: 999;
        padding: 1rem 0;
        border-bottom: 1px solid #eee;
        margin-bottom: 2rem;
    }
    .input-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 1.5rem 0;
    }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        height: 42px;  /* 与输入框高度保持一致 */
    }
    .reportview-container {
        background: #f0f2f6;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
        margin-top: 0.5rem;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    /* 确保输入框和按钮在同一水平线上 */
    div.row-widget.stTextInput {
        margin-bottom: 0;
    }
    /* 自选基金卡片样式 */
    .fund-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        background-color: white;
        height: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .fund-card h4 {
        margin: 0 0 1rem 0;
        font-size: 1.1rem;
        color: #333;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .fund-card p {
        margin: 0.5rem 0;
        color: #666;
        font-size: 0.9rem;
    }
    .fund-card .info-row {
        display: flex;
        justify-content: space-between;
        margin: 0.5rem 0;
    }
    .fund-card .update-time {
        color: #999;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    .fund-card .button-group {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 初始化session state
if 'fund_code' not in st.session_state:
    st.session_state.fund_code = ''
if 'fund_data' not in st.session_state:
    st.session_state.fund_data = None
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None
if 'favorite_funds' not in st.session_state:
    st.session_state.favorite_funds = {}
if 'current_view' not in st.session_state:
    st.session_state.current_view = None
if 'previous_fund_code' not in st.session_state:
    st.session_state.previous_fund_code = None
if 'show_toast' not in st.session_state:
    st.session_state.show_toast = None
if 'show_detail_popup' not in st.session_state:
    st.session_state.show_detail_popup = False
if 'detail_fund_code' not in st.session_state:
    st.session_state.detail_fund_code = None

def show_fund_detail_popup(fund_code):
    """显示基金详情弹窗"""
    st.session_state.show_detail_popup = True
    st.session_state.detail_fund_code = fund_code
    st.session_state.fund_data = None
    st.rerun()

def display_fund_analysis(df, fund_info, show_header=True):
    """显示基金分析内容"""
    if show_header:
        st.markdown('<h2 class="section-header">基金基本信息</h2>', unsafe_allow_html=True)
    
    # 显示基金基本信息
    col1, col2 = st.columns(2)
    with col1:
        # 处理基金名称，移除代码部分
        fund_name = fund_info.get('fund_name', '未获取到')
        if '(' in fund_name:
            fund_name = fund_name.split('(')[0]
        elif '（' in fund_name:
            fund_name = fund_name.split('（')[0]
        st.markdown(f"**基金名称：** {fund_name}")
        st.markdown(f"**基金公司：** {fund_info.get('fund_company', '未获取到')}")
    with col2:
        st.markdown(f"**基金代码：** {fund_info.get('fund_code', '未获取到')}")
        st.markdown(f"**基金类型：** {fund_info.get('fund_type', '未获取到')}")
    
    # 显示基金数据分析结果
    st.markdown('<h2 class="section-header">净值走势</h2>', unsafe_allow_html=True)
    
    # 创建净值走势图
    fig = go.Figure()
    
    # 根据基金类型显示不同的数据
    is_money_fund = fund_info.get('is_money_fund', False)
    if is_money_fund:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['nav'],
            mode='lines',
            name='每万份收益',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.update_layout(
            title='每万份收益走势图',
            xaxis_title='日期',
            yaxis_title='每万份收益（元）',
            hovermode='x unified',
            showlegend=True,
            height=500
        )
    else:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['nav'],
            mode='lines',
            name='单位净值',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.update_layout(
            title='基金净值走势图',
            xaxis_title='日期',
            yaxis_title='单位净值',
            hovermode='x unified',
            showlegend=True,
            height=500
        )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)
    
    # 基本统计信息
    st.markdown('<h2 class="section-header">基金统计信息</h2>', unsafe_allow_html=True)
    
    # 计算统计指标
    latest_date = df['date'].max()
    latest_nav = df['nav'].iloc[-1]
    establishment_date = df['date'].min()
    
    if is_money_fund:
        # 计算七日年化收益率
        last_7_days = df[df['date'] > latest_date - pd.Timedelta(days=7)]['nav']
        seven_day_sum = last_7_days.sum()
        seven_day_return = (seven_day_sum / 10000) * 100  # 七日累计收益率
        seven_day_annual = (pow(1 + seven_day_return/100, 365/7) - 1) * 100  # 七日年化收益率
        
        # 计算历史七日年化收益率序列
        df['rolling_7day_sum'] = df['nav'].rolling(window=7).sum()
        df['rolling_7day_return'] = (df['rolling_7day_sum'] / 10000) * 100
        df['rolling_7day_annual'] = (pow(1 + df['rolling_7day_return']/100, 365/7) - 1) * 100
        
        max_7day_annual = df['rolling_7day_annual'].max()
        min_7day_annual = df['rolling_7day_annual'].min()
        
        # 显示统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(f"最新每万份收益（{latest_date.strftime('%Y-%m-%d')}）", f"{latest_nav:.4f}元")
        with col2:
            st.metric("七日年化收益率", f"{seven_day_annual:.2f}%")
        with col3:
            st.metric(f"历史最高七日年化（{df.loc[df['rolling_7day_annual'].idxmax(), 'date'].strftime('%Y-%m-%d')}）", f"{max_7day_annual:.2f}%")
        with col4:
            st.metric(f"历史最低七日年化（{df.loc[df['rolling_7day_annual'].idxmin(), 'date'].strftime('%Y-%m-%d')}）", f"{min_7day_annual:.2f}%")
        
        # 显示额外的统计信息
        st.markdown("---")
        st.markdown(f"**基金成立日期：** {establishment_date.strftime('%Y-%m-%d')}")
        st.markdown(f"**最新数据日期：** {latest_date.strftime('%Y-%m-%d')}")
    else:
        # 非货币基金的原有统计逻辑
        nav_change = (df['nav'].iloc[-1] / df['nav'].iloc[0] - 1) * 100
        max_nav = df['nav'].max()
        max_nav_date = df[df['nav'] == max_nav]['date'].iloc[0]
        min_nav = df['nav'].min()
        min_nav_date = df[df['nav'] == min_nav]['date'].iloc[0]
        total_return = ((df['nav'].iloc[-1] / df['nav'].iloc[0]) - 1) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(f"最新净值（{latest_date.strftime('%Y-%m-%d')}）", f"{latest_nav:.4f}")
        with col2:
            st.metric("累计收益（最新净值/首日净值-1）", f"{nav_change:.2f}%")
        with col3:
            st.metric(f"历史最高（{max_nav_date.strftime('%Y-%m-%d')}）", f"{max_nav:.4f}")
        with col4:
            st.metric(f"历史最低（{min_nav_date.strftime('%Y-%m-%d')}）", f"{min_nav:.4f}")
        
        st.markdown("---")
        st.markdown(f"**基金成立日期：** {establishment_date.strftime('%Y-%m-%d')}")
        st.markdown(f"**最新数据日期：** {latest_date.strftime('%Y-%m-%d')}")
        st.markdown(f"**成立至今累计收益：** {total_return:.2f}%")
    
    # 添加基金投资天数指标分析
    st.markdown('<h2 class="section-header">基金投资天数指标分析</h2>', unsafe_allow_html=True)
    
    # 日期选择
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown("#### 选择投资区间")
    with col2:
        # 快速选择按钮
        period_cols = st.columns(7)
        periods = {
            "近一周": 7,
            "近一月": 30,
            "近三月": 90,
            "近半年": 180,
            "近一年": 365,
            "近两年": 730,
            "近三年": 1095
        }
        
        def update_date_range(days):
            # 使用当前选择的结束日期，而不是数据集的最大日期
            current_end_date = st.session_state.get('end_date_input', df['date'].max().date())
            # 转换为datetime以便进行日期计算
            current_end_date = pd.to_datetime(current_end_date)
            start_date = current_end_date - pd.Timedelta(days=days)
            # 确保开始日期不早于基金成立日期
            if start_date < df['date'].min():
                start_date = df['date'].min()
            st.session_state.start_date = start_date.date()
            st.session_state.end_date = current_end_date.date()
        
        for i, (period_name, days) in enumerate(periods.items()):
            with period_cols[i]:
                if st.button(period_name, key=f"period_{days}"):
                    update_date_range(days)
    
    # 日期选择器
    date_cols = st.columns(2)
    with date_cols[0]:
        start_date = st.date_input(
            "开始日期",
            min_value=establishment_date.date(),
            max_value=latest_date.date(),
            value=st.session_state.start_date or establishment_date.date(),
            key="start_date_input"
        )
    with date_cols[1]:
        end_date = st.date_input(
            "结束日期",
            min_value=establishment_date.date(),
            max_value=latest_date.date(),
            value=st.session_state.end_date or latest_date.date(),
            key="end_date_input"
        )
    
    # 转换日期为datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # 获取选定期间的数据
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    period_df = df.loc[mask].copy()
    
    if not period_df.empty and start_date <= end_date:
        # 计算投资天数
        trading_days = len(period_df)
        calendar_days = (end_date - start_date).days + 1
        
        if is_money_fund:
            # 计算货币基金的收益指标
            total_income = period_df['nav'].sum()  # 区间内每日万份收益之和
            cumulative_return = (total_income / 10000) * 100  # 累计收益率
            annual_return = (pow(1 + cumulative_return/100, 365/calendar_days) - 1) * 100  # 年化收益率
            
            # 显示指标分析结果
            st.markdown("### 投资区间基本信息")
            st.markdown(f"- **投资天数：** {calendar_days}天（其中交易日{trading_days}天）")
            
            st.markdown("### 收益类指标")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("年化收益率", f"{annual_return:.2f}%",
                        help="年化收益率 = (1 + 累计收益率)^(365/投资天数) - 1")
            with col2:
                st.metric("区间累计收益率", f"{cumulative_return:.2f}%",
                        help="累计收益率 = (区间内每日万份收益之和/10000) × 100%")
        else:
            # 非货币基金的原有计算逻辑
            period_return = (period_df['nav'].iloc[-1] / period_df['nav'].iloc[0] - 1) * 100
            annual_return = (pow(1 + period_return/100, 252/trading_days) - 1) * 100
            
            # 计算风险类指标
            period_df['daily_return'] = period_df['nav'].pct_change()
            # 计算区间波动率
            mean_return = period_df['daily_return'].mean()
            volatility = np.sqrt(((period_df['daily_return'] - mean_return) ** 2).sum() / (trading_days - 1)) * 100
            
            period_df['rolling_max'] = period_df['nav'].expanding().max()
            period_df['drawdown'] = (period_df['nav'] - period_df['rolling_max']) / period_df['rolling_max'] * 100
            max_drawdown = abs(period_df['drawdown'].min())
            
            # 显示指标分析结果
            st.markdown("### 投资区间基本信息")
            st.markdown(f"- **投资天数：** {calendar_days}天（其中交易日{trading_days}天）")
            st.markdown(f"- **区间起始净值：** {period_df['nav'].iloc[0]:.4f}")
            st.markdown(f"- **区间结束净值：** {period_df['nav'].iloc[-1]:.4f}")
            
            st.markdown("### 收益类指标")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("年化收益率", f"{annual_return:.2f}%",
                        help="年化收益率 = (1 + 期间总收益率)^(252/投资天数) - 1")
            with col2:
                st.metric("区间累计收益率", f"{period_return:.2f}%",
                        help="累计收益率 = (期末净值 - 期初净值) / 期初净值")
            
            st.markdown("### 风险类指标")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("区间波动率", f"{volatility:.2f}%",
                        help="波动率 = √(Σ(日收益率 - 平均收益率)²/(交易天数-1))")
            with col2:
                st.metric("最大回撤", f"{max_drawdown:.2f}%",
                        help="最大回撤 = (期间最高点净值 - 期间最低点净值) / 期间最高点净值")
    else:
        st.error("请选择有效的投资区间")

# 从本地文件加载自选基金数据
# 使用绝对路径确保文件保存在根目录下
FAVORITE_FUNDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "favorite_funds.json")

def load_favorite_funds():
    if os.path.exists(FAVORITE_FUNDS_FILE):
        try:
            with open(FAVORITE_FUNDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_favorite_funds():
    with open(FAVORITE_FUNDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.favorite_funds, f, ensure_ascii=False)

# 加载自选基金数据
if len(st.session_state.favorite_funds) == 0:
    st.session_state.favorite_funds = load_favorite_funds()

# 侧边栏导航
st.sidebar.markdown("# 📊 基金分析工具")
st.sidebar.markdown("---")

# 导航选项
selected_nav = st.sidebar.radio(
    "功能导航",
    ["基金查询", "自选基金", "基金比较", "基金投资计划", "待开发"]
)

# 处理导航逻辑
if selected_nav != "基金查询" and st.session_state.current_view == "fund_query_from_favorite":
    # 如果从自选基金跳转来的，且用户点击了其他导航，恢复之前的基金代码
    if st.session_state.previous_fund_code:
        st.session_state.fund_code = st.session_state.previous_fund_code
        st.session_state.previous_fund_code = None
    st.session_state.current_view = None

# 如果切换到基金查询功能，自动关闭自选基金卡片
if selected_nav == "基金查询":
    st.session_state.show_detail_popup = False
    st.session_state.detail_fund_code = None

nav_option = selected_nav

# 显示提示信息
if st.session_state.show_toast:
    st.toast(st.session_state.show_toast["message"], icon=st.session_state.show_toast["icon"])
    st.session_state.show_toast = None

# 检查是否需要显示基金详情弹窗
if st.session_state.show_detail_popup and st.session_state.detail_fund_code:
    # 创建详情容器
    detail_container = st.container()
    with detail_container:
        st.subheader("基金详情")
        # 获取基金数据
        try:
            with st.spinner("正在获取基金数据..."):
                df = get_fund_data(st.session_state.detail_fund_code)
                fund_info = get_fund_info(st.session_state.detail_fund_code)
                
            if not df.empty:
                # 显示基金分析内容
                display_fund_analysis(df, fund_info)
            else:
                st.error("未能获取到基金数据，请检查基金代码是否正确。")
                
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
            
        # 添加关闭按钮
        if st.button("关闭", key="close_detail_popup"):
            st.session_state.show_detail_popup = False
            st.session_state.detail_fund_code = None
            st.rerun()

# 主界面内容
if nav_option == "基金查询":
    st.session_state.current_view = "fund_query"
    st.markdown('<h1 class="main-header">基金分析报告</h1>', unsafe_allow_html=True)
    
    # 创建固定在顶部的容器
    with st.container():
        st.markdown('<div class="fixed-top">', unsafe_allow_html=True)
        
        # 如果是从自选基金跳转来的，添加返回按钮
        if st.session_state.current_view == "fund_query_from_favorite":
            if st.button("← 返回自选基金", use_container_width=True):
                st.session_state.fund_code = st.session_state.previous_fund_code
                st.session_state.previous_fund_code = None
                st.session_state.current_view = None
                st.session_state.nav_option = "自选基金"
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
        
        # 输入基金代码
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            fund_code = st.text_input("👉 请输入基金代码", 
                                    value=st.session_state.fund_code,
                                    placeholder="例如: 017811",
                                    label_visibility="collapsed")
        with col2:
            analyze_button = st.button("开始分析", use_container_width=True)
        with col3:
            # 检查基金是否已在自选中
            is_favorite = fund_code in st.session_state.favorite_funds
            if is_favorite:
                if st.button("移出自选", use_container_width=True):
                    del st.session_state.favorite_funds[fund_code]
                    save_favorite_funds()
                    st.session_state.show_toast = {"message": "已从自选中移除！", "icon": "✅"}
                    st.rerun()
            else:
                if st.button("加入自选", use_container_width=True):
                    if fund_code and st.session_state.fund_data is not None:
                        st.session_state.favorite_funds[fund_code] = {
                            'fund_info': st.session_state.fund_data['fund_info'],
                            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        save_favorite_funds()
                        st.session_state.show_toast = {"message": f"基金 {fund_code} 已添加到自选！", "icon": "✅"}
                        st.rerun()
                    elif fund_code:
                        st.warning('请先点击"开始分析"按钮获取基金数据')
                    else:
                        st.warning("请先输入基金代码")
        st.markdown('</div>', unsafe_allow_html=True)

    if analyze_button and fund_code:
        st.session_state.fund_code = fund_code
        st.session_state.fund_data = None
        st.session_state.start_date = None
        st.session_state.end_date = None
        st.rerun()
    
    if st.session_state.fund_code:
        try:
            # 获取基金数据（如果还没有获取）
            if st.session_state.fund_data is None:
                with st.spinner("正在获取基金数据..."):
                    df = get_fund_data(st.session_state.fund_code)
                    fund_info = get_fund_info(st.session_state.fund_code)
                    st.session_state.fund_data = {
                        'df': df,
                        'fund_info': fund_info
                    }
            else:
                df = st.session_state.fund_data['df']
                fund_info = st.session_state.fund_data['fund_info']
            
            if not df.empty:
                # 显示基金基本信息
                st.markdown('<h2 class="section-header">基金基本信息</h2>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    # 处理基金名称，移除代码部分
                    fund_name = fund_info.get('fund_name', '未获取到')
                    if '(' in fund_name:
                        fund_name = fund_name.split('(')[0]
                    elif '（' in fund_name:
                        fund_name = fund_name.split('（')[0]
                    st.markdown(f"**基金名称：** {fund_name}")
                    st.markdown(f"**基金公司：** {fund_info.get('fund_company', '未获取到')}")
                with col2:
                    st.markdown(f"**基金代码：** {st.session_state.fund_code}")
                    st.markdown(f"**基金类型：** {fund_info.get('fund_type', '未获取到')}")
                
                # 显示基金数据分析结果
                st.markdown('<h2 class="section-header">净值走势</h2>', unsafe_allow_html=True)
                
                # 创建净值走势图
                fig = go.Figure()
                
                # 根据基金类型显示不同的数据
                is_money_fund = fund_info.get('is_money_fund', False)
                if is_money_fund:
                    fig.add_trace(go.Scatter(
                        x=df['date'],
                        y=df['nav'],
                        mode='lines',
                        name='每万份收益',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    fig.update_layout(
                        title='每万份收益走势图',
                        xaxis_title='日期',
                        yaxis_title='每万份收益（元）',
                        hovermode='x unified',
                        showlegend=True,
                        height=500
                    )
                else:
                    fig.add_trace(go.Scatter(
                        x=df['date'],
                        y=df['nav'],
                        mode='lines',
                        name='单位净值',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    fig.update_layout(
                        title='基金净值走势图',
                        xaxis_title='日期',
                        yaxis_title='单位净值',
                        hovermode='x unified',
                        showlegend=True,
                        height=500
                    )
                
                # 显示图表
                st.plotly_chart(fig, use_container_width=True)
                
                # 基本统计信息
                st.markdown('<h2 class="section-header">基金统计信息</h2>', unsafe_allow_html=True)
                
                # 计算统计指标
                latest_date = df['date'].max()
                latest_nav = df['nav'].iloc[-1]
                establishment_date = df['date'].min()
                
                if is_money_fund:
                    # 计算七日年化收益率
                    last_7_days = df[df['date'] > latest_date - pd.Timedelta(days=7)]['nav']
                    seven_day_sum = last_7_days.sum()
                    seven_day_return = (seven_day_sum / 10000) * 100  # 七日累计收益率
                    seven_day_annual = (pow(1 + seven_day_return/100, 365/7) - 1) * 100  # 七日年化收益率
                    
                    # 计算历史七日年化收益率序列
                    df['rolling_7day_sum'] = df['nav'].rolling(window=7).sum()
                    df['rolling_7day_return'] = (df['rolling_7day_sum'] / 10000) * 100
                    df['rolling_7day_annual'] = (pow(1 + df['rolling_7day_return']/100, 365/7) - 1) * 100
                    
                    max_7day_annual = df['rolling_7day_annual'].max()
                    min_7day_annual = df['rolling_7day_annual'].min()
                    
                    # 显示统计信息
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(f"最新每万份收益（{latest_date.strftime('%Y-%m-%d')}）", f"{latest_nav:.4f}元")
                    with col2:
                        st.metric("七日年化收益率", f"{seven_day_annual:.2f}%")
                    with col3:
                        st.metric(f"历史最高七日年化（{df.loc[df['rolling_7day_annual'].idxmax(), 'date'].strftime('%Y-%m-%d')}）", f"{max_7day_annual:.2f}%")
                    with col4:
                        st.metric(f"历史最低七日年化（{df.loc[df['rolling_7day_annual'].idxmin(), 'date'].strftime('%Y-%m-%d')}）", f"{min_7day_annual:.2f}%")
                    
                    # 显示额外的统计信息
                    st.markdown("---")
                    st.markdown(f"**基金成立日期：** {establishment_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"**最新数据日期：** {latest_date.strftime('%Y-%m-%d')}")
                else:
                    # 非货币基金的原有统计逻辑
                    nav_change = (df['nav'].iloc[-1] / df['nav'].iloc[0] - 1) * 100
                    max_nav = df['nav'].max()
                    max_nav_date = df[df['nav'] == max_nav]['date'].iloc[0]
                    min_nav = df['nav'].min()
                    min_nav_date = df[df['nav'] == min_nav]['date'].iloc[0]
                    total_return = ((df['nav'].iloc[-1] / df['nav'].iloc[0]) - 1) * 100
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(f"最新净值（{latest_date.strftime('%Y-%m-%d')}）", f"{latest_nav:.4f}")
                    with col2:
                        st.metric("累计收益（最新净值/首日净值-1）", f"{nav_change:.2f}%")
                    with col3:
                        st.metric(f"历史最高（{max_nav_date.strftime('%Y-%m-%d')}）", f"{max_nav:.4f}")
                    with col4:
                        st.metric(f"历史最低（{min_nav_date.strftime('%Y-%m-%d')}）", f"{min_nav:.4f}")
                    
                    st.markdown("---")
                    st.markdown(f"**基金成立日期：** {establishment_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"**最新数据日期：** {latest_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"**成立至今累计收益：** {total_return:.2f}%")
                
                # 添加基金投资天数指标分析
                st.markdown('<h2 class="section-header">基金投资天数指标分析</h2>', unsafe_allow_html=True)
                
                # 日期选择
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.markdown("#### 选择投资区间")
                with col2:
                    # 快速选择按钮
                    period_cols = st.columns(7)
                    periods = {
                        "近一周": 7,
                        "近一月": 30,
                        "近三月": 90,
                        "近半年": 180,
                        "近一年": 365,
                        "近两年": 730,
                        "近三年": 1095
                    }
                    
                    def update_date_range(days):
                        # 使用当前选择的结束日期，而不是数据集的最大日期
                        current_end_date = st.session_state.get('end_date_input', df['date'].max().date())
                        # 转换为datetime以便进行日期计算
                        current_end_date = pd.to_datetime(current_end_date)
                        start_date = current_end_date - pd.Timedelta(days=days)
                        # 确保开始日期不早于基金成立日期
                        if start_date < df['date'].min():
                            start_date = df['date'].min()
                        st.session_state.start_date = start_date.date()
                        st.session_state.end_date = current_end_date.date()
                    
                    for i, (period_name, days) in enumerate(periods.items()):
                        with period_cols[i]:
                            if st.button(period_name, key=f"period_{days}"):
                                update_date_range(days)
                
                # 日期选择器
                date_cols = st.columns(2)
                with date_cols[0]:
                    start_date = st.date_input(
                        "开始日期",
                        min_value=establishment_date.date(),
                        max_value=latest_date.date(),
                        value=st.session_state.start_date or establishment_date.date(),
                        key="start_date_input"
                    )
                with date_cols[1]:
                    end_date = st.date_input(
                        "结束日期",
                        min_value=establishment_date.date(),
                        max_value=latest_date.date(),
                        value=st.session_state.end_date or latest_date.date(),
                        key="end_date_input"
                    )
                
                # 转换日期为datetime
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                
                # 获取选定期间的数据
                mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                period_df = df.loc[mask].copy()
                
                if not period_df.empty and start_date <= end_date:
                    # 计算投资天数
                    trading_days = len(period_df)
                    calendar_days = (end_date - start_date).days + 1
                    
                    if is_money_fund:
                        # 计算货币基金的收益指标
                        total_income = period_df['nav'].sum()  # 区间内每日万份收益之和
                        cumulative_return = (total_income / 10000) * 100  # 累计收益率
                        annual_return = (pow(1 + cumulative_return/100, 365/calendar_days) - 1) * 100  # 年化收益率
                        
                        # 显示指标分析结果
                        st.markdown("### 投资区间基本信息")
                        st.markdown(f"- **投资天数：** {calendar_days}天（其中交易日{trading_days}天）")
                        
                        st.markdown("### 收益类指标")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("年化收益率", f"{annual_return:.2f}%",
                                    help="年化收益率 = (1 + 累计收益率)^(365/投资天数) - 1")
                        with col2:
                            st.metric("区间累计收益率", f"{cumulative_return:.2f}%",
                                    help="累计收益率 = (区间内每日万份收益之和/10000) × 100%")
                    else:
                        # 非货币基金的原有计算逻辑
                        period_return = (period_df['nav'].iloc[-1] / period_df['nav'].iloc[0] - 1) * 100
                        annual_return = (pow(1 + period_return/100, 252/trading_days) - 1) * 100
                        
                        # 计算风险类指标
                        period_df['daily_return'] = period_df['nav'].pct_change()
                        # 计算区间波动率
                        mean_return = period_df['daily_return'].mean()
                        volatility = np.sqrt(((period_df['daily_return'] - mean_return) ** 2).sum() / (trading_days - 1)) * 100
                        
                        period_df['rolling_max'] = period_df['nav'].expanding().max()
                        period_df['drawdown'] = (period_df['nav'] - period_df['rolling_max']) / period_df['rolling_max'] * 100
                        max_drawdown = abs(period_df['drawdown'].min())
                        
                        # 显示指标分析结果
                        st.markdown("### 投资区间基本信息")
                        st.markdown(f"- **投资天数：** {calendar_days}天（其中交易日{trading_days}天）")
                        st.markdown(f"- **区间起始净值：** {period_df['nav'].iloc[0]:.4f}")
                        st.markdown(f"- **区间结束净值：** {period_df['nav'].iloc[-1]:.4f}")
                        
                        st.markdown("### 收益类指标")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("年化收益率", f"{annual_return:.2f}%",
                                    help="年化收益率 = (1 + 期间总收益率)^(252/投资天数) - 1")
                        with col2:
                            st.metric("区间累计收益率", f"{period_return:.2f}%",
                                    help="累计收益率 = (期末净值 - 期初净值) / 期初净值")
                        
                        st.markdown("### 风险类指标")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("区间波动率", f"{volatility:.2f}%",
                                    help="波动率 = √(Σ(日收益率 - 平均收益率)²/(交易天数-1))")
                        with col2:
                            st.metric("最大回撤", f"{max_drawdown:.2f}%",
                                    help="最大回撤 = (期间最高点净值 - 期间最低点净值) / 期间最高点净值")
                else:
                    st.error("请选择有效的投资区间")
                
            else:
                st.error("未能获取到基金数据，请检查基金代码是否正确。")
                
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
    elif not st.session_state.fund_code:
        st.info("👆 请输入基金代码并点击'开始分析'按钮开始分析")

elif nav_option == "自选基金":
    st.session_state.current_view = "favorite_funds"
    st.markdown('<h1 class="main-header">自选基金</h1>', unsafe_allow_html=True)
    
    if not st.session_state.favorite_funds:
        st.info("您还没有添加任何自选基金，请在基金查询页面添加。")
    else:
        # 显示自选基金列表
        st.markdown("### 我的自选基金")
        
        # 创建多列布局
        cols_per_row = 3
        funds = list(st.session_state.favorite_funds.items())
        
        for i in range(0, len(funds), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(funds):
                    fund_code, fund_data = funds[i + j]
                    with cols[j]:
                        with st.container():
                            # 处理基金名称，移除代码部分
                            fund_name = fund_data['fund_info']['fund_name']
                            if '(' in fund_name:
                                fund_name = fund_name.split('(')[0]
                            elif '（' in fund_name:
                                fund_name = fund_name.split('（')[0]
                            
                            st.markdown(f"""
                            <div class="fund-card">
                                <h4 title="{fund_name}">{fund_name}</h4>
                                <div class="info-row">
                                    <span>代码：{fund_code}</span>
                                    <span>{fund_data['fund_info'].get('fund_type', '未知')}</span>
                                </div>
                                <p class="update-time">更新时间：{fund_data['last_update']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("查看详情", key=f"view_{fund_code}"):
                                    # 打开详情弹窗
                                    show_fund_detail_popup(fund_code)
                            with col2:
                                if st.button("移出自选", key=f"remove_{fund_code}"):
                                    del st.session_state.favorite_funds[fund_code]
                                    save_favorite_funds()
                                    st.rerun()

elif nav_option == "基金比较":
    st.markdown('<h1 class="main-header">基金比较</h1>', unsafe_allow_html=True)
    st.info("🚧 此功能正在开发中，敬请期待...")
    
elif nav_option == "基金投资计划":
    st.markdown('<h1 class="main-header">基金投资计划</h1>', unsafe_allow_html=True)
    st.info("🚧 此功能正在开发中，敬请期待...")
    
else:  # 待开发
    st.markdown('<h1 class="main-header">更多功能</h1>', unsafe_allow_html=True)
    st.info("🚧 更多功能正在开发中，敬请期待...")