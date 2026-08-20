import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone, timedelta
import time
import sys
import re

# 设置时区为东八区（北京时间）
BJ_TZ = timezone(timedelta(hours=8))

# 南开大学就业指导中心招聘信息页面
BASE_URL = "https://career.nankai.edu.cn"
RECRUITMENT_URL = f"{BASE_URL}/correcruit/index.html"

def get_current_time():
    """获取当前北京时间"""
    return datetime.now(BJ_TZ).strftime('%Y-%m-%d %H:%M:%S')

def is_recruitment_link(href):
    """判断链接是否为招聘信息链接"""
    if not href:
        return False
    pattern = r'/correcruit/content/id/\d+\.html'
    return bool(re.search(pattern, href))

def fetch_detail_page(url):
    """
    抓取招聘详情页面的详细信息
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 初始化详细信息
        detail = {
            'company': '',
            'pub_time': '',
            'salary': '',
            'location': '',
            'category': '',
            'degree': '不限',
            'major': '',
            'description': ''
        }
        
        # 尝试多种方式提取信息
        # 1. 从表格中提取
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if '单位名称' in label or '企业名称' in label or '公司' in label:
                        detail['company'] = value
                    elif '发布时间' in label or '发布日期' in label:
                        detail['pub_time'] = value
                    elif '薪资' in label or '待遇' in label or '薪酬' in label:
                        detail['salary'] = value
                    elif '工作地域' in label or '工作地点' in label or '地区' in label:
                        detail['location'] = value
                    elif '职业类别' in label or '职位类别' in label or '岗位类别' in label:
                        detail['category'] = value
                    elif '学历' in label or '学位' in label:
                        detail['degree'] = value
                        if '博士' in value:
                            detail['degree'] = '博士'
                        elif '硕士' in value:
                            detail['degree'] = '硕士'
                        elif '本科' in value:
                            detail['degree'] = '本科'
                        else:
                            detail['degree'] = '不限'
                    elif '专业' in label:
                        detail['major'] = value
        
        # 2. 从定义列表或描述中提取
        if not detail['company']:
            # 尝试从标题中提取公司名称
            title_tag = soup.find('h1') or soup.find('h2') or soup.find('h3')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # 假设标题格式为 "公司名称 - 职位名称" 或 "公司名称招聘"
                if ' - ' in title_text:
                    detail['company'] = title_text.split(' - ')[0]
                elif '招聘' in title_text:
                    detail['company'] = title_text.split('招聘')[0]
        
        # 3. 从页面其他部分提取信息
        page_text = soup.get_text()
        
        # 提取薪资信息
        salary_patterns = [
            r'(\d+[千千万万]?[-~到]\d+[千千万万]?/?[月年]?)',
            r'(\d+[千千万万]?以上/?[月年]?)',
            r'面议',
            r'薪资[：:]\s*([^。\n]*)',
            r'待遇[：:]\s*([^。\n]*)'
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, page_text)
            if match:
                if not detail['salary']:
                    detail['salary'] = match.group(1) if match.groups() else match.group(0)
                break
        
        # 提取工作地点
        location_patterns = [
            r'工作[地点地域][：:]\s*([^。\n]*)',
            r'工作[城市地区][：:]\s*([^。\n]*)'
        ]
        for pattern in location_patterns:
            match = re.search(pattern, page_text)
            if match:
                if not detail['location']:
                    detail['location'] = match.group(1)
                break
        
        # 提取职位类别
        category_patterns = [
            r'职位[类别分类][：:]\s*([^。\n]*)',
            r'职业[类别分类][：:]\s*([^。\n]*)',
            r'岗位[类别分类][：:]\s*([^。\n]*)'
        ]
        for pattern in category_patterns:
            match = re.search(pattern, page_text)
            if match:
                if not detail['category']:
                    detail['category'] = match.group(1)
                break
        
        # 提取发布时间
        time_patterns = [
            r'发布[时间日期][：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'发布时间[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
        ]
        for pattern in time_patterns:
            match = re.search(pattern, page_text)
            if match:
                if not detail['pub_time']:
                    detail['pub_time'] = match.group(1)
                break
        
        # 提取描述信息
        content_div = soup.find('div', class_='content') or soup.find('div', class_='article-content')
        if content_div:
            detail['description'] = content_div.get_text(strip=True)[:500]  # 只取前500字
        
        return detail
        
    except Exception as e:
        print(f"抓取详情页出错: {e}")
        return {}

def fetch_jobs_from_nankai():
    """
    从南开大学就业指导中心抓取招聘信息
    """
    all_jobs = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    max_pages = 50
    total_count = 0
    
    start_time = get_current_time()
    print(f"开始抓取时间: {start_time}")
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = RECRUITMENT_URL
        else:
            url = f"{BASE_URL}/correcruit/index/p/{page}.html"
        
        print(f"\n正在抓取第 {page}/{max_pages} 页: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有招聘信息链接
            all_links = soup.find_all('a', href=True)
            page_count = 0
            
            for link in all_links:
                try:
                    href = link.get('href', '')
                    
                    # 只处理招聘信息链接
                    if not is_recruitment_link(href):
                        continue
                    
                    title = link.get('title') or link.get_text(strip=True)
                    
                    # 处理相对链接
                    if href and not href.startswith('http'):
                        href = BASE_URL + href
                    
                    # 获取发布时间（从列表页）
                    pub_time = ''
                    parent = link.parent
                    if parent:
                        time_span = parent.find('span', class_='time') or parent.find('span', class_='date')
                        if time_span:
                            pub_time = time_span.get_text(strip=True)
                    
                    # 先创建基本信息
                    job_info = {
                        'title': title,
                        'url': href,
                        'company': '',
                        'degree': '不限',
                        'major': '',
                        'salary': '',
                        'location': '',
                        'category': '',
                        'source': '南开大学就业指导中心',
                        'update_time': get_current_time(),
                        'pub_time': pub_time,
                        'description': ''
                    }
                    
                    all_jobs.append(job_info)
                    page_count += 1
                    total_count += 1
                    
                except Exception as e:
                    continue
            
            print(f"第 {page} 页共找到 {page_count} 条招聘信息")
            
            # 如果当前页没有招聘信息，可能已经到最后一页
            if page_count == 0:
                print(f"第 {page} 页没有招聘信息，可能已到最后一页")
                break
            
            # 每页之间等待0.5秒
            time.sleep(0.5)
            
        except Exception as e:
            print(f"抓取第 {page} 页时出错: {e}")
            continue
    
    # 抓取详情页信息
    print(f"\n开始抓取详情页信息...")
    print(f"共 {len(all_jobs)} 条招聘信息需要抓取详情")
    
    for i, job in enumerate(all_jobs):
        print(f"正在抓取第 {i+1}/{len(all_jobs)} 条详情: {job['title']}")
        
        detail = fetch_detail_page(job['url'])
        
        # 更新详细信息
        if detail:
            job['company'] = detail.get('company', '') or job['company']
            job['pub_time'] = detail.get('pub_time', '') or job['pub_time']
            job['salary'] = detail.get('salary', '')
            job['location'] = detail.get('location', '')
            job['category'] = detail.get('category', '')
            job['degree'] = detail.get('degree', '不限')
            job['major'] = detail.get('major', '')
            job['description'] = detail.get('description', '')
        
        # 每抓取一条详情后等待0.3秒
        time.sleep(0.3)
    
    # 记录结束时间
    end_time = get_current_time()
    print(f"\n抓取完成！")
    print(f"开始时间: {start_time}")
    print(f"结束时间: {end_time}")
    print(f"共获取 {total_count} 条招聘信息")
    
    return all_jobs

def save_jobs_to_json(jobs_data):
    """保存招聘信息到JSON文件"""
    os.makedirs('.', exist_ok=True)
    
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 jobs.json")
    print(f"总计 {len(jobs_data)} 条招聘信息")

def main():
    print("=" * 50)
    print("南开大学招聘信息抓取工具（增强版）")
    print("=" * 50)
    print(f"当前时间: {get_current_time()}")
    print(f"Python版本: {sys.version}")
    print("=" * 50)
    
    # 抓取数据
    jobs_data = fetch_jobs_from_nankai()
    
    # 保存数据
    save_jobs_to_json(jobs_data)
    
    # 验证文件已保存
    if os.path.exists('jobs.json'):
        file_size = os.path.getsize('jobs.json')
        print(f"\n文件 jobs.json 已创建，大小: {file_size} 字节")
    else:
        print("\n警告: jobs.json 文件未创建！")
    
    print("\n完成！")

if __name__ == "__main__":
    main()
