import requests
import json

iam_url = "https://iam.apigateway.data.gov.mo/facility_drink"
dspa_url = "https://dspa.apigateway.data.gov.mo/T_Bas_POI_Basic/drinkingFountain"

headers = {
    "Authorization": "APPCODE 09d43a591fba407fb862412970667de4",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

print("🔄 正在從政府網關安全下載飲水設施數據（含相片欄位）...")

combined_data = []

def find_list_in_json(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ['records', 'data', 'Data', 'results', 'features', 'list']:
            if key in data and isinstance(data[key], list):
                return data[key]
        for val in data.values():
            res = find_list_in_json(val)
            if res is not None:
                return res
    return None

# 1. 抓取市政署資料 (GET)
try:
    iam_res = requests.get(iam_url, headers=headers, timeout=15)
    iam_json = iam_res.json()
    iam_items = find_list_in_json(iam_json)

    if iam_items:
        for item in iam_items:
            loc = item.get('location', '')
            if loc and ',' in loc:
                lat, lng = loc.split(',')
                combined_data.append({
                    "type": "iam",
                    "name": item.get('nameZh', '市政署飲水機'),
                    "address": item.get('addressZh', ''),
                    "openHour": item.get('openHourZh', ''),
                    "photo": item.get('photo', ''),  # 【新增】抓取照片網址
                    "lat": float(lat),
                    "lng": float(lng)
                })
        print(f"✅ 成功解析動態市政署數據（含相片），目前累計: {len(combined_data)} 筆")
except Exception as e:
    print(f"❌ 市政署數據抓取失敗: {e}")

# 2. 抓取環保局資料 (POST)
try:
    dspa_res = requests.post(dspa_url, headers=headers, timeout=15)
    dspa_json = dspa_res.json()
    dspa_items = find_list_in_json(dspa_json)

    if dspa_items:
        dspa_count = 0
        for item in dspa_items:
            if item.get('latitude') and item.get('longitude'):
                combined_data.append({
                    "type": "dspa",
                    "name": item.get('name_tc', '環保局飲水設施'),
                    "address": item.get('address_tc', ''),
                    "openHour": "依場地開放時間為準",
                    "photo": "",  # 環保局若無提供相片則留空
                    "lat": float(item['latitude']),
                    "lng": float(item['longitude'])
                })
                dspa_count += 1
        print(f"✅ 成功透過 POST 接口解析環境保護局最新數據，新增: {dspa_count} 筆")
except Exception as e:
    print(f"❌ 環保局動態數據抓取或解析失敗: {e}")

# 儲存為合法的 JSON 檔案
with open("water_data.json", "w", encoding="utf-8") as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=4)

print(f"🎉 任務結束！最終成功合併儲存 {len(combined_data)} 筆實時資料至 water_data.json")
