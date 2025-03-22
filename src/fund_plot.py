import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import os

# 设置中文字体
def set_chinese_font():
    # 尝试设置中文字体，如果系统中有这些字体
    font_list = ['SimHei', 'Microsoft YaHei', 'SimSun']
    font = None
    
    for font_name in font_list:
        try:
            font = FontProperties(fname=f"C:\\Windows\\Fonts\\{font_name}.ttf")
            break
        except:
            continue
    
    return font

def plot_fund_nav(df, fund_code, title=None, start_date=None, end_date=None):
    """
    绘制基金净值曲线
    
    参数:
        df (pandas.DataFrame): 包含日期和净值数据的DataFrame
        fund_code (str): 基金代码
        title (str, optional): 图表标题，默认为None
        start_date (str, optional): 开始日期，格式为'YYYY-MM-DD'，默认为None
        end_date (str, optional): 结束日期，格式为'YYYY-MM-DD'，默认为None
    """
    if df.empty:
        print("没有数据可以绘制")
        return
    
    # 创建图形和子图
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 设置中文字体
    font = set_chinese_font()
    
    # 绘制单位净值曲线
    line, = ax.plot(df['date'], df['nav'], label='单位净值', color='blue', linewidth=2)
    
    # 设置x轴格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    
    # 设置标题和标签
    if title:
        ax.set_title(title, fontproperties=font, fontsize=16)
    else:
        ax.set_title(f'基金{fund_code}净值走势图', fontproperties=font, fontsize=16)
    
    ax.set_xlabel('日期', fontproperties=font, fontsize=12)
    ax.set_ylabel('净值', fontproperties=font, fontsize=12)
    
    # 添加图例
    ax.legend(prop=font)
    
    # 添加网格
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # 自动调整x轴标签
    fig.autofmt_xdate()
    
    # 添加最新净值标注
    latest = df.iloc[-1]
    ax.annotate(f'最新单位净值: {latest["nav"]:.4f}',
                xy=(latest['date'], latest['nav']),
                xytext=(15, 15),
                textcoords='offset points',
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=.2'),
                fontproperties=font)
    
    # 创建鼠标移动事件处理函数
    def on_mouse_move(event):
        if event.inaxes:
            # 移除之前的垂直线和标注
            for artist in ax.lines + ax.texts:
                if getattr(artist, 'is_cursor_indicator', False):
                    artist.remove()
            
            # 添加新的垂直线
            vline = ax.axvline(event.xdata, color='gray', linestyle='--', alpha=0.5)
            vline.is_cursor_indicator = True
            
            # 获取最接近的数据点
            dates = mdates.num2date(df['date'].map(mdates.date2num))
            idx = min(range(len(dates)), key=lambda i: abs(mdates.date2num(dates[i]) - event.xdata))
            closest_date = dates[idx]
            closest_nav = df['nav'].iloc[idx]
            
            # 添加日期标注
            date_text = ax.text(event.xdata, ax.get_ylim()[0], 
                               closest_date.strftime('%Y-%m-%d'),
                               ha='center', va='top',
                               fontproperties=font)
            date_text.is_cursor_indicator = True
            
            # 添加净值标注
            nav_text = ax.text(event.xdata, closest_nav,
                              f'{closest_nav:.4f}',
                              ha='left', va='bottom',
                              fontproperties=font)
            nav_text.is_cursor_indicator = True
            
            fig.canvas.draw_idle()
    
    # 连接鼠标移动事件
    fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)
    
    # 保存图表
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    fund_dir = os.path.join(base_dir, fund_code)
    if not os.path.exists(fund_dir):
        os.makedirs(fund_dir)
    
    # 如果提供了起止日期，则在文件名中包含这些信息
    if start_date and end_date:
        # 移除日期中的连字符，使文件名更简洁
        start_date_str = start_date.replace('-', '')
        end_date_str = end_date.replace('-', '')
        filename = f'nav_{start_date_str}_{end_date_str}.png'
    else:
        # 如果没有提供日期，则使用当前数据的时间范围
        start_date_str = df['date'].min().strftime('%Y%m%d')
        end_date_str = df['date'].max().strftime('%Y%m%d')
        filename = f'nav_{start_date_str}_{end_date_str}.png'
    
    plt.savefig(os.path.join(fund_dir, filename), dpi=300, bbox_inches='tight')
    
    # 显示图表
    plt.tight_layout()
    plt.show()