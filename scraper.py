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
        job_items = soup.find_all('a', href=re.compile(r'/correcruit/content/id/\d+\.html'))
        
        for job in job_items:
            title = job.get_text(strip=True)
            link = urljoin(self.base_url, job.get('href'))
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
            content_div = soup.find('div', class_='content') or soup.find('div', class_='article') or soup.find('body')
            
            if content_div:
                # 获取原始文本，保留更多信息
                text = content_div.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                # 打印前几行用于调试（可选）
                # print(f"调试信息 - 前10行文本：")
                # for i, line in enumerate(lines[:10]):
                #     print(f"  {i}: {line}")
                
                # 直接使用正则表达式提取关键信息
                full_text = '\n'.join(lines)
                
                # 1. 提取工作地域
                location_patterns = [
                    r'工作地域[：:]\s*(.+?)(?:\n|$)',
                    r'工作地点[：:]\s*(.+?)(?:\n|$)',
                    r'工作地区[：:]\s*(.+?)(?:\n|$)'
                ]
                for pattern in location_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        job_info['work_location'] = match.group(1).strip()
                        break
                
                # 2. 提取学历要求
                education_patterns = [
                    r'学历要求[：:]\s*(.+?)(?:\n|$)',
                    r'学历[：:]\s*(.+?)(?:\n|$)',
                    r'学位要求[：:]\s*(.+?)(?:\n|$)'
                ]
                for pattern in education_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        job_info['education_requirement'] = match.group(1).strip()
                        break
                
                # 3. 提取职位类别
                category_patterns = [
                    r'职位类别[：:]\s*(.+?)(?:\n|$)',
                    r'岗位类别[：:]\s*(.+?)(?:\n|$)',
                    r'工作类型[：:]\s*(.+?)(?:\n|$)'
                ]
                for pattern in category_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        job_info['job_category'] = match.group(1).strip()
                        break
                
                # 4. 提取发布时间
                time_patterns = [
                    r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2})',
                    r'发布日期[：:]\s*(\d{4}-\d{2}-\d{2})',
                    r'(\d{4}-\d{2}-\d{2})'
                ]
                for pattern in time_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        job_info['publish_time'] = match.group(1).strip()
                        break
                
                # 5. 提取专业要求
                major_patterns = [
                    r'专业要求[：:]\s*(.+?)(?:\n|$)',
                    r'专业[：:]\s*(.+?)(?:\n|$)'
                ]
                for pattern in major_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        major_text = match.group(1).strip()
                        # 如果专业要求内容很短，可能内容在下一行
                        if len(major_text) < 5 and match.end() < len(full_text):
                            next_line_match = re.search(r'\n(.+?)(?:\n|$)', full_text[match.end():])
                            if next_line_match:
                                major_text = next_line_match.group(1).strip()
                        job_info['major_requirement'] = major_text
                        break
                
                # 6. 提取薪资（包含"元"的数字）
                salary_patterns = [
                    r'(\d+-\d+元)',
                    r'(\d+元)',
                    r'薪资[：:]\s*(.+?)(?:\n|$)',
                    r'薪酬[：:]\s*(.+?)(?:\n|$)'
                ]
                for pattern in salary_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        job_info['salary'] = match.group(1).strip()
                        break
                
                # 7. 提取公司名称
                # 方法1：从标题中提取
                company_match = re.match(r'^(.+?)(?:\s*\d{4}\s*校园招聘|\s*招聘|\s*校园|\s*202[0-9])', title)
                if company_match:
                    job_info['company_name'] = company_match.group(1).strip()
                
                # 方法2：从文本中查找（通常在薪资后面）
                if not job_info['company_name']:
                    for i, line in enumerate(lines):
                        if re.search(r'\d+.*元', line) and i + 1 < len(lines):
                            # 薪资行的下一行可能是公司名称
                            next_line = lines[i + 1]
                            if not any(keyword in next_line for keyword in ['工作地域', '工作地点', '职位类别', '学历要求', '招聘人数', '发布时间', '浏览量', '专业要求', 'http', 'www']):
                                if len(next_line) > 3 and len(next_line) < 100:
                                    job_info['company_name'] = next_line.strip()
                                    break
            
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
                    print(f"    专业：{job_info['major_requirement'][:30] if job_info['major_requirement'] else '无'}...")
                
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
        total = len(self.jobs)
        with_location = sum(1 for job in self.jobs if job['work_location'])
        with_education = sum(1 for job in self.jobs if job['education_requirement'])
        with_salary = sum(1 for job in self.jobs if job['salary'])
        with_company = sum(1 for job in self.jobs if job['company_name'])
        
        print(f"\n提取统计：")
        print(f"  工作地域：{with_location}/{total}")
        print(f"  学历要求：{with_education}/{total}")
        print(f"  薪资：{with_salary}/{total}")
        print(f"  公司名称：{with_company}/{total}")

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
