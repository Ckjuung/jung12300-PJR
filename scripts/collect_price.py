# scripts/collect_price.py
import requests, xmltodict, pandas as pd
from datetime import datetime
import os

# ✅ 인증키는 GitHub Actions 환경변수(API_KEY)에서 가져옴
SERVICE_KEY = os.environ.get("API_KEY")
LAWD_CD = "11200"  # 성동구
APT_NAME = "텐즈힐"
DEAL_YM = datetime.today().strftime("%Y%m")

def fetch_items(deal_type="매매"):
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev" \
          if deal_type == "매매" else \
          "http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"

    params = {"serviceKey": SERVICE_KEY, "LAWD_CD": LAWD_CD, "DEAL_YMD": DEAL_YM}
    res = requests.get(url, params=params)
    data = xmltodict.parse(res.content)
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if not isinstance(items, list):
        items = [items]
    return [i for i in items if APT_NAME in i.get("aptNm", "")]

sales = fetch_items("매매")
rents = fetch_items("전세")

def avg_price(data, key):
    return pd.DataFrame(data)[key].str.replace(",", "").astype(int).mean() if data else 0

sale_avg = avg_price(sales, "dealAmount")
rent_avg = avg_price(rents, "rentFee")
ratio = (rent_avg / sale_avg * 100) if sale_avg else 0

result = pd.DataFrame([{
    "date": DEAL_YM,
    "매매가": int(sale_avg),
    "전세가": int(rent_avg),
    "전세가율(%)": round(ratio, 1)
}])

result.to_csv("data/output.csv", index=False)

# 📄 마크다운 보고서 생성
markdown = f"""# 전세가율 분석 보고서

- 단지명: **{APT_NAME}**
- 지역코드: **{LAWD_CD} (성동구)**
- 기준월: **{DEAL_YM}**
- 매매가 평균: **{sale_avg:,.0f}만원**
- 전세가 평균: **{rent_avg:,.0f}만원**
- 전세가율: **{ratio:.1f}%**
"""

with open("data/report.md", "w", encoding="utf-8") as f:
    f.write(markdown)

print("✅ 분석 완료 및 report.md 저장")
