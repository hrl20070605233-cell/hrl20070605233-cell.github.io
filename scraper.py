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
        
        # 查找招聘信息列表 - 根据实际页面结构调整选择器
        job_items = soup.find_all('a', href=re.compile(r'/correcruit/content/id/\d+\.html'))
        
        for job in job_items:
            title = job.get_text(strip=True)
            link = urljoin(self.base_url, job.get('href'))
            # 过滤掉空标题或无效链接
            if title and link and 'content/id/' in link:
                links.append({
                    'title': title,
                    'link': link
                })
        
        # 去重
        seen = set()
        unique_links = []
        for item in links:
            if item['link'] not in seen:
                seen.add(item['link'])
                unique_links.append(item)
        
        return unique_links
    
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
        """解析详情页，根据实际文本结构提取信息"""
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
            # 获取页面的纯文本内容
            # 先找到主要内容区域
            content_div = soup.find('div', class_='content') or soup.find('div', class_='article') or soup.find('body')
            
            if content_div:
                # 获取所有文本行
                text = content_div.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                # 根据你提供的文本结构解析
                for i, line in enumerate(lines):
                    # 1. 查找薪资（包含"元"的数字）
                    if re.search(r'\d+.*元', line) and not job_info['salary']:
                        job_info['salary'] = line.strip()
                    
                    # 2. 查找公司名称（通常在薪资后面，且不包含特殊关键词）
                    elif (job_info['salary'] and not job_info['company_name'] and 
                          '工作地域' not in line and '职位类别' not in line and 
                          '学历要求' not in line and '招聘人数' not in line and
                          '发布时间' not in line and '浏览量' not in line and
                          '专业要求' not in line and '职位投递' not in line and
                          'http' not in line and not re.search(r'\d+.*元', line)):
                        # 这可能是公司名称
                        if len(line) > 2 and len(line) < 100:  # 合理的公司名称长度
                            job_info['company_name'] = line.strip()
                    
                    # 3. 查找工作地域
                    if '工作地域' in line:
                        location = line.replace('工作地域：', '').replace('工作地域:', '').strip()
                        job_info['work_location'] = location
                    
                    # 4. 查找职位类别
                    if '职位类别' in line:
                        category = line.replace('职位类别：', '').replace('职位类别:', '').strip()
                        job_info['job_category'] = category
                    
                    # 5. 查找学历要求
                    if '学历要求' in line:
                        education = line.replace('学历要求：', '').replace('学历要求:', '').strip()
                        job_info['education_requirement'] = education
                    
                    # 6. 查找发布时间
                    if '发布时间' in line:
                        time_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
                        if time_match:
                            job_info['publish_time'] = time_match.group()
                    
                    # 7. 查找专业要求（可能在下一行）
                    if '专业要求' in line:
                        # 专业要求可能在当前行或下一行
                        major_text = line.replace('专业要求：', '').replace('专业要求:', '').replace('*', '').strip()
                        if major_text:
                            job_info['major_requirement'] = major_text
                        elif i + 1 < len(lines):
                            # 检查下一行是否是专业要求内容
                            next_line = lines[i + 1]
                            if not any(keyword in next_line for keyword in ['工作地域', '职位类别', '学历要求', '招聘人数', '发布时间', '浏览量']):
                                job_info['major_requirement'] = next_line.strip()
                
                # 如果还没找到公司名称，尝试从标题中提取
                if not job_info['company_name']:
                    # 标题格式通常是：公司名称 + 招聘信息
                    company_match = re.match(r'^(.+?)(?:\s*\d{4}\s*校园招聘|\s*招聘|\s*校园)', title)
                    if company_match:
                        job_info['company_name'] = company_match.group(1).strip()
            
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
                print(f"  正在爬取第{i}个：{job['title'][:50]}...")
                
                detail_html = self.get_detail_page(job['link'])
                if detail_html:
                    job_info = self.parse_detail_page(detail_html, job['title'], job['link'])
                    self.jobs.append(job_info)
                    
                    # 显示提取结果
                    print(f"    公司：{job_info['company_name']}")
                    print(f"    薪资：{job_info['salary']}")
                    print(f"    地点：{job_info['work_location']}")
                    print(f"    学历：{job_info['education_requirement']}")
                
                # 添加延时，避免请求过快
                time.sleep(1.5)
            
            # 页面间延时
            time.sleep(2)
        
        print(f"\n爬取完成！共获取{len(self.jobs)}条招聘信息")
    
    def save_to_json(self, filename='jobs.json'):
        """保存到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到{filename}")
        
        # 显示统计信息
        filled_jobs = sum(1 for job in self.jobs if job['company_name'] and job['salary'])
        print(f"成功提取完整信息的职位：{filled_jobs}/{len(self.jobs)}")

# 运行爬虫
if __name__ == "__main__":
    spider = NankaiCareerSpider()
    spider.crawl_pages(1, 3)  # 爬取前3页
    spider.save_to_json('jobs.json')
    
    # 显示爬取结果摘要
    print("\n爬取结果摘要（前5条）：")
    for i, job in enumerate(spider.jobs[:5], 1):
        print(f"\n{i}. {job['title']}")
        print(f"   公司：{job['company_name']}")
        print(f"   薪资：{job['salary']}")
        print(f"   地点：{job['work_location']}")
        print(f"   学历：{job['education_requirement']}")
        print(f"   专业：{job['major_requirement'][:50] if job['major_requirement'] else '无'}")
        print(f"   类别：{job['job_category']}")
        print(f"   时间：{job['publish_time']}")
