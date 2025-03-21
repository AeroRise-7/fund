import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import numpy as np

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fund_data import get_fund_data, get_fund_info
from src.fund_analysis import (
    calculate_max_drawdown,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_annual_return
)

# 初始化session state
if 'fund_code' not in st.session_state:
    st.session_state.fund_code = ''
if 'fund_data' not in st.session_state:
    st.session_state.fund_data = None
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None

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
        margin-bottom: 2rem;
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
    }
    .reportview-container {
        background: #f0f2f6;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 侧边栏导航
st.sidebar.markdown("# 📊 基金分析工具")
st.sidebar.markdown("---")

# 导航选项
nav_option = st.sidebar.radio(
    "功能导航",
    ["基金查询", "基金比较", "基金投资计划", "待开发"]
)

# 主界面内容
if nav_option == "基金查询":
    st.markdown('<h1 class="main-header">基金分析报告</h1>', unsafe_allow_html=True)
    
    # 输入基金代码
    fund_code = st.text_input("👉 请输入基金代码", 
                             value=st.session_state.fund_code,
                             placeholder="例如: 017811")
    
    # 添加分析按钮
    analyze_button = st.button("开始分析", use_container_width=True)
    
    if analyze_button:
        st.session_state.fund_code = fund_code
        st.session_state.fund_data = None  # 清除旧数据
        st.session_state.start_date = None  # 重置日期
        st.session_state.end_date = None
    
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
                    st.markdown(f"**基金名称：** {fund_info.get('fund_name', '未获取到')}")
                    st.markdown(f"**基金公司：** {fund_info.get('fund_company', '未获取到')}")
                with col2:
                    st.markdown(f"**基金代码：** {st.session_state.fund_code}")
                
                # 显示基金数据分析结果
                st.markdown('<h2 class="section-header">净值走势</h2>', unsafe_allow_html=True)
                
                # 创建净值走势图
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['nav'],
                    mode='lines',
                    name='单位净值',
                    line=dict(color='#1f77b4', width=2)
                ))
                
                # 更新布局
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
                nav_change = (df['nav'].iloc[-1] / df['nav'].iloc[0] - 1) * 100
                max_nav = df['nav'].max()
                max_nav_date = df[df['nav'] == max_nav]['date'].iloc[0]
                min_nav = df['nav'].min()
                min_nav_date = df[df['nav'] == min_nav]['date'].iloc[0]
                establishment_date = df['date'].min()
                total_return = ((df['nav'].iloc[-1] / df['nav'].iloc[0]) - 1) * 100
                
                # 使用列布局显示统计信息
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(f"最新净值（{latest_date.strftime('%Y-%m-%d')}）", f"{latest_nav:.4f}")
                with col2:
                    st.metric("累计收益（最新净值/首日净值-1）", f"{nav_change:.2f}%")
                with col3:
                    st.metric(f"历史最高（{max_nav_date.strftime('%Y-%m-%d')}）", f"{max_nav:.4f}")
                with col4:
                    st.metric(f"历史最低（{min_nav_date.strftime('%Y-%m-%d')}）", f"{min_nav:.4f}")
                
                # 显示额外的统计信息
                st.markdown("---")
                st.markdown(f"**基金成立日期：** {establishment_date.strftime('%Y-%m-%d')}")
                st.markdown(f"**最新数据日期：** {latest_date.strftime('%Y-%m-%d')}")
                st.markdown(f"**成立至今收益率：** {total_return:.2f}%")
                
                # 添加基金投资天数指标分析
                st.markdown('<h2 class="section-header">基金投资天数指标分析</h2>', unsafe_allow_html=True)
                
                # 日期选择
                st.markdown("#### 选择投资区间")
                col1, col2 = st.columns(2)
                
                # 使用session state存储日期选择
                with col1:
                    start_date = st.date_input(
                        "开始日期",
                        min_value=establishment_date.date(),
                        max_value=latest_date.date(),
                        value=st.session_state.start_date or establishment_date.date(),
                        key="start_date_input"
                    )
                with col2:
                    end_date = st.date_input(
                        "结束日期",
                        min_value=establishment_date.date(),
                        max_value=latest_date.date(),
                        value=st.session_state.end_date or latest_date.date(),
                        key="end_date_input"
                    )
                
                # 更新session state中的日期
                st.session_state.start_date = start_date
                st.session_state.end_date = end_date
                
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
                    
                    # 计算各项指标
                    # 1. 收益类指标
                    period_return = (period_df['nav'].iloc[-1] / period_df['nav'].iloc[0] - 1) * 100
                    annual_return = (pow(1 + period_return/100, 252/trading_days) - 1) * 100
                    
                    # 2. 风险类指标
                    # 计算日收益率序列
                    period_df['daily_return'] = period_df['nav'].pct_change()
                    # 波动率（年化）
                    daily_volatility = period_df['daily_return'].std()
                    annual_volatility = daily_volatility * np.sqrt(252) * 100
                    
                    # 最大回撤
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
                        st.metric("年化波动率", f"{annual_volatility:.2f}%",
                                help="波动率 = 日收益率的标准差 × √252")
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

elif nav_option == "基金比较":
    st.markdown('<h1 class="main-header">基金比较</h1>', unsafe_allow_html=True)
    st.info("🚧 此功能正在开发中，敬请期待...")
    
elif nav_option == "基金投资计划":
    st.markdown('<h1 class="main-header">基金投资计划</h1>', unsafe_allow_html=True)
    st.info("🚧 此功能正在开发中，敬请期待...")
    
else:  # 待开发
    st.markdown('<h1 class="main-header">更多功能</h1>', unsafe_allow_html=True)
    st.info("🚧 更多功能正在开发中，敬请期待...") 