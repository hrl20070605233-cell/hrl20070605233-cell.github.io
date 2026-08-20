import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def fetch_jobs():
    """获取招聘信息"""
    # 这里写你的招聘信息获取逻辑
    # 示例：从某个网站爬取
    jobs = []
    
    try:
        # 示例：从 GitHub Jobs API 获取
        url = "https://jobs.github.com/positions.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"成功获取 {len(jobs)} 条招聘信息")
        else:
            print(f"请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"获取招聘信息失败: {e}")
    
    return jobs

def save_jobs(jobs):
    """保存招聘信息到文件"""
    if not jobs:
        print("没有招聘信息需要保存")
        return False
    
    # 保存为 JSON 文件
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    
    # 更新 README.md（可选）
    update_readme(jobs)
    
    print(f"成功保存 {len(jobs)} 条招聘信息")
    return True

def update_readme(jobs):
    """更新 README.md 文件"""
    readme_path = 'README.md'
    
    # 生成招聘信息表格
    table = "| 职位 | 公司 | 地点 | 发布时间 |\n|------|------|------|----------|\n"
    
    for job in jobs[:10]:  # 只显示前10条
        title = job.get('title', '未知')
        company = job.get('company', '未知')
        location = job.get('location', '未知')
        created_at = job.get('created_at', '未知')[:10]
        
        table += f"| {title} | {company} | {location} | {created_at} |\n"
    
    # 读取现有 README
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "# 招聘信息\n\n"
    
    # 更新招聘信息部分
    if "## 最新招聘信息" in content:
        # 替换现有内容
        start = content.find("## 最新招聘信息")
        end = content.find("## ", start + 1) if content.find("## ", start + 1) != -1 else len(content)
        content = content[:start] + f"## 最新招聘信息\n\n{table}\n" + content[end:]
    else:
        content += f"\n## 最新招聘信息\n\n{table}\n"
    
    # 写入文件
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("README.md 已更新")

if __name__ == "__main__":
    print("开始更新招聘信息...")
    jobs = fetch_jobs()
    if jobs:
        save_jobs(jobs)
    else:
        print("未获取到招聘信息，使用示例数据")
        # 使用示例数据
        sample_jobs = [
            {
                "title": "Python 开发工程师",
                "company": "示例公司",
                "location": "北京",
                "created_at": datetime.now().isoformat()
            }
        ]
        save_jobs(sample_jobs)
