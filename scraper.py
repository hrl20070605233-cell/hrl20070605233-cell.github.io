import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin

class NankaiCareerSpider:
    def __init__(self):
        self.base_url = "https://career.nankai.edu.cn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.jobs = []
    
    def get_list_page(self, page_num):
        """获取列表页"""
        url = f"https://career.nankai.edu.cn/correcruit/index/p/{page_num}.html"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
            else:
                print(f"获取第{page_num}页失败，状态码：{response.status_code}")
                return None
        except Exception as e:
            print(f"请求第{page_num}页出错：{e}")
            return None
    
    def parse_list_page(self, html):
        """解析列表页，获取所有招聘信息链接"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # 查找招聘信息列表
        job_list = soup.find_all('a', href=re.compile(r'/correcruit/content/id/\d+\.html'))
        
        for job in job_list:
            title = job.get_text(strip=True)
            link = urljoin(self.base_url, job.get('href'))
            if title and link:
                links.append({
                    'title': title,
                    'link': link
                })
        
        return links
    
    def get_detail_page(self, url):
        """获取详情页"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
            else:
                print(f"获取详情页失败：{url}，状态码：{response.status_code}")
                return None
        except Exception as e:
            print(f"请求详情页出错：{url}，错误：{e}")
            return None
    
    def parse_detail_page(self, html, title, link):
        """解析详情页，提取所需信息"""
        soup = BeautifulSoup(html, 'html.parser')
        
        job_info = {
            'title': title,
            'link': link,
            'company_name': '',
            'education_requirement': '',
            'major_requirement': '',
            'salary': '',
            'work_location': '',
            'job_category': '',
            'publish_time': ''
        }
        
        try:
            # 查找招聘信息表格
            # 通常这些信息在表格中
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).replace('：', '').replace(':', '')
                        value = cells[1].get_text(strip=True)
                        
                        if '单位名称' in key or '公司名称' in key:
                            job_info['company_name'] = value
                        elif '学历要求' in key:
                            job_info['education_requirement'] = value
                        elif '专业要求' in key:
                            job_info['major_requirement'] = value
                        elif '薪资' in key or '薪酬' in key:
                            job_info['salary'] = value
                        elif '工作地区' in key or '工作地点' in key:
                            job_info['work_location'] = value
                        elif '岗位类别' in key or '职位类别' in key:
                            job_info['job_category'] = value
                        elif '发布时间' in key or '发布日期' in key:
                            job_info['publish_time'] = value
            
            # 如果表格中没有找到，尝试其他方式
            # 查找包含这些信息的div或p标签
            if not job_info['company_name']:
                # 尝试从页面标题或其他位置获取公司名称
                company_elem = soup.find('h1') or soup.find('h2') or soup.find('h3')
                if company_elem:
                    text = company_elem.get_text(strip=True)
                    # 公司名称通常在标题中
                    if '【' in text and '】' in text:
                        company_match = re.search(r'【(.+?)】', text)
                        if company_match:
                            job_info['company_name'] = company_match.group(1)
            
            # 查找发布时间
            if not job_info['publish_time']:
                time_pattern = re.findall(r'\d{4}-\d{2}-\d{2}', html)
                if time_pattern:
                    job_info['publish_time'] = time_pattern[0]
            
        except Exception as e:
            print(f"解析详情页出错：{link}，错误：{e}")
        
        return job_info
    
    def crawl_pages(self, start_page=1, end_page=3):
        """爬取指定范围的页面"""
        print(f"开始爬取第{start_page}到第{end_page}页...")
        
        for page_num in range(start_page, end_page + 1):
            print(f"\n正在爬取第{page_num}页...")
            
            # 获取列表页
            html = self.get_list_page(page_num)
            if not html:
                continue
            
            # 解析列表页获取链接
            job_links = self.parse_list_page(html)
            print(f"第{page_num}页找到{len(job_links)}个招聘信息")
            
            # 爬取每个详情页
            for i, job in enumerate(job_links, 1):
                print(f"  正在爬取第{i}个：{job['title'][:30]}...")
                
                detail_html = self.get_detail_page(job['link'])
                if detail_html:
                    job_info = self.parse_detail_page(detail_html, job['title'], job['link'])
                    self.jobs.append(job_info)
                    print(f"    成功提取：{job_info['company_name']} - {job_info['work_location']}")
                
                # 添加延时，避免请求过快
                time.sleep(1)
            
            # 页面间延时
            time.sleep(2)
        
        print(f"\n爬取完成！共获取{len(self.jobs)}条招聘信息")
    
    def save_to_json(self, filename='jobs.json'):
        """保存到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到{filename}")

# 运行爬虫
if __name__ == "__main__":
    spider = NankaiCareerSpider()
    spider.crawl_pages(1, 3)  # 爬取前3页
    spider.save_to_json('jobs.json')
    
    # 显示爬取结果摘要
    print("\n爬取结果摘要：")
    for i, job in enumerate(spider.jobs[:5], 1):
        print(f"{i}. {job['title']}")
        print(f"   公司：{job['company_name']}")
        print(f"   地点：{job['work_location']}")
        print(f"   学历：{job['education_requirement']}")
        print(f"   薪资：{job['salary']}")
        print(f"   时间：{job['publish_time']}")
        print()
