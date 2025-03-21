import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fund_data import get_fund_data
from src.fund_plot import plot_fund_nav
from src.fund_analysis import (
    calculate_max_drawdown,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_annual_return,
    calculate_period_returns,
    calculate_return_distribution
)
from src.fund_visualization import (
    plot_risk_metrics,
    plot_period_returns,
    plot_return_distribution
)
import datetime

def validate_date(date_str):
    """验证日期格式是否正确"""
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def main():
    print("=" * 50)
    print("基金净值查询与分析工具")
    print("=" * 50)
    
    # 获取用户输入
    fund_code = input("请输入基金代码 (例如: 005827): ").strip()
    
    # 验证基金代码
    if not fund_code.isdigit() or len(fund_code) != 6:
        print("错误: 基金代码必须是6位数字")
        return
    
    # 获取日期范围
    default_end_date = datetime.datetime.now().strftime('%Y-%m-%d')
    default_start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
    
    print(f"\n请输入查询日期范围 (默认为过去一年: {default_start_date} 至 {default_end_date})")
    start_date = input(f"开始日期 (YYYY-MM-DD) [{default_start_date}]: ").strip()
    end_date = input(f"结束日期 (YYYY-MM-DD) [{default_end_date}]: ").strip()
    
    # 使用默认值（如果用户未输入）
    if not start_date:
        start_date = default_start_date
    if not end_date:
        end_date = default_end_date
    
    # 验证日期格式
    if not validate_date(start_date) or not validate_date(end_date):
        print("错误: 日期格式不正确，请使用YYYY-MM-DD格式")
        return
    
    # 验证日期范围
    start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    
    if start_dt > end_dt:
        print("错误: 开始日期不能晚于结束日期")
        return
    
    print(f"\n正在获取基金 {fund_code} 从 {start_date} 到 {end_date} 的净值数据...")
    
    # 获取基金数据
    fill_missing = input("是否显示非交易日数据？(y/n，y则保留非交易日并使用上一交易日数据，n则仅显示交易日): ").strip().lower() == 'y'
    df = get_fund_data(fund_code, start_date, end_date, fill_missing=fill_missing)
    
    if df.empty:
        print("未找到数据，请检查基金代码是否正确或调整日期范围")
        return
    
    print(f"\n成功获取 {len(df)} 条净值记录")
    actual_start_date = df['date'].min().strftime('%Y-%m-%d')
    actual_end_date = df['date'].max().strftime('%Y-%m-%d')
    print(f"数据日期范围: {actual_start_date} 至 {actual_end_date}")
    
    # 检查实际获取的日期范围与用户请求的日期范围是否一致
    if actual_start_date != start_date or actual_end_date != end_date:
        print("\n注意: 实际获取的数据日期范围与请求的日期范围不完全一致")
        print("这可能是因为:")
        print("1. 基金在请求的某些日期没有交易数据")
        print("2. 请求的日期范围超出了基金的存续期")
        print("3. 未来日期的数据尚未产生")
    
    # 计算基础技术指标
    nav_series = df['nav']
    max_drawdown = calculate_max_drawdown(nav_series)
    volatility = calculate_volatility(nav_series)
    sharpe_ratio = calculate_sharpe_ratio(nav_series)
    annual_return = calculate_annual_return(nav_series)
    
    # 计算周期收益率
    monthly_returns, quarterly_returns, yearly_returns = calculate_period_returns(df)
    
    # 计算收益分布统计
    return_stats = calculate_return_distribution(nav_series)
    
    # 显示基本统计信息
    print("\n基本统计信息:")
    print(f"起始单位净值: {df['nav'].iloc[0]:.4f}")
    print(f"最新单位净值: {df['nav'].iloc[-1]:.4f}")
    print(f"区间涨跌幅: {((df['nav'].iloc[-1] / df['nav'].iloc[0]) - 1) * 100:.2f}%")
    
    # 显示风险收益指标
    print("\n风险收益指标:")
    print(f"年化收益率: {annual_return:.2f}%")
    print(f"最大回撤率: {max_drawdown:.2f}%")
    print(f"波动率: {volatility:.2f}%")
    print(f"夏普比率: {sharpe_ratio:.2f}")
    
    # 绘制净值曲线
    print("\n正在绘制净值曲线...")
    plot_fund_nav(df, fund_code, start_date=start_date, end_date=end_date)
    
    # 绘制风险指标可视化
    print("\n正在生成风险指标分析图表...")
    plot_risk_metrics(df, fund_code, max_drawdown, volatility, sharpe_ratio, annual_return)
    
    # 绘制周期收益分析
    print("\n正在生成周期收益分析图表...")
    plot_period_returns(monthly_returns, quarterly_returns, yearly_returns, fund_code, start_date=start_date, end_date=end_date)
    
    # 绘制收益分布分析
    print("\n正在生成收益分布分析图表...")
    plot_return_distribution(return_stats, fund_code, start_date=start_date, end_date=end_date)
    
    print("\n所有图表已保存到 data 目录")

if __name__ == "__main__":
    main()