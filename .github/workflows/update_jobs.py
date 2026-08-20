import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def fetch_jobs():
    """从招聘网站获取职位信息"""
    # 这里以拉勾网为例，实际使用时需要根据目标网站调整
    url = "https://www.zhipin.com/web/geek/job"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 示例职位数据（实际使用时替换为真实的爬虫逻辑）
    jobs = [
        {
            "title": "Python开发工程师",
            "company": "某科技有限公司",
            "location": "北京",
            "salary": "20K-35K",
            "description": "负责后端服务开发，参与系统架构设计",
            "date": datetime.now().strftime("%Y-%m-%d")
        },
        {
            "title": "前端开发工程师",
            "company": "某互联网公司",
            "location": "上海",
            "salary": "18K-30K",
            "description": "负责Web前端开发，优化用户体验",
            "date": datetime.now().strftime("%Y-%m-%d")
        },
        {
            "title": "数据分析师",
            "company": "某数据科技公司",
            "location": "深圳",
            "salary": "15K-25K",
            "description": "负责数据分析，提供业务决策支持",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    ]
    
    return jobs

def generate_html(jobs):
    """生成HTML页面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>招聘信息汇总</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .job-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .job-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .job-title {
            font-size: 20px;
            font-weight: bold;
            color: #1a73e8;
            margin-bottom: 10px;
        }
        .company {
            font-size: 16px;
            color: #666;
            margin-bottom: 8px;
        }
        .info {
            display: flex;
            gap: 20px;
            margin-bottom: 10px;
            color: #888;
            font-size: 14px;
        }
        .salary {
            color: #e74c3c;
            font-weight: bold;
            font-size: 18px;
        }
        .description {
            color: #555;
            line-height: 1.6;
        }
        .update-time {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <h1>📋 最新招聘信息</h1>
"""
    
    for job in jobs:
        html_content += f"""
    <div class="job-card">
        <div class="job-title">{job['title']}</div>
        <div class="company">🏢 {job['company']}</div>
        <div class="info">
            <span>📍 {job['location']}</span>
            <span>📅 {job['date']}</span>
        </div>
        <div class="salary">💰 {job['salary']}</div>
        <div class="description">{job['description']}</div>
    </div>
"""
    
    html_content += f"""
    <div class="update-time">
        最后更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    """主函数"""
    try:
        # 获取职位信息
        jobs = fetch_jobs()
        
        # 生成HTML
        html = generate_html(jobs)
        
        # 写入文件
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"成功更新 {len(jobs)} 个职位信息")
        
    except Exception as e:
        print(f"更新失败: {str(e)}")
        # 如果失败，保留原有内容
        exit(1)

if __name__ == "__main__":
    main()
