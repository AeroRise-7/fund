import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import os
from matplotlib.font_manager import FontProperties
from src.fund_plot import set_chinese_font

def plot_risk_metrics(df, fund_code, max_drawdown, volatility, sharpe_ratio, annual_return):
    """
    绘制风险指标可视化图表
    
    参数:
        df: pandas.DataFrame, 包含日期和净值数据的DataFrame
        fund_code: str, 基金代码
        max_drawdown: float, 最大回撤率
        volatility: float, 波动率
        sharpe_ratio: float, 夏普比率
        annual_return: float, 年化收益率
    """
    # 设置中文字体
    font = set_chinese_font()
    
    # 创建图形和子图
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'基金{fund_code}风险指标分析', fontproperties=font, fontsize=20)
    
    # 1. 绘制累计收益曲线
    ax1 = axs[0, 0]
    returns = df['nav'].pct_change().fillna(0)
    cumulative_returns = (1 + returns).cumprod() - 1
    ax1.plot(df['date'], cumulative_returns * 100, 'b-', linewidth=2)
    ax1.set_title('累计收益率(%)', fontproperties=font, fontsize=14)
    ax1.set_xlabel('日期', fontproperties=font)
    ax1.set_ylabel('累计收益率(%)', fontproperties=font)
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # 2. 绘制回撤曲线
    ax2 = axs[0, 1]
    running_max = np.maximum.accumulate(df['nav'])
    drawdown = (df['nav'] - running_max) / running_max * 100
    ax2.fill_between(df['date'], drawdown, 0, color='r', alpha=0.3)
    ax2.plot(df['date'], drawdown, 'r-', linewidth=1)
    ax2.set_title('回撤率(%)', fontproperties=font, fontsize=14)
    ax2.set_xlabel('日期', fontproperties=font)
    ax2.set_ylabel('回撤率(%)', fontproperties=font)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # 3. 绘制风险指标条形图
    ax3 = axs[1, 0]
    metrics = ['年化收益率', '波动率', '最大回撤率', '夏普比率']
    values = [annual_return, volatility, max_drawdown, sharpe_ratio]
    colors = ['green', 'orange', 'red', 'blue']
    
    bars = ax3.bar(range(len(metrics)), values, color=colors, alpha=0.7)
    ax3.set_title('风险收益指标', fontproperties=font, fontsize=14)
    ax3.set_ylabel('百分比/比率', fontproperties=font)
    ax3.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # 设置x轴刻度和标签
    ax3.set_xticks(range(len(metrics)))
    ax3.set_xticklabels(metrics, fontproperties=font)
    
    # 在柱状图上添加数值标签
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{value:.2f}', ha='center', va='bottom', fontproperties=font)
    
    # 4. 绘制日收益率分布直方图
    ax4 = axs[1, 1]
    daily_returns = df['nav'].pct_change().dropna() * 100
    sns.histplot(daily_returns, kde=True, ax=ax4, bins=30, color='skyblue')
    ax4.set_title('日收益率分布', fontproperties=font, fontsize=14)
    ax4.set_xlabel('日收益率(%)', fontproperties=font)
    ax4.set_ylabel('频率', fontproperties=font)
    ax4.grid(True, linestyle='--', alpha=0.7)
    
    # 添加均值和标准差的垂直线
    mean_return = daily_returns.mean()
    std_return = daily_returns.std()
    ax4.axvline(mean_return, color='r', linestyle='--', alpha=0.8, label=f'均值: {mean_return:.2f}%')
    ax4.axvline(mean_return + std_return, color='g', linestyle='--', alpha=0.8, label=f'+1σ: {mean_return + std_return:.2f}%')
    ax4.axvline(mean_return - std_return, color='g', linestyle='--', alpha=0.8, label=f'-1σ: {mean_return - std_return:.2f}%')
    ax4.legend(prop=font)
    
    # 调整布局
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # 保存图表
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    fund_dir = os.path.join(base_dir, fund_code)
    if not os.path.exists(fund_dir):
        os.makedirs(fund_dir)
    
    # 从df中获取时间范围
    start_date = df['date'].min().strftime('%Y%m%d')
    end_date = df['date'].max().strftime('%Y%m%d')
    filename = f'risk_analysis_{start_date}_{end_date}.png'
    plt.savefig(os.path.join(fund_dir, filename), dpi=300, bbox_inches='tight')
    
    return fig

