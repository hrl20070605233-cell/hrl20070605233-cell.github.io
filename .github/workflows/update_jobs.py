import json
import requests
from bs4 import BeautifulSoup
import re

def fetch_jobs():
    """从多个来源获取招聘信息"""
    jobs = []
    
    # 来源1：GitHub 官方职位（仍然可用）
    try:
        url = "https://jobs.github.com/api/v1/positions.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for job in data[:10]:  # 获取前10条
                jobs.append({
                    "title": job.get("title", "未知职位"),
                    "company": job.get("company", "未知公司"),
                    "location": job.get("location", "未知地点"),
                    "description": job.get("description", "")[:200] + "...",
                    "url": job.get("url", "#"),
                    "source": "GitHub Jobs"
                })
    except Exception as e:
        print(f"GitHub Jobs API 获取失败: {e}")
    
    # 来源2：从 Indeed 爬取（示例）
    if not jobs:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            url = "https://www.indeed.com/jobs?q=python+developer&l=remote"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 这里需要根据 Indeed 的实际HTML结构调整选择器
                # 示例：简化处理
                print("Indeed 数据获取成功，但需要解析")
        except Exception as e:
            print(f"Indeed 获取失败: {e}")
    
    # 来源3：使用示例数据（备用）
    if not jobs:
        jobs = get_sample_jobs()
    
    return jobs

def get_sample_jobs():
    """返回示例数据"""
    return [
        {
            "title": "Python 后端开发工程师",
            "company": "某知名互联网公司",
            "location": "远程/北京",
            "description": "负责后端服务开发，熟悉Python/Django/Flask，有3年以上经验...",
            "url": "https://example.com/job1",
            "source": "示例数据"
        },
        {
            "title": "全栈工程师",
            "company": "创业公司",
            "location": "上海",
            "description": "React + Python 全栈开发，熟悉前后端分离架构...",
            "url": "https://example.com/job2",
            "source": "示例数据"
        },
        {
            "title": "数据工程师",
            "company": "金融科技公司",
            "location": "深圳",
            "description": "负责数据管道开发，熟悉Python/Spark/Airflow...",
            "url": "https://example.com/job3",
            "source": "示例数据"
        }
    ]

def update_readme(jobs):
    """更新README.md"""
    if not jobs:
        return
    
    # 读取现有README
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        content = "# 招聘信息\n\n"
    
    # 生成招聘信息表格
    table = "## 最新招聘信息\n\n"
    table += "| 职位 | 公司 | 地点 | 描述 | 来源 |\n"
    table += "|------|------|------|------|------|\n"
    
    for job in jobs:
        title = job.get('title', '未知')
        company = job.get('company', '未知')
        location = job.get('location', '未知')
        desc = job.get('description', '')[:50] + '...'
        source = job.get('source', '未知')
        url = job.get('url', '#')
        
        table += f"| [{title}]({url}) | {company} | {location} | {desc} | {source} |\n"
    
    # 替换或追加表格
    if "## 最新招聘信息" in content:
        # 替换现有表格
        start = content.find("## 最新招聘信息")
        end = content.find("##", start + 1)
        if end == -1:
            end = len(content)
        content = content[:start] + table + content[end:]
    else:
        # 追加到末尾
        content += "\n\n" + table
    
    # 写入文件
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("README.md 已更新")

def main():
    print("开始更新招聘信息...")
    
    jobs = fetch_jobs()
    
    if not jobs:
        print("未获取到招聘信息，使用示例数据")
        jobs = get_sample_jobs()
    
    # 保存为JSON
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    
    # 更新README
    update_readme(jobs)
    
    print(f"成功保存 {len(jobs)} 条招聘信息")

if __name__ == "__main__":
    main()
