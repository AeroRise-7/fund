import numpy as np
import pandas as pd

def calculate_max_drawdown(nav_series):
    """
    计算最大回撤率
    最大回撤率 = (谷值 - 峰值) / 峰值 * 100%
    
    参数:
        nav_series: pandas.Series, 净值数据序列
    返回:
        float: 最大回撤率（百分比）
    """
    cummax = nav_series.cummax()
    drawdown = (nav_series - cummax) / cummax
    return float(drawdown.min() * 100)

def calculate_volatility(nav_series):
    """
    计算波动率（年化）
    
    参数:
        nav_series: pandas.Series, 净值数据序列
    返回:
        float: 年化波动率（百分比）
    """
    daily_returns = nav_series.pct_change().dropna()
    return float(daily_returns.std() * np.sqrt(252) * 100)

def calculate_sharpe_ratio(nav_series, risk_free_rate=0.03):
    """
    计算夏普比率
    夏普比率 = (年化收益率 - 无风险利率) / 年化波动率
    
    参数:
        nav_series: pandas.Series, 净值数据序列
        risk_free_rate: float, 无风险利率，默认3%
    返回:
        float: 夏普比率
    """
    daily_returns = nav_series.pct_change().dropna()
    excess_returns = daily_returns - risk_free_rate/252
    if len(excess_returns) == 0:
        return 0
    return float(np.sqrt(252) * excess_returns.mean() / excess_returns.std())

def calculate_annual_return(nav_series):
    """
    计算年化收益率
    
    参数:
        nav_series: pandas.Series, 净值数据序列
    返回:
        float: 年化收益率（百分比）
    """
    try:
        # 确保日期索引是datetime类型
        if not isinstance(nav_series.index, pd.DatetimeIndex):
            nav_series.index = pd.to_datetime(nav_series.index)
        
        # 计算总天数
        total_days = (nav_series.index[-1] - nav_series.index[0]).days
        if total_days <= 0:
            return 0.0
            
        # 计算总收益率
        total_return = (nav_series.iloc[-1] / nav_series.iloc[0]) - 1
        
        # 计算年化收益率
        annual_return = (1 + total_return) ** (365 / total_days) - 1
        return float(annual_return * 100)
    except Exception as e:
        print(f"计算年化收益率时发生错误: {str(e)}")
        return 0.0

def calculate_period_returns(df):
    """
    计算月度、季度和年度收益率
    
    参数:
        df: pandas.DataFrame, 包含日期和净值数据的DataFrame
    返回:
        tuple: (月度收益率, 季度收益率, 年度收益率)
    """
    # 确保日期列是datetime类型
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 计算日收益率
    daily_returns = df['nav'].pct_change()
    
    # 计算月度收益率
    monthly_returns = (1 + daily_returns).resample('M').prod() - 1
    
    # 计算季度收益率
    quarterly_returns = (1 + daily_returns).resample('Q').prod() - 1
    
    # 计算年度收益率
    yearly_returns = (1 + daily_returns).resample('Y').prod() - 1
    
    return monthly_returns, quarterly_returns, yearly_returns

def calculate_return_distribution(nav_series):
    """
    计算收益率分布统计
    
    参数:
        nav_series: pandas.Series, 净值数据序列
    返回:
        dict: 包含收益率分布统计信息的字典
    """
    # 计算日收益率
    returns = nav_series.pct_change().dropna()
    
    # 计算统计指标
    stats = {
        'mean': returns.mean() * 100,  # 平均日收益率
        'std': returns.std() * 100,    # 标准差
        'skew': returns.skew(),        # 偏度
        'kurtosis': returns.kurtosis(), # 峰度
        'min': returns.min() * 100,     # 最小值
        'max': returns.max() * 100,     # 最大值
        'median': returns.median() * 100 # 中位数
    }
    
    # 计算分位数
    percentiles = [1, 5, 10, 25, 75, 90, 95, 99]
    for p in percentiles:
        stats[f'percentile_{p}'] = np.percentile(returns, p) * 100
    
    return stats