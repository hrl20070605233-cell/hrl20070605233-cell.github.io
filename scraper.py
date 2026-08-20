import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def fetch_nankai_jobs():
    """抓取南开大学就业指导中心招聘信息"""
    url = "https://career.nankai.edu.cn/"  # 这是南开就业中心官网
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 注意：这里需要根据实际页面结构调整选择器
        # 我们先打印出页面标题看看是否抓取成功
        print(f"页面标题: {soup.title.text}")
        
        # 先返回一个测试数据，看看能不能跑通
        jobs = [
            {
                "title": "测试岗位 - 南开大学就业信息",
                "company": "测试公司",
                "degree": "本科",
                "major": "计算机",
                "url": "https://career.nankai.edu.cn",
                "source": "南开大学就业指导中心",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
        
        return jobs
        
    except Exception as e:
        print(f"抓取出错: {e}")
        return []

def save_jobs(jobs):
    """保存为JSON文件"""
    data = {
        "博士": [j for j in jobs if j['degree'] == '博士'],
        "硕士": [j for j in jobs if j['degree'] == '硕士'],
        "本科": [j for j in jobs if j['degree'] == '本科'],
        "不限": [j for j in jobs if j['degree'] == '不限']
    }
    
    with open('jobs.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("数据已保存到 jobs.json")

if __name__ == "__main__":
    print("开始抓取南开大学就业信息...")
    jobs = fetch_nankai_jobs()
    save_jobs(jobs)
    print(f"抓取完成，共 {len(jobs)} 条数据")
