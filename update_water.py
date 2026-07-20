import requests
import json

iam_url = "https://iam.apigateway.data.gov.mo/facility_drink"
dspa_url = "https://dspa.apigateway.data.gov.mo/T_Bas_POI_Basic/drinkingFountain"
headers = {"Authorization": "APPCODE 09d43a591fba407fb862412970667de4"}

print("🔄 正在從政府網關下載飲水設施數據...")

combined_data = []

# 1. 抓取市政署資料
try:
    iam_res = requests.get(iam_url, headers=headers, timeout=15)
    iam_json = iam_res.json()
    # 確保抓到陣列（兼容不同的包裝結構）
    iam_items = iam_json.get('data', iam_json.get('Data', iam_json))
    if isinstance(iam_items, list):
        for item in iam_items:
            loc = item.get('location', '')
            if loc and ',' in loc:
                lat, lng = loc.split(',')
                combined_data.append({
                    "type": "iam",
                    "name": item.get('nameZh', '市政署飲水機'),
                    "address": item.get('addressZh', ''),
                    "openHour": item.get('openHourZh', ''),
                    "lat": float(lat),
                    "lng": float(lng)
                })
        print(f"✅ 成功解析市政署數據，共 {len(iam_items)} 筆")
except Exception as e:
    print(f"❌ 市政署數據抓取失敗: {e}")

# 2. 抓取環保局資料
try:
    dspa_res = requests.get(dspa_url, headers=headers, timeout=15)
    dspa_json = dspa_res.json()
    dspa_items = dspa_json.get('data', dspa_json.get('Data', dspa_json))
    if isinstance(dspa_items, list):
        for item in dspa_items:
            if item.get('latitude') and item.get('longitude'):
                combined_data.append({
                    "type": "dspa",
                    "name": item.get('name_tc', '環保局飲水設施'),
                    "address": item.get('address_tc', ''),
                    "openHour": "",
                    "lat": float(item['latitude']),
                    "lng": float(item['longitude'])
                })
        print(f"✅ 成功解析環保局數據")
except Exception as e:
    print(f"❌ 環保局數據抓取失敗: {e}")

# 儲存為合法的 JSON 檔案
with open("water_data.json", "w", encoding="utf-8") as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=4)

print("🎉 所有數據已成功合併並儲存為 water_data.json")