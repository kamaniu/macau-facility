import requests
import json

iam_url = "https://iam.apigateway.data.gov.mo/facility_drink"
dspa_url = "https://dspa.apigateway.data.gov.mo/T_Bas_POI_Basic/drinkingFountain"

# 【強化】補上標準瀏覽器 User-Agent 偽裝，防止被政府防火牆直接阻擋
headers = {
    "Authorization": "APPCODE 09d43a591fba407fb862412970667de4",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

print("🔄 正在從政府網關安全下載飲水設施數據...")

combined_data = []

# 1. 抓取市政署資料
try:
    iam_res = requests.get(iam_url, headers=headers, timeout=15)
    print(f"📡 市政署響應狀態碼: {iam_res.status_code}")
    
    # 打印前200字檢查是否有拿到真實內容
    print(f"📄 市政署原始回應片段: {iam_res.text[:200]}")
    
    iam_json = iam_res.json()
    # 兼容多種包裹結構：直接是陣列、在 data 裡、或在首層鍵名中
    if isinstance(iam_json, list):
        iam_items = iam_json
    elif isinstance(iam_json, dict):
        iam_items = iam_json.get('data', iam_json.get('Data', iam_json.get('features', None)))
        if iam_items is None:
            # 如果還是找不到，把字典裡所有是陣列的值抓出來嘗試
            iam_items = next((v for v in iam_json.values() if isinstance(v, list)), iam_json)
    else:
        iam_items = []

    if isinstance(iam_items, list) and len(iam_items) > 0:
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
    else:
        print("⚠️ 市政署未提取到有效的陣列資料")
except Exception as e:
    print(f"❌ 市政署數據抓取失敗: {e}")

# 2. 抓取環保局資料
try:
    dspa_res = requests.get(dspa_url, headers=headers, timeout=15)
    print(f"📡 環保局響應狀態碼: {dspa_res.status_code}")
    print(f"📄 環保局原始回應片段: {dspa_res.text[:200]}")
    
    dspa_json = dspa_res.json()
    if isinstance(dspa_json, list):
        dspa_items = dspa_json
    elif isinstance(dspa_json, dict):
        dspa_items = dspa_json.get('data', dspa_json.get('Data', dspa_json.get('records', None)))
        if dspa_items is None:
            dspa_items = next((v for v in dspa_json.values() if isinstance(v, list)), dspa_json)
    else:
        dspa_items = []

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
        print(f"✅ 成功解析環保局數據，目前總計累計: {len(combined_data)} 筆")
except Exception as e:
    print(f"❌ 環保局數據抓取失敗: {e}")

# 儲存為合法的 JSON 檔案
with open("water_data.json", "w", encoding="utf-8") as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=4)

print(f"🎉 任務結束！共合併儲存 {len(combined_data)} 筆資料至 water_data.json")
