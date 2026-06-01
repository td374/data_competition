# -*- coding: utf-8 -*-
import os
import time
import requests
import re
from pathlib import Path

class CninfoFetcher:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://www.cninfo.com.cn/'
    }

    def __init__(self, root_dir="巨潮年报或ESG_2019-2021"):
        self.root_dir = Path(root_dir)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _search_annual_report(self, stock_code, year):
        url = "http://www.cninfo.com.cn/new/fulltextSearch/full"
        params = {
            'searchkey': f"{stock_code} {year} 年年度报告",
            'isfulltext': 'false',
            'sortName': 'pubdate',
            'sortType': 'desc',
            'pageNum': 1
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            for ann in data.get("announcements", []):
                title = ann.get("announcementTitle", "")
                title = re.sub(r"<.*?>", "", title)
                if "年度报告" in title and "摘要" not in title and "英文" not in title:
                    adj_url = ann.get("adjunctUrl")
                    if adj_url:
                        return f"http://static.cninfo.com.cn/{adj_url}"
        except Exception as e:
            print(f"搜索失败 {stock_code} {year}: {e}")
        return None

    def download_pdf(self, url, save_path):
        if save_path.exists():
            print(f"✅ 已存在，跳过: {save_path.name}")
            return True
        try:
            resp = self.session.get(url, stream=True, timeout=30)
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            print(f"✅ 下载成功: {save_path}")
            return True
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return False

    def run(self, company_list, years):
        for industry, groups in company_list.items():
            industry_dir = self.root_dir / industry
            industry_dir.mkdir(parents=True, exist_ok=True)

            for group_name, stocks in groups.items():
                group_dir = industry_dir / group_name
                group_dir.mkdir(exist_ok=True)

                for code, fullname, shortname in stocks:
                    stock_dir = group_dir / f"{code}_{shortname}"
                    stock_dir.mkdir(exist_ok=True)

                    for y in years:
                        print(f"\n正在处理 → {industry} | {group_name} | {code} {shortname} {y}年报")
                        url = self._search_annual_report(code, y)
                        if not url:
                            print(f"❌ 未找到 {y} 年报")
                            time.sleep(1)
                            continue

                        filename = f"{code}_{shortname}_{y}_年度报告.pdf"
                        save_path = stock_dir / filename
                        self.download_pdf(url, save_path)
                        time.sleep(1.2)
                    time.sleep(2)

        print("\n🎉 全部企业年报下载完成！")

if __name__ == '__main__':

    # ===================== 你的企业名单（自动分行业+分组）=====================
    COMPANY_LIST = {
        "航空": {
            "绿色": [
                ("601111", "中国国际航空股份有限公司", "中国国航"),
                ("600029", "中国南方航空股份有限公司", "南方航空"),
            ],
            "争议": [
                ("600115", "中国东方航空股份有限公司", "东方航空"),
                ("601021", "春秋航空股份有限公司", "春秋航空"),
            ],
            "棕色": [
                ("600897", "厦门国际航空港股份有限公司", "厦门空港"),
                ("600004", "广州白云国际机场股份有限公司", "白云机场"),
            ],
            "独立测试集": [
                ("600221", "海南航空控股股份有限公司", "海南航空"),
            ],
            "标杆": [
                ("600009", "上海国际机场股份有限公司", "上海机场"),
            ]
        },
        "发电": {
            "绿色": [
                ("600011", "华能国际电力股份有限公司", "华能国际"),
                ("600900", "中国长江电力股份有限公司", "长江电力"),
                ("600886", "国投电力控股股份有限公司", "国投电力"),
            ],
            "争议": [
                ("600795", "国电电力发展股份有限公司", "国电电力"),
                ("601991", "大唐国际发电股份有限公司", "大唐发电"),
            ],
            "棕色": [
                ("600578", "北京京能电力股份有限公司", "京能电力"),
                ("600726", "华电能源股份有限公司", "华电能源"),
            ],
            "独立测试集": [
                ("600157", "永泰能源股份有限公司", "永泰能源"),
                ("600509", "新疆天富能源股份有限公司", "天富能源"),
            ],
            "标杆": [
                ("600023", "浙江浙能电力股份有限公司", "浙能电力"),
                ("600025", "华能澜沧江水电股份有限公司", "华能水电"),
            ]
        }
    }

    # 下载年份
    YEARS = [2019, 2020, 2021]

    # 启动
    fetcher = CninfoFetcher()
    fetcher.run(COMPANY_LIST, YEARS)