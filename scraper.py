import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import re
import hashlib

class NankaiJobScraper:
    def __init__(self):
        self.base_url = "https://career.nankai.edu.cn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.jobs_file = 'jobs.json'
        
    def scrape_jobs(self):
        """爬取所有招聘信息"""
        print(f"[{datetime.now()}] 开始爬取招聘信息...")
        all_jobs = []
        
        try:
            # 爬取多个分类
            categories = [
                {'name': '校园招聘', 'url': '/recruitment/list?type=1'},
                {'name': '实习招聘', 'url': '/recruitment/list?type=2'},
                {'name': '宣讲会', 'url': '/recruitment/list?type=3'}
            ]
            
            for category in categories:
                print(f"正在爬取：{category['name']}")
                jobs = self.scrape_category(category)
                all_jobs.extend(jobs)
                print(f"  {category['name']}：获取 {len(jobs)} 条")
            
            # 去重
            all_jobs = self.deduplicate(all_jobs)
            
            # 排序
            all_jobs.sort(key=lambda x: x.get('pub_time', ''), reverse=True)
            
            print(f"总计获取 {len(all_jobs)} 条招聘信息")
            return all_jobs
            
        except Exception as e:
            print(f"爬取失败：{str(e)}")
            return []
    
    def scrape_category(self, category):
        """爬取单个分类的招聘信息"""
        jobs = []
        url = f"{self.base_url}{category['url']}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 解析招聘列表（根据实际页面结构调整）
                job_items = soup.select('.job-list .item') or soup.select('.list-item') or soup.select('tr')
                
                for item in job_items:
                    try:
                        job = self.parse_job_item(item, category['name'])
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        print(f"  解析条目失败：{str(e)}")
                        continue
                        
        except Exception as e:
            print(f"  爬取分类失败：{str(e)}")
            
        return jobs
    
    def parse_job_item(self, item, category_name):
        """解析单个招聘条目"""
        job = {
            'id': '',
            'title': '',
            'company': '',
            'category': category_name,
            'location': '',
            'degree': '',
            'major': '',
            'salary': '',
            'pub_time': '',
            'deadline': '',
            'url': '',
            'description': '',
            'requirements': '',
            'contact': '',
            'source': '南开大学就业信息网'
        }
        
        # 提取标题
        title_elem = item.select_one('.title a') or item.select_one('a[title]') or item.select_one('a')
        if title_elem:
            job['title'] = title_elem.text.strip()
            job['url'] = self.base_url + title_elem['href'] if title_elem.get('href') else ''
        
        # 提取公司
        company_elem = item.select_one('.company') or item.select_one('.unit') or item.select_one('.org')
        if company_elem:
            job['company'] = company_elem.text.strip()
        
        # 提取地点
        location_elem = item.select_one('.location') or item.select_one('.place') or item.select_one('.city')
        if location_elem:
            job['location'] = location_elem.text.strip()
        
        # 提取学历要求
        degree_elem = item.select_one('.degree') or item.select_one('.education') or item.select_one('.edu')
        if degree_elem:
            job['degree'] = degree_elem.text.strip()
        
        # 提取专业要求
        major_elem = item.select_one('.major') or item.select_one('.profession')
        if major_elem:
            job['major'] = major_elem.text.strip()
        
        # 提取薪资
        salary_elem = item.select_one('.salary') or item.select_one('.pay') or item.select_one('.money')
        if salary_elem:
            job['salary'] = salary_elem.text.strip()
        
        # 提取发布时间
        time_elem = item.select_one('.time') or item.select_one('.date') or item.select_one('.pub-date')
        if time_elem:
            job['pub_time'] = time_elem.text.strip()
        
        # 提取截止日期
        deadline_elem = item.select_one('.deadline') or item.select_one('.end-date')
        if deadline_elem:
            job['deadline'] = deadline_elem.text.strip()
        
        # 提取描述
        desc_elem = item.select_one('.description') or item.select_one('.desc') or item.select_one('.summary')
        if desc_elem:
            job['description'] = desc_elem.text.strip()[:500]  # 限制长度
        
        # 生成唯一ID
        job['id'] = hashlib.md5(f"{job['title']}{job['company']}{job['url']}".encode()).hexdigest()[:12]
        
        return job
    
    def deduplicate(self, jobs):
        """去重处理"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            key = (job['title'], job['company'], job['url'])
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def save_jobs(self, jobs):
        """保存招聘信息"""
        try:
            # 读取现有数据
            existing_jobs = []
            if os.path.exists(self.jobs_file):
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    existing_jobs = json.load(f)
            
            # 合并新旧数据
            existing_ids = {job.get('id') for job in existing_jobs}
            new_jobs = [job for job in jobs if job.get('id') not in existing_ids]
            
            all_jobs = existing_jobs + new_jobs
            
            # 限制数据量（保留最近1000条）
            if len(all_jobs) > 1000:
                all_jobs = all_jobs[:1000]
            
            # 保存文件
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            
            # 保存更新时间
            update_info = {
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_jobs': len(all_jobs),
                'new_jobs': len(new_jobs)
            }
            
            with open('update_info.json', 'w', encoding='utf-8') as f:
                json.dump(update_info, f, ensure_ascii=False, indent=2)
            
            print(f"保存成功！共 {len(all_jobs)} 条招聘信息，本次新增 {len(new_jobs)} 条")
            return True
            
        except Exception as e:
            print(f"保存失败：{str(e)}")
            return False

def main():
    scraper = NankaiJobScraper()
    jobs = scraper.scrape_jobs()
    
    if jobs:
        scraper.save_jobs(jobs)
        print("✅ 更新完成！")
    else:
        print("❌ 未获取到数据，保留原有数据")

if __name__ == '__main__':
    main()