def plot_period_returns(monthly_returns, quarterly_returns, yearly_returns, fund_code, start_date=None, end_date=None):
    """
    绘制月度/季度/年度收益率图表
    
    参数:
        monthly_returns: pandas.Series, 月度收益率
        quarterly_returns: pandas.Series, 季度收益率
        yearly_returns: pandas.Series, 年度收益率
        fund_code: str, 基金代码
        start_date: str, 可选，开始日期，格式为YYYY-MM-DD
        end_date: str, 可选，结束日期，格式为YYYY-MM-DD
    """
    # 设置中文字体
    font = set_chinese_font()
    
    # 创建图形和子图
    fig, axs = plt.subplots(3, 1, figsize=(14, 18))
    fig.suptitle(f'基金{fund_code}周期收益分析', fontproperties=font, fontsize=20)
    
    # 1. 月度收益率
    ax1 = axs[0]
    monthly_returns = monthly_returns * 100  # 转换为百分比
    bars = ax1.bar(monthly_returns.index.strftime('%Y-%m'), monthly_returns.values,
                  color=[('green' if x >= 0 else 'red') for x in monthly_returns.values],
                  alpha=0.7)
    ax1.set_title('月度收益率(%)', fontproperties=font, fontsize=16)
    ax1.set_ylabel('收益率(%)', fontproperties=font)
    ax1.grid(True, linestyle='--', alpha=0.7, axis='y')
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # 设置x轴标签
    if len(monthly_returns) > 12:
        # 如果数据点过多，只显示部分标签
        for i, tick in enumerate(ax1.get_xticklabels()):
            if i % 3 != 0:  # 每隔3个显示一个
                tick.set_visible(False)
    
    # 2. 季度收益率
    ax2 = axs[1]
    quarterly_returns = quarterly_returns * 100  # 转换为百分比
    bars = ax2.bar(quarterly_returns.index.strftime('%Y-Q%q'), quarterly_returns.values,
                  color=[('green' if x >= 0 else 'red') for x in quarterly_returns.values],
                  alpha=0.7)
    ax2.set_title('季度收益率(%)', fontproperties=font, fontsize=16)
    ax2.set_ylabel('收益率(%)', fontproperties=font)
    ax2.grid(True, linestyle='--', alpha=0.7, axis='y')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # 3. 年度收益率
    ax3 = axs[2]
    yearly_returns = yearly_returns * 100  # 转换为百分比
    bars = ax3.bar(yearly_returns.index.strftime('%Y'), yearly_returns.values,
                  color=[('green' if x >= 0 else 'red') for x in yearly_returns.values],
                  alpha=0.7, width=0.6)
    ax3.set_title('年度收益率(%)', fontproperties=font, fontsize=16)
    ax3.set_ylabel('收益率(%)', fontproperties=font)
    ax3.grid(True, linestyle='--', alpha=0.7, axis='y')
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # 在柱状图上添加数值标签
    for ax, returns in zip([ax1, ax2, ax3], [monthly_returns, quarterly_returns, yearly_returns]):
        for bar, value in zip(ax.patches, returns.values):
            height = bar.get_height()
            # 根据值的正负决定标签位置
            if value >= 0:
                va = 'bottom'
                y_pos = height + 0.5
            else:
                va = 'top'
                y_pos = height - 0.5
            ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                    f'{value:.2f}%', ha='center', va=va, fontproperties=font, fontsize=8)
    
    # 调整布局
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # 保存图表
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    fund_dir = os.path.join(base_dir, fund_code)
    if not os.path.exists(fund_dir):
        os.makedirs(fund_dir)
    
    # 获取时间范围
    if start_date is None or end_date is None:
        # 如果没有提供日期，则从收益率数据的索引中获取
        if not monthly_returns.empty:
            date_range = monthly_returns.index
            start_date_str = date_range.min().strftime('%Y%m%d')
            end_date_str = date_range.max().strftime('%Y%m%d')
        else:
            # 如果没有数据，使用当前日期
            import datetime
            current_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date_str = current_date
            end_date_str = current_date
    else:
        # 将传入的日期字符串转换为所需格式
        start_date_str = start_date.replace('-', '')
        end_date_str = end_date.replace('-', '')
    
    filename = f'period_returns_{start_date_str}_{end_date_str}.png'
    plt.savefig(os.path.join(fund_dir, filename), dpi=300, bbox_inches='tight')
    
    return fig

