import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin

class NKUCareerSpider:
    def __init__(self):
        self.base_url = "https://career.nankai.edu.cn"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://career.nankai.edu.cn/'
        }
        self.all_jobs = []
        
    def get_list_page(self, page_num):
        """
        获取列表页的招聘信息链接
        """
        url = f"https://career.nankai.edu.cn/correcruit/index/p/{page_num}.html"
        print(f"\n正在爬取第{page_num}页: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            job_links = []
            
            # 查找招聘信息列表 - 根据实际页面结构调整
            # 常见的列表结构
            selectors = [
                ('div', 'newslist'),  # 新闻列表
                ('ul', 'list'),       # 无序列表
                ('div', 'list'),      # 列表容器
                ('table', 'table'),   # 表格
            ]
            
            for tag, class_name in selectors:
                container = soup.find(tag, class_=class_name)
                if container:
                    links = container.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        title = link.get_text(strip=True)
                        
                        # 过滤有效的招聘链接
                        if href and title and len(title) > 5:
                            if '/correcruit/' in href or '/content/' in href or 'correcruit' in href:
                                full_url = urljoin(self.base_url, href)
                                if full_url not in [j['url'] for j in job_links]:
                                    job_links.append({
                                        'title': title,
                                        'url': full_url,
                                        'page': page_num
                                    })
            
            # 如果上面的方法没找到，尝试查找所有可能的链接
            if not job_links:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    if href and title and len(title) > 10:
                        # 查找包含招聘相关关键词的链接
                        if any(keyword in href for keyword in ['correcruit', 'content', 'detail', 'show']):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in [j['url'] for j in job_links]:
                                job_links.append({
                                    'title': title,
                                    'url': full_url,
                                    'page': page_num
                                })
            
            print(f"第{page_num}页找到 {len(job_links)} 个招聘信息")
            
            # 打印前几个链接用于调试
            if job_links:
                print("示例链接:")
                for i, job in enumerate(job_links[:3]):
                    print(f"  {i+1}. {job['title'][:30]}... -> {job['url']}")
            
            return job_links
            
        except Exception as e:
            print(f"获取第{page_num}页失败: {e}")
            return []
    
    def extract_detail_info(self, url, title):
        """
        提取详情页的完整信息
        """
        print(f"  正在提取: {title[:40]}...")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            info = {
                'title': title,
                'url': url,
                'company_name': '',
                'job_title': '',
                'education_requirement': '',
                'major_requirement': '',
                'salary': '',
                'work_location': '',
                'job_category': '',
                'job_description': '',
                'publish_date': '',
                'view_count': '',
                'contact_info': '',
                'application_deadline': ''
            }
            
            # 1. 提取公司名称
            company_selectors = [
                ('div', 'company'),
                ('span', 'company'),
                ('h1', 'company'),
                ('div', 'company_name'),
            ]
            for tag, class_name in company_selectors:
                company_elem = soup.find(tag, class_=class_name)
                if company_elem:
                    info['company_name'] = company_elem.get_text(strip=True)
                    break
            
            # 如果没找到，尝试从标题中提取
            if not info['company_name'] and '招聘' in title:
                company_name = title.split('招聘')[0].strip()
                if company_name:
                    info['company_name'] = company_name
            
            # 2. 提取职位名称
            title_selectors = [
                ('div', 'title1'),
                ('h1', 'title'),
                ('div', 'job_title'),
                ('h2', 'title'),
            ]
            for tag, class_name in title_selectors:
                title_elem = soup.find(tag, class_=class_name)
                if title_elem:
                    info['job_title'] = title_elem.get_text(strip=True)
                    break
            
            # 3. 提取发布时间和浏览量
            date_selectors = [
                ('div', 'date'),
                ('span', 'time'),
                ('div', 'info'),
                ('p', 'date'),
            ]
            for tag, class_name in date_selectors:
                date_elem = soup.find(tag, class_=class_name)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    
                    # 提取发布时间
                    date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', date_text)
                    if date_match:
                        info['publish_date'] = date_match.group(1)
                    
                    # 提取浏览量
                    view_match = re.search(r'浏览[量数][：:]\s*(\d+)', date_text)
                    if view_match:
                        info['view_count'] = view_match.group(1)
                    break
            
            # 4. 提取主要内容区域
            content_selectors = [
                ('div', 'zpnr'),
                ('div', 'content'),
                ('div', 'article'),
                ('div', 'detail'),
                ('div', 'main'),
            ]
            
            content_div = None
            for tag, class_name in content_selectors:
                content_div = soup.find(tag, class_=class_name)
                if content_div:
                    break
            
            if content_div:
                full_text = content_div.get_text(separator='\n', strip=True)
                
                # 提取学历要求
                edu_patterns = [
                    r'学历[要求]*[：:]\s*([^。；\n]+)',
                    r'学历[要求]*\s*[：:]\s*([^。；\n]+)',
                    r'学历[：:]\s*([^。；\n]+)',
                ]
                for pattern in edu_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        info['education_requirement'] = match.group(1).strip()
                        break
                
                # 提取专业要求
                major_patterns = [
                    r'专业[要求]*[：:]\s*([^。；\n]+)',
                    r'专业[要求]*\s*[：:]\s*([^。；\n]+)',
                    r'专业[：:]\s*([^。；\n]+)',
                ]
                for pattern in major_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        info['major_requirement'] = match.group(1).strip()
                        break
                
                # 提取薪资信息
                salary_patterns = [
                    r'薪酬[：:]\s*([^。；\n]+)',
                    r'薪资[：:]\s*([^。；\n]+)',
                    r'薪[资酬][：:]\s*([^。；\n]+)',
                    r'工资[：:]\s*([^。；\n]+)',
                ]
                for pattern in salary_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        salary_text = match.group(1).strip()
                        info['salary'] = salary_text.split('；')[0].split('。')[0]
                        break
                
                # 提取工作地点
                location_patterns = [
                    r'工作地点[：:]\s*([^。；\n]+)',
                    r'工作地区[：:]\s*([^。；\n]+)',
                    r'工作城市[：:]\s*([^。；\n]+)',
                    r'地点[：:]\s*([^。；\n]+)',
                ]
                for pattern in location_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        info['work_location'] = match.group(1).strip()
                        break
                
                # 提取联系方式
                contact_patterns = [
                    r'联系[方式人][：:]\s*([^。；\n]+)',
                    r'电话[：:]\s*([^。；\n]+)',
                    r'邮箱[：:]\s*([^。；\n]+)',
                ]
                for pattern in contact_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        info['contact_info'] = match.group(1).strip()
                        break
                
                # 提取截止日期
                deadline_patterns = [
                    r'截止[日期时间][：:]\s*([^。；\n]+)',
                    r'报名截止[：:]\s*([^。；\n]+)',
                ]
                for pattern in deadline_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        info['application_deadline'] = match.group(1).strip()
                        break
                
                # 职位描述（取前2000字符）
                info['job_description'] = full_text[:2000]
            
            # 5. 提取职位类别
            category_patterns = [
                r'职位类别[：:]\s*([^。；\n]+)',
                r'岗位类别[：:]\s*([^。；\n]+)',
            ]
            for pattern in category_patterns:
                match = re.search(pattern, soup.get_text())
                if match:
                    info['job_category'] = match.group(1).strip()
                    break
            
            return info
            
        except Exception as e:
            print(f"  提取详情失败: {e}")
            return {
                'title': title,
                'url': url,
                'error': str(e)
            }
    
    def crawl_pages(self, num_pages=2):
        """
        爬取指定页数的招聘信息
        """
        print(f"开始爬取前{num_pages}页的招聘信息...")
        print("=" * 60)
        
        for page in range(1, num_pages + 1):
            # 获取列表页的链接
            job_links = self.get_list_page(page)
            
            if not job_links:
                print(f"第{page}页没有找到招聘信息")
                continue
            
            # 逐个提取详情页信息
            for i, job in enumerate(job_links, 1):
                print(f"\n[{page}-{i}/{len(job_links)}] ", end="")
                detail_info = self.extract_detail_info(job['url'], job['title'])
                self.all_jobs.append(detail_info)
                
                # 礼貌性延迟，避免请求过快
                time.sleep(1.5)
            
            print(f"\n第{page}页爬取完成")
            time.sleep(2)  # 页面间延迟
        
        print("\n" + "=" * 60)
        print(f"爬取完成！共获取 {len(self.all_jobs)} 条招聘信息")
        
        return self.all_jobs
    
    def save_results(self, filename='nku_jobs.json'):
        """
        保存结果到JSON文件
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_jobs, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到 {filename}")
    
    def print_summary(self):
        """
        打印爬取结果摘要
        """
        print("\n" + "=" * 60)
        print("爬取结果摘要")
        print("=" * 60)
        
        for i, job in enumerate(self.all_jobs, 1):
            print(f"\n{i}. {job.get('job_title', job.get('title', 'N/A'))}")
            print(f"   公司: {job.get('company_name', 'N/A')}")
            print(f"   学历: {job.get('education_requirement', 'N/A')}")
            print(f"   专业: {job.get('major_requirement', 'N/A')[:50]}...")
            print(f"   薪资: {job.get('salary', 'N/A')}")
            print(f"   地点: {job.get('work_location', 'N/A')}")
            print(f"   类别: {job.get('job_category', 'N/A')}")
            print(f"   发布时间: {job.get('publish_date', 'N/A')}")
            print(f"   截止日期: {job.get('application_deadline', 'N/A')}")
            print(f"   链接: {job.get('url', 'N/A')}")

# 运行爬虫
if __name__ == "__main__":
    spider = NKUCareerSpider()
    
    # 爬取前2页
    jobs = spider.crawl_pages(num_pages=2)
    
    # 保存结果
    spider.save_results('nku_jobs.json')
    
    # 打印摘要
    spider.print_summary()
