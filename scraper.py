import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime

class NankaiCareerSpider:
    def __init__(self):
        self.base_url = "https://career.nankai.edu.cn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.jobs = []
    
    def get_page_content(self, url):
        """获取页面内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"请求异常: {e}")
            return None
    
    def parse_list_page(self, html_content):
        """解析列表页面，提取招聘信息的基本信息和链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        job_list = []
        
        # 查找招聘信息列表
        # 根据常见的页面结构，招聘信息通常在特定的列表容器中
        job_items = soup.find_all('li') or soup.find_all('div', class_=re.compile(r'item|list|job'))
        
        for item in job_items:
            try:
                # 查找链接
                link_tag = item.find('a', href=re.compile(r'/correcruit/content/id/\d+\.html'))
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    link = link_tag.get('href')
                    if link and not link.startswith('http'):
                        link = self.base_url + link
                    
                    # 查找公司名称和其他信息
                    company = ""
                    company_tag = item.find('span', class_=re.compile(r'company|corp|enterprise')) or \
                                 item.find('div', class_=re.compile(r'company|corp|enterprise'))
                    if company_tag:
                        company = company_tag.get_text(strip=True)
                    
                    # 查找发布时间
                    publish_time = ""
                    time_tag = item.find('span', class_=re.compile(r'time|date')) or \
                               item.find('div', class_=re.compile(r'time|date'))
                    if time_tag:
                        publish_time = time_tag.get_text(strip=True)
                    
                    if title and link:
                        job_list.append({
                            'title': title,
                            'link': link,
                            'company': company,
                            'publish_time': publish_time
                        })
            except Exception as e:
                print(f"解析列表项时出错: {e}")
                continue
        
        return job_list
    
    def parse_detail_page(self, html_content, url):
        """解析详情页面，提取详细的招聘信息"""
        soup = BeautifulSoup(html_content, 'html.parser')
        job_detail = {
            'link': url,
            'title': '',
            'company': '',
            'education_requirement': '',
            'major_requirement': '',
            'salary': '',
            'work_location': '',
            'job_category': '',
            'publish_time': ''
        }
        
        try:
            # 提取标题
            title_tag = soup.find('h1') or soup.find('h2') or soup.find('title')
            if title_tag:
                job_detail['title'] = title_tag.get_text(strip=True)
            
            # 提取所有文本内容进行分析
            all_text = soup.get_text()
            
            # 提取公司名称
            company_patterns = [
                r'公司名称[：:]\s*([^\n]+)',
                r'单位名称[：:]\s*([^\n]+)',
                r'企业名称[：:]\s*([^\n]+)',
                r'招聘单位[：:]\s*([^\n]+)'
            ]
            for pattern in company_patterns:
                match = re.search(pattern, all_text)
                if match:
                    job_detail['company'] = match.group(1).strip()
                    break
            
            # 提取学历要求
            education_patterns = [
                r'学历要求[：:]\s*([^\n]+)',
                r'学历[：:]\s*([^\n]+)',
                r'学历层次[：:]\s*([^\n]+)'
            ]
            for pattern in education_patterns:
                match = re.search(pattern, all_text)
                if match:
                    job_detail['education_requirement'] = match.group(1).strip()
                    break
            
            # 提取专业要求
            major_patterns = [
                r'专业要求[：:]\s*([^\n]+)',
                r'专业[：:]\s*([^\n]+)',
                r'所需专业[：:]\s*([^\n]+)'
            ]
            for pattern in major_patterns:
                match = re.search(pattern, all_text)
                if match:
                    job_detail['major_requirement'] = match.group(1).strip()
                    break
            
            # 提取薪资待遇
            salary_patterns = [
                r'薪资待遇[：:]\s*([^\n]+)',
                r'薪资[：:]\s*([^\n]+)',
                r'薪酬[：:]\s*([^\n]+)',
                r'工资[：:]\s*([^\n]+)'
            ]
            for pattern in salary_patterns:
                match = re.search(pattern, all_text)
                if match:
                    job_detail['salary'] = match.group(1).strip()
                    break
            
            # 提取工作地区
            location_patterns = [
                r'工作地区[：:]\s*([^\n]+)',
                r'工作地点[：:]\s*([^\n]+)',
                r'工作地址[：:]\s*([^\n]+)',
                r'所在地区[：:]\s*([^\n]+)'
            ]
            for pattern in location_patterns:
                match = re.search(pattern, all_text)
                if match:
                    job_detail['work_location'] = match.group(1).strip()
                    break
            
            # 提取岗位类别
            category_patterns = [
                r'岗位类别[：:]\s*([^\n]+)',
                r'岗位类型[：:]\s*([^\n]+)',
                r'职位类别[：:]\s*([^\n]+)',
                r'招聘岗位[：:]\s*([^\n]+)'
            ]
            for pattern in category_patterns:
                match = re.search(pattern, all_text)
                if match:
                    job_detail['job_category'] = match.group(1).strip()
                    break
            
            # 提取发布时间
            time_patterns = [
                r'发布时间[：:]\s*([^\n]+)',
                r'发布日期[：:]\s*([^\n]+)',
                r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2})'
            ]
            for pattern in time_patterns:
                match = re.search(pattern, all_text)
                if match:
                    job_detail['publish_time'] = match.group(1).strip()
                    break
            
        except Exception as e:
            print(f"解析详情页面时出错: {e}")
        
        return job_detail
    
    def crawl(self, max_pages=2):
        """爬取招聘信息"""
        print(f"开始爬取前{max_pages}页的招聘信息...")
        
        for page in range(1, max_pages + 1):
            if page == 1:
                list_url = f"{self.base_url}/correcruit/index.html"
            else:
                list_url = f"{self.base_url}/correcruit/index/p/{page}.html"
            
            print(f"正在爬取第{page}页: {list_url}")
            
            # 获取列表页面
            list_html = self.get_page_content(list_url)
            if not list_html:
                print(f"无法获取第{page}页的内容")
                continue
            
            # 解析列表页面
            job_list = self.parse_list_page(list_html)
            print(f"第{page}页找到{len(job_list)}个招聘信息")
            
            # 爬取每个招聘信息的详情
            for i, job in enumerate(job_list):
                print(f"正在爬取第{page}页第{i+1}个招聘信息: {job['title']}")
                
                # 获取详情页面
                detail_html = self.get_page_content(job['link'])
                if detail_html:
                    # 解析详情页面
                    job_detail = self.parse_detail_page(detail_html, job['link'])
                    
                    # 如果列表页有基本信息，而详情页没有，则使用列表页的信息
                    if not job_detail['title']:
                        job_detail['title'] = job['title']
                    if not job_detail['company']:
                        job_detail['company'] = job['company']
                    if not job_detail['publish_time']:
                        job_detail['publish_time'] = job['publish_time']
                    
                    self.jobs.append(job_detail)
                    print(f"成功爬取: {job_detail['title']}")
                
                # 添加延迟，避免请求过于频繁
                time.sleep(1)
            
            # 页面间延迟
            time.sleep(2)
        
        print(f"爬取完成，共获取{len(self.jobs)}个招聘信息")
    
    def save_to_json(self, filename='jobs.json'):
        """保存结果到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")

def main():
    spider = NankaiCareerSpider()
    spider.crawl(max_pages=2)  # 只爬取前2页
    spider.save_to_json('jobs.json')

if __name__ == "__main__":
    main()
