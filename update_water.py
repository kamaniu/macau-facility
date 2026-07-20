import requests
import json

iam_url = "https://iam.apigateway.data.gov.mo/facility_drink"
dspa_url = "https://dspa.apigateway.data.gov.mo/T_Bas_POI_Basic/drinkingFountain"

headers = {
    "Authorization": "APPCODE 09d43a591fba407fb862412970667de4",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

print("🔄 正在從政府網關安全下載飲水設施數據...")

combined_data = []

# 強力遞迴函數：自動挖出 JSON 裡面隱藏的清單陣列
def find_list_in_json(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # 優先找常見的關鍵字
        for key in ['records', 'data', 'Data', 'results', 'features', 'list']:
            if key in data and isinstance(data[key], list):
                return data[key]
        # 遍歷字典所有欄位深度挖掘
        for val in data.values():
            res = find_list_in_json(val)
            if res is not None:
                return res
    return None

# 1. 抓取市政署資料
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
                    "lat": float(lat),
                    "lng": float(lng)
                })
        print(f"✅ 成功解析市政署數據，目前累計: {len(combined_data)} 筆")
except Exception as e:
    print(f"❌ 市政署數據抓取失敗: {e}")

# 2. 抓取環保局資料 (進行深度挖掘)
try:
    dspa_res = requests.get(dspa_url, headers=headers, timeout=15)
    dspa_json = dspa_res.json()
    
    # 打印環保局返回的結構前 300 個字，方便你在 Actions 日誌排查
    print(f"📄 環保局原始數據包裝結構: {str(dspa_json)[:300]}")
    
    dspa_items = find_list_in_json(dspa_json)

    if dspa_items:
        dspa_count = 0
        for item in dspa_items:
            # 確保有座標欄位才能畫在地上
            if item.get('latitude') and item.get('longitude'):
                combined_data.append({
                    "type": "dspa",
                    "name": item.get('name_tc', '環保局飲水設施'),
                    "address": item.get('address_tc', ''),
                    "openHour": "",
                    "lat": float(item['latitude']),
                    "lng": float(item['longitude'])
                })
                dspa_count += 1
        print(f"✅ 成功解析環境保護局數據，新增: {dspa_count} 筆")
    else:
        print("⚠️ 環境保護局未提取到有效的陣列清單資料！")
except Exception as e:
    print(f"❌ 環保局數據抓取失敗: {e}")

# 儲存為合法的 JSON 檔案
with open("water_data.json", "w", encoding="utf-8") as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=4)

print(f"🎉 任務結束！共合併儲存 {len(combined_data)} 筆資料至 water_data.json")
