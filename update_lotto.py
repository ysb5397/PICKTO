import csv
import requests

CSV_FILE = 'data/lotto645.csv'

def get_latest_drw_no():
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            valid_rows = [row for row in reader if row] 
            
            if len(valid_rows) > 1:
                last_row = valid_rows[-1]
                latest_no_str = last_row[0].replace(',', '').strip()
                return int(latest_no_str)
    except FileNotFoundError:
        pass
    except ValueError as e:
        print(f"회차 변환 오류: {e}")
    return 0

def fetch_lotto_data(drw_no):
    target_int = int(drw_no)
    url = f"https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do?srchLtEpsd={target_int}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://dhlottery.co.kr",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        session = requests.Session()
        session.get("https://dhlottery.co.kr", headers=headers, timeout=5)
        
        response = session.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            res_json = response.json()
            lotto_list = res_json.get("data", {}).get("list", [])
            
            # API 응답 리스트에서 일치하는 회차 탐색
            for item in lotto_list:
                item_epsd = item.get("ltEpsd")
                if item_epsd is not None and int(item_epsd) == target_int:
                    return [
                        int(item.get("ltEpsd")),
                        int(item.get("tm1WnNo")),
                        int(item.get("tm2WnNo")),
                        int(item.get("tm3WnNo")),
                        int(item.get("tm4WnNo")),
                        int(item.get("tm5WnNo")),
                        int(item.get("tm6WnNo")),
                        int(item.get("bnsWnNo"))
                    ]
            
            fetched_epsds = [x.get("ltEpsd") for x in lotto_list]
            print(f"ℹ️ [디버그] {target_int}회차를 찾지 못했습니다. (서버 응답 회차 목록: {fetched_epsds})")

    except Exception as e:
        print(f"❌ [디버그] API 호출 실패: {e}")

    return None

def main():
    latest_no = get_latest_drw_no()
    if latest_no == 0:
        print("CSV 파일을 찾을 수 없거나 데이터가 없습니다.")
        return

    target_no = latest_no + 1
    new_data = fetch_lotto_data(target_no)
    
    if new_data:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(new_data)
        print(f"✅ {target_no}회차 자동 업데이트 완료")
    else:
        print(f"ℹ️ {target_no}회차 데이터가 아직 없음. (추첨 전이거나 API 지연)")

if __name__ == "__main__":
    main()
