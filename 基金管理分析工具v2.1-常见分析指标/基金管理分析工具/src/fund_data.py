import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import datetime

def get_fund_data(fund_code, start_date, end_date, fill_missing=False):
    """
    获取指定基金在指定日期范围内的净值数据
    
    参数:
        fund_code (str): 基金代码
        start_date (str): 开始日期，格式为 'YYYY-MM-DD'
        end_date (str): 结束日期，格式为 'YYYY-MM-DD'
        fill_missing (bool): 是否填充缺失的日期数据，默认为False
    
    返回:
        pandas.DataFrame: 包含日期和净值数据的DataFrame
    """
    # 将日期字符串转换为datetime对象
    start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    
    # 初始化结果列表
    all_data = []
    
    # 计算总天数
    total_days = (end_dt - start_dt).days
    
    # 使用tqdm创建总体进度条
    main_pbar = tqdm(desc=f"获取基金{fund_code}数据", total=total_days, unit="天")
    
    # 如果时间跨度大于90天，则分段请求
    if total_days > 90:
        # 每次请求90天的数据
        current_start_dt = start_dt
        while current_start_dt < end_dt:
            # 计算当前段的结束日期
            current_end_dt = min(current_start_dt + datetime.timedelta(days=90), end_dt)
            
            # 转换为字符串格式
            current_start_date = current_start_dt.strftime('%Y-%m-%d')
            current_end_date = current_end_dt.strftime('%Y-%m-%d')
            
            # 获取当前时间段的数据
            segment_data = _fetch_fund_data(fund_code, current_start_date, current_end_date)
            all_data.extend(segment_data)
            
            # 更新进度条
            days_processed = min(90, (current_end_dt - current_start_dt).days)
            main_pbar.update(days_processed)
            
            # 移动到下一个时间段
            current_start_dt = current_end_dt + datetime.timedelta(days=1)
            
            # 添加延迟，避免请求过于频繁
            time.sleep(1)
    else:
        # 时间跨度小于90天，直接请求
        all_data = _fetch_fund_data(fund_code, start_date, end_date)
        main_pbar.update(total_days)
    
    main_pbar.close()
    
    # 转换为DataFrame
    df = pd.DataFrame(all_data)
    
    # 转换数据类型
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
        df['acc_nav'] = pd.to_numeric(df['acc_nav'], errors='coerce')
        
        # 按日期排序
        df = df.sort_values('date')
        
        # 去除可能的重复数据
        df = df.drop_duplicates(subset=['date'])
        
        # 如果需要填充缺失的日期数据
        if fill_missing and not df.empty:
            # 创建完整的日期范围
            date_range = pd.date_range(start=start_dt, end=end_dt)
            
            # 创建一个新的DataFrame，包含完整的日期范围
            full_df = pd.DataFrame({'date': date_range})
            
            # 将原始数据与完整日期范围合并
            df = pd.merge(full_df, df, on='date', how='left')
            
            # 前向填充缺失值（使用前一个交易日的数据）
            df['nav'] = df['nav'].fillna(method='ffill')
            df['acc_nav'] = df['acc_nav'].fillna(method='ffill')
            
            print(f"注意: 已填充 {len(date_range) - len(all_data)} 个非交易日的数据点")
    
    return df

def _fetch_fund_data(fund_code, start_date, end_date):
    """
    从东方财富网获取指定时间段的基金净值数据
    
    参数:
        fund_code (str): 基金代码
        start_date (str): 开始日期，格式为 'YYYY-MM-DD'
        end_date (str): 结束日期，格式为 'YYYY-MM-DD'
    
    返回:
        list: 包含基金净值数据的列表
    """
    # 初始化结果列表和页码
    segment_data = []
    page = 1
    per_page = 20  # 每页最大条目数
    
    while True:
        # 构建API URL
        url = f"http://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code={fund_code}&sdate={start_date}&edate={end_date}&per={per_page}&page={page}"
        
        # 发送请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        
        # 解析HTML
        print(f"正在获取第 {page} 页数据...")
        
        # 调试信息：输出响应内容的一部分
        if page == 1:
            print(f"API响应前100个字符: {response.text[:100]}...")
        
        # 处理JavaScript包装的HTML内容
        content = response.text
        # 提取var apidata={ content:"<table>...</table>" }中的<table>...</table>部分
        if 'content:"' in content:
            html_content = content.split('content:"')[1].split('",')[0]
            # 替换转义字符
            html_content = html_content.replace('\\', '\\').replace('\"', '"')
            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table')
        else:
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table', class_='w782 comm lsjz')
        
        # 如果没有找到表格或表格为空
        if not table or not table.find_all('tr'):
            if page == 1:  # 如果是第一页就没有数据，说明可能有问题
                print(f"警告: 无法获取数据，API返回为空。这可能是因为：")
                print(f"1. 基金代码 {fund_code} 在 {start_date} 之前可能尚未成立")
                print(f"2. 东方财富网可能限制了历史数据的查询范围")
                print(f"3. 网络连接问题或API暂时不可用")
                print(f"建议：尝试调整查询日期范围或稍后重试")
            break
        
        # 解析表格数据
        rows = table.find_all('tr')
        row_count = len(rows) - 1  # 减去表头
        print(f"第 {page} 页找到 {row_count} 条数据记录")
        
        for row in rows[1:]:  # 跳过表头
            cells = row.find_all('td')
            if len(cells) >= 3:
                date = cells[0].text.strip()
                nav = cells[1].text.strip()  # 单位净值
                acc_nav = cells[2].text.strip()  # 累计净值
                
                segment_data.append({
                    'date': date,
                    'nav': nav,
                    'acc_nav': acc_nav
                })
        
        # 检查是否有下一页
        # 从页面中查找分页信息
        pager_text = soup.find('div', class_='pagebtns')
        if pager_text:
            print(f"页面 {page} 分页信息: {pager_text.text.strip()}")
        
        # 查找页码信息，确定是否有下一页
        # 在JavaScript包装的HTML中，分页信息可能在不同的位置
        has_next_page = False
        
        # 检查是否有分页信息
        if pager_text:
            print(f"页面 {page} 分页信息: {pager_text.text.strip()}")
            if '下一页' in pager_text.text:
                has_next_page = True
                print(f"检测到下一页按钮，将继续获取第 {page+1} 页")
        
        # 如果没有明确的分页信息，但数据量达到每页上限，可能还有下一页
        elif row_count >= per_page:
            has_next_page = True
            print(f"当前页 (第{page}页) 数据达到 {per_page} 条上限，可能有下一页")
        
        # 如果没有下一页，退出循环
        if not has_next_page:
            if pager_text:
                print(f"已到达最后一页 (第{page}页)")
            else:
                print(f"当前页 (第{page}页) 数据不足 {per_page} 条，判断为最后一页")
            break
        
        # 增加页码
        page += 1
        
        # 添加延迟，避免请求过于频繁
        time.sleep(0.5)
    
    return segment_data