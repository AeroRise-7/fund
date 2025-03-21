import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import datetime
from io import StringIO
import os
import json

# 定义缓存目录
CACHE_DIR = "data/fund_cache"

def get_fund_info(fund_code):
    """获取基金基本信息，包括基金名称、公司等"""
    try:
        # 使用天天基金搜索API获取基金信息
        search_url = f"http://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?callback=&m=1&key={fund_code}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(search_url, headers=headers)
        
        # 初始化返回的字典
        fund_info = {
            'fund_name': '未获取到',
            'fund_company': '未获取到',
            'fund_code': fund_code
        }
        
        # 解析返回的JSON数据
        try:
            data = response.json()
            if 'Datas' in data and len(data['Datas']) > 0:
                for item in data['Datas']:
                    if item['CODE'] == fund_code:
                        fund_info['fund_name'] = item['NAME']
                        fund_info['fund_company'] = item['FundBaseInfo']['JJGS']
                        break
        except Exception as e:
            print(f"解析基金信息时发生错误: {str(e)}")
        
        return fund_info
        
    except Exception as e:
        print(f"获取基金信息时发生错误: {str(e)}")
        return {
            'fund_name': '未获取到',
            'fund_company': '未获取到',
            'fund_code': fund_code
        }

def get_cached_fund_data(fund_code):
    """从本地缓存获取基金数据"""
    cache_file = os.path.join(CACHE_DIR, f"{fund_code}.csv")
    meta_file = os.path.join(CACHE_DIR, f"{fund_code}_meta.json")
    
    if os.path.exists(cache_file) and os.path.exists(meta_file):
        try:
            # 读取缓存数据
            df = pd.read_csv(cache_file)
            df['date'] = pd.to_datetime(df['date'])
            
            # 读取元数据
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)
            
            # 检查最后更新时间
            last_update = pd.to_datetime(meta_data['last_update'])
            current_time = pd.to_datetime(datetime.datetime.now())
            
            # 如果今天已经更新过，直接返回缓存数据
            if last_update.date() == current_time.date():
                print(f"使用今日已更新的缓存数据（最后更新：{last_update.strftime('%Y-%m-%d %H:%M:%S')}）")
                return df, True  # 返回第二个参数表示是否是今日数据
            
            print(f"找到缓存数据（最后更新：{last_update.strftime('%Y-%m-%d %H:%M:%S')}），检查是否需要更新...")
            return df, False  # 返回第二个参数表示是否是今日数据
            
        except Exception as e:
            print(f"读取缓存数据时发生错误: {str(e)}")
            # 如果读取出错，删除可能损坏的缓存文件
            try:
                os.remove(cache_file)
                os.remove(meta_file)
            except:
                pass
    return None, False

def save_fund_data_to_cache(fund_code, df):
    """保存基金数据到本地缓存"""
    try:
        # 确保缓存目录存在
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        # 保存数据文件
        cache_file = os.path.join(CACHE_DIR, f"{fund_code}.csv")
        df.to_csv(cache_file, index=False)
        
        # 保存元数据
        meta_file = os.path.join(CACHE_DIR, f"{fund_code}_meta.json")
        meta_data = {
            'last_update': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fund_code': fund_code,
            'data_count': len(df),
            'date_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d')
            }
        }
        with open(meta_file, 'w') as f:
            json.dump(meta_data, f, indent=4)
        
        print(f"数据已缓存到: {cache_file}")
        
    except Exception as e:
        print(f"保存缓存数据时发生错误: {str(e)}")

def get_fund_data(fund_code, start_date=None, end_date=None, fill_missing=False):
    """获取基金历史净值数据，支持缓存和智能更新"""
    try:
        # 设置结束日期为当前日期
        if end_date is None:
            end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 获取缓存数据
        cached_data, is_today = get_cached_fund_data(fund_code)
        
        if cached_data is not None:
            if is_today:
                # 如果是今天的数据，直接返回
                return cached_data
            
            # 获取缓存的最后一个日期
            last_cache_date = cached_data['date'].max()
            current_date = pd.to_datetime(end_date)
            
            # 如果缓存数据不是最新的，获取增量更新
            if current_date.date() > last_cache_date.date():
                print(f"缓存数据需要更新，获取 {last_cache_date.strftime('%Y-%m-%d')} 之后的数据...")
                # 获取增量数据
                increment_start = (last_cache_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                new_data = fetch_fund_data_from_api(fund_code, increment_start, end_date)
                
                if not new_data.empty:
                    # 合并新旧数据
                    df = pd.concat([cached_data, new_data], ignore_index=True)
                    df = df.drop_duplicates(subset=['date']).sort_values('date')
                    # 更新缓存
                    save_fund_data_to_cache(fund_code, df)
                    print("缓存数据已更新")
                else:
                    print("没有新数据需要更新")
                    df = cached_data
            else:
                print("缓存数据已是最新，无需更新")
                df = cached_data
        else:
            # 获取完整历史数据
            print(f"未找到缓存数据，开始获取基金{fund_code}的完整历史数据...")
            df = fetch_fund_data_from_api(fund_code, None, None)  # 不需要传入日期参数
            if not df.empty:
                save_fund_data_to_cache(fund_code, df)
        
        # 填充非交易日数据
        if fill_missing and not df.empty:
            date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
            df = df.set_index('date').reindex(date_range)
            df = df.ffill()  # 使用ffill()替代fillna(method='ffill')
            df = df.reset_index().rename(columns={'index': 'date'})
        
        return df
    
    except Exception as e:
        print(f"获取基金数据时发生错误: {str(e)}")
        return pd.DataFrame()

def fetch_fund_data_from_api(fund_code, start_date, end_date):
    """从API获取基金数据，使用分页方式从最新日期往前滚动获取"""
    all_data = pd.DataFrame()
    page = 1
    per_page = 20  # 每页数据量，东方财富默认20条
    
    print(f"开始获取基金{fund_code}的历史数据...")
    
    while True:
        try:
            # 构建API URL，添加分页参数
            url = f"http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={fund_code}&per={per_page}&page={page}"
            
            # 发送请求获取数据
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            
            # 检查是否有"暂无数据"
            if "暂无数据" in response.text:
                print(f"已获取所有数据")
                break
            
            # 使用StringIO包装HTML内容
            try:
                df = pd.read_html(StringIO(response.text))[0]
            except Exception as e:
                print(f"解析HTML表格时发生错误: {str(e)}")
                if page == 1:
                    return pd.DataFrame()
                break
            
            # 如果没有数据了，退出循环
            if df.empty:
                break
            
            # 重命名列
            df.columns = ['date', 'nav', 'acc_nav', 'daily_return', 'subscription_status', 'redemption_status', 'dividend']
            
            # 转换日期列
            df['date'] = pd.to_datetime(df['date'])
            
            # 转换净值列为数值类型
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
            
            # 合并数据
            all_data = pd.concat([all_data, df[['date', 'nav']]], ignore_index=True)
            
            print(f"第{page}页: 获取到{len(df)}条数据，最早日期: {df['date'].min().strftime('%Y-%m-%d')}")
            
            # 检查是否还有下一页（通过数据量判断）
            if len(df) < per_page:
                print("已到达最后一页")
                break
            
            # 下一页
            page += 1
            
            # 添加延迟，避免请求过于频繁
            time.sleep(0.5)
            
        except Exception as e:
            print(f"获取第 {page} 页数据时发生错误: {str(e)}")
            if page == 1:
                return pd.DataFrame()
            break
    
    if not all_data.empty:
        # 删除无效数据并排序
        all_data = all_data.dropna(subset=['date', 'nav'])
        all_data = all_data.sort_values('date')
        all_data = all_data.drop_duplicates(subset=['date'])
        print(f"共获取到 {len(all_data)} 条数据记录，日期范围：{all_data['date'].min().strftime('%Y-%m-%d')} 至 {all_data['date'].max().strftime('%Y-%m-%d')}")
    
    return all_data

def fetch_fund_data_segment(fund_code, start_date, end_date):
    """获取指定时间段的基金数据，支持分页"""
    segment_data = pd.DataFrame()
    page = 1
    per_page = 100  # 每页数据量
    
    while True:
        try:
            # 构建API URL，添加分页参数
            url = f"http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={fund_code}&sdate={start_date}&edate={end_date}&per={per_page}&page={page}"
            
            # 发送请求获取数据
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            
            # 检查是否有"暂无数据"
            if "暂无数据" in response.text:
                if page == 1:
                    print(f"当前时间段无数据")
                break
            
            # 使用StringIO包装HTML内容
            try:
                df = pd.read_html(StringIO(response.text))[0]
            except Exception as e:
                print(f"解析HTML表格时发生错误: {str(e)}")
                break
            
            # 如果没有数据了，退出循环
            if df.empty:
                break
            
            # 重命名列
            df.columns = ['date', 'nav', 'acc_nav', 'daily_return', 'subscription_status', 'redemption_status', 'dividend']
            
            # 转换日期列
            df['date'] = pd.to_datetime(df['date'])
            
            # 转换净值列为数值类型
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
            
            # 合并数据
            segment_data = pd.concat([segment_data, df[['date', 'nav']]], ignore_index=True)
            
            # 检查是否还有下一页
            if len(df) < per_page:
                break
            
            # 下一页
            page += 1
            
            # 添加延迟，避免请求过于频繁
            time.sleep(0.5)
            
        except Exception as e:
            print(f"获取第 {page} 页数据时发生错误: {str(e)}")
            break
    
    return segment_data

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