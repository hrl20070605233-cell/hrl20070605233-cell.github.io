import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

# 南开大学就业指导中心招聘信息页面
BASE_URL = "https://career.nankai.edu.cn"
RECRUITMENT_URL = f"{BASE_URL}/correcruit/index.html"

def fetch_jobs_from_nankai():
    """
    从南开大学就业指导中心抓取招聘信息（抓取全部50页）
    """
    all_jobs = {
        "博士": [],
        "硕士": [],
        "本科": [],
        "不限": []
    }
    
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }
    
    # 抓取全部50页
    max_pages = 50
    total_count = 0
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = RECRUITMENT_URL
        else:
            url = f"{BASE_URL}/correcruit/index/p/{page}.html"
        
        print(f"\n正在抓取第 {page}/{max_pages} 页: {url}")
        
        try:
            # 发送请求
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                continue
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找招聘信息列表
            job_list = soup.find('div', class_='recruit-list') or soup.find('ul', class_='news-list')
            
            if not job_list:
                # 尝试其他常见结构
                job_list = soup.find('div', class_='list-content') or soup.find('div', class_='article-list')
            
            if job_list:
                # 提取招聘信息
                items = job_list.find_all('li') or job_list.find_all('div', class_='item')
                
                if not items:
                    # 尝试查找所有链接
                    items = job_list.find_all('a', href=True)
                
                page_count = 0
                for item in items:
                    try:
                        # 提取标题和链接
                        link = item.find('a') if item.name != 'a' else item
                        if not link or not link.get('href'):
                            continue
                        
                        title = link.get('title') or link.get_text(strip=True)
                        url = link.get('href', '')
                        
                        # 处理相对链接
                        if url and not url.startswith('http'):
                            url = BASE_URL + url
                        
                        # 跳过非招聘链接
                        if not title or len(title) < 5:
                            continue
                        
                        # 提取发布时间
                        time_span = item.find('span', class_='time') or item.find('span', class_='date')
                        pub_time = time_span.get_text(strip=True) if time_span else ''
                        
                        # 根据标题判断学历要求
                        degree = '不限'
                        if any(kw in title for kw in ['博士', '博士后', 'PhD', 'Ph.D']):
                            degree = '博士'
                        elif any(kw in title for kw in ['硕士', '研究生', 'Master', '硕士及以上']):
                            degree = '硕士'
                        elif any(kw in title for kw in ['本科', '学士', 'Bachelor', '本科及以上']):
                            degree = '本科'
                        
                        # 提取公司名称
                        company = ''
                        company_span = item.find('span', class_='company') or item.find('span', class_='unit')
                        if company_span:
                            company = company_span.get_text(strip=True)
                        
                        # 提取专业要求
                        major = ''
                        major_span = item.find('span', class_='major') or item.find('span', class_='specialty')
                        if major_span:
                            major = major_span.get_text(strip=True)
                        
                        job_info = {
                            'title': title,
                            'url': url,
                            'company': company,
                            'degree': degree,
                            'major': major,
                            'source': '南开大学就业指导中心',
                            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'pub_time': pub_time
                        }
                        
                        all_jobs[degree].append(job_info)
                        page_count += 1
                        total_count += 1
                        
                    except Exception as e:
                        continue
                
                print(f"第 {page} 页共抓取 {page_count} 条信息")
                
            else:
                print(f"第 {page} 页未找到招聘信息列表，尝试直接查找所有链接...")
                # 直接查找所有链接
                all_links = soup.find_all('a', href=True)
                page_count = 0
                for link in all_links:
                    try:
                        title = link.get('title') or link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        # 过滤：只保留包含招聘关键词的链接
                        if title and len(title) > 5 and '招聘' in title:
                            if href and not href.startswith('http'):
                                href = BASE_URL + href
                            
                            degree = '不限'
                            if any(kw in title for kw in ['博士', '博士后']):
                                degree = '博士'
                            elif any(kw in title for kw in ['硕士', '研究生']):
                                degree = '硕士'
                            elif any(kw in title for kw in ['本科', '学士']):
                                degree = '本科'
                            
                            job_info = {
                                'title': title,
                                'url': href,
                                'company': '',
                                'degree': degree,
                                'major': '',
                                'source': '南开大学就业指导中心',
                                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'pub_time': ''
                            }
                            
                            all_jobs[degree].append(job_info)
                            page_count += 1
                            total_count += 1
                    except:
                        continue
                
                print(f"第 {page} 页共抓取 {page_count} 条信息")
            
            # 每页之间等待1秒，避免请求过快
            time.sleep(1)
            
        except Exception as e:
            print(f"抓取第 {page} 页时出错: {e}")
            continue
    
    print(f"\n抓取完成！共获取 {total_count} 条招聘信息")
    return all_jobs

def save_jobs_to_json(jobs_data):
    """
    保存招聘信息到JSON文件
    """
    # 确保数据目录存在
    os.makedirs('.', exist_ok=True)
    
    # 保存到jobs.json
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 jobs.json")
    
    # 统计信息
    total = sum(len(v) for v in jobs_data.values())
    print(f"总计 {total} 条招聘信息")
    for degree, jobs in jobs_data.items():
        print(f"  {degree}: {len(jobs)} 条")

def main():
    print("=" * 50)
    print("南开大学招聘信息抓取工具（全部50页）")
    print("=" * 50)
    
    # 抓取数据
    jobs_data = fetch_jobs_from_nankai()
    
    # 保存数据
    save_jobs_to_json(jobs_data)
    
    print("\n完成！")

if __name__ == "__main__":
    main()