def plot_return_distribution(return_stats, fund_code, start_date=None, end_date=None):
    """
    绘制收益分布分析图表
    
    参数:
        return_stats: dict, 收益率分布统计信息
        fund_code: str, 基金代码
        start_date: str, 可选，开始日期，格式为YYYY-MM-DD
        end_date: str, 可选，结束日期，格式为YYYY-MM-DD
    """
    # 设置中文字体
    font = set_chinese_font()
    
    # 创建图形和子图
    fig, axs = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle(f'基金{fund_code}收益分布分析', fontproperties=font, fontsize=20)
    
    # 1. 收益率统计指标表格
    ax1 = axs[0]
    ax1.axis('off')  # 关闭坐标轴
    
    # 准备表格数据
    table_data = [
        ['指标', '值'],
        ['平均日收益率(%)', f"{return_stats['mean']:.4f}"],
        ['标准差(%)', f"{return_stats['std']:.4f}"],
        ['偏度', f"{return_stats['skew']:.4f}"],
        ['峰度', f"{return_stats['kurtosis']:.4f}"],
        ['最小值(%)', f"{return_stats['min']:.4f}"],
        ['最大值(%)', f"{return_stats['max']:.4f}"],
        ['中位数(%)', f"{return_stats['median']:.4f}"],
        ['1%分位数(%)', f"{return_stats['percentile_1']:.4f}"],
        ['5%分位数(%)', f"{return_stats['percentile_5']:.4f}"],
        ['95%分位数(%)', f"{return_stats['percentile_95']:.4f}"],
        ['99%分位数(%)', f"{return_stats['percentile_99']:.4f}"]
    ]
    
    # 创建表格
    table = ax1.table(cellText=table_data, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2)  # 调整表格大小
    
    # 设置表格样式
    for (i, j), cell in table.get_celld().items():
        if i == 0:  # 表头行
            cell.set_text_props(fontproperties=font, weight='bold')
            cell.set_facecolor('lightgray')
        else:
            cell.set_text_props(fontproperties=font)
        if j == 0:  # 第一列
            cell.set_text_props(fontproperties=font, weight='bold')
    
    # 2. 收益率分布箱线图和小提琴图
    ax2 = axs[1]
    
    # 提取分位数数据
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    percentile_values = [return_stats[f'percentile_{p}'] if p != 50 else return_stats['median'] for p in percentiles]
    
    # 绘制箱线图
    box_data = [return_stats['min'], return_stats['percentile_25'], return_stats['median'], 
               return_stats['percentile_75'], return_stats['max']]
    ax2.boxplot([box_data], vert=False, widths=0.7, patch_artist=True, 
               boxprops=dict(facecolor='lightblue', color='black', alpha=0.7))
    
    # 设置标题和标签
    ax2.set_title('收益率分布', fontproperties=font, fontsize=14)
    ax2.set_xlabel('收益率(%)', fontproperties=font)
    ax2.set_ylabel('分布', fontproperties=font)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # 添加分位数标注
    for i, (p, v) in enumerate(zip(percentiles, percentile_values)):
        ax2.text(v, 1.1, f'{p}%: {v:.2f}%', 
                ha='center', va='bottom', 
                fontproperties=font, fontsize=8, 
                rotation=45)
    
    # 调整布局
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # 保存图表
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    fund_dir = os.path.join(base_dir, fund_code)
    if not os.path.exists(fund_dir):
        os.makedirs(fund_dir)
    
    # 获取时间范围
    if start_date is None or end_date is None:
        # 如果没有提供日期，使用当前日期
        import datetime
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date_str = current_date
        end_date_str = current_date
    else:
        # 将传入的日期字符串转换为所需格式
        start_date_str = start_date.replace('-', '')
        end_date_str = end_date.replace('-', '')
    
    filename = f'return_distribution_{start_date_str}_{end_date_str}.png'
    plt.savefig(os.path.join(fund_dir, filename), dpi=300, bbox_inches='tight')
    
    return fig