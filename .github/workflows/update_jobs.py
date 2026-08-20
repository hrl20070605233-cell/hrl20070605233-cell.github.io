name: 更新招聘数据

on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

permissions:
  contents: write  # 添加这一行，赋予写入权限

jobs:
  update:
    runs-on: ubuntu-latest
    
    steps:
      - name: 检出代码
        uses: actions/checkout@v3  # 升级到v3
      
      - name: 设置Python
        uses: actions/setup-python@v4  # 升级到v4
        with:
          python-version: '3.9'
      
      - name: 安装依赖
        run: |
          pip install requests beautifulsoup4
      
      - name: 运行爬虫
        run: python scraper.py
      
      - name: 提交更新
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add jobs.json
          git diff --quiet && git diff --staged --quiet || git commit -m "自动更新招聘数据 $(date +'%Y-%m-%d %H:%M')"
          git push
