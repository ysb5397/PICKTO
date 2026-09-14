import csv
import requests

CSV_FILE = 'data/lotto645.csv'

def get_latest_drw_no():
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            # 단순 split 대신 csv.reader를 써서 "1,239" 같은 따옴표 안의 콤마도 안전하게 처리
            reader = list(csv.reader(f))
            # 빈 줄을 제외하고 유효한 데이터가 있는 마지막 줄 찾기
            valid_rows = [row for row in reader if row] 
            
            if len(valid_rows) > 1:
                last_row = valid_rows[-1]
                # 첫 번째 열(회차)에서 콤마와 띄어쓰기를 완전히 제거 후 정수로 변환
                latest_no_str = last_row[0].replace(',', '').strip()
                return int(latest_no_str)
    except FileNotFoundError:
        pass
    except ValueError as e:
        print(f"회차 변환 오류: {e}")
    return 0

def fetch_lotto_data(drw_no):
    url = f"https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do?srchLtEpsd={drw_no}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            res_json = response.json()
            lotto_list = res_json.get("data", {}).get("list", [])
            
            # 리스트 중에서 찾는 회차(target_no)와 일치하는 데이터 탐색
            for item in lotto_list:
                if item.get("ltEpsd") == target_no:
                    # 기존 코드와 완벽히 동일하게 8개 항목 리스트로 조립하여 리턴
                    return [
                        item.get("ltEpsd"),    # 회차
                        item.get("tm1WnNo"),   # 번호1
                        item.get("tm2WnNo"),   # 번호2
                        item.get("tm3WnNo"),   # 번호3
                        item.get("tm4WnNo"),   # 번호4
                        item.get("tm5WnNo"),   # 번호5
                        item.get("tm6WnNo"),   # 번호6
                        item.get("bnsWnNo")    # 보너스 번호
                    ]
                    
    except Exception as e:
        print(f"❌ API 요청 중 오류 발생: {e}")
        
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
        print(f"✅ {target_no}회차 자동 업데이트 완료!")
    else:
        print(f"ℹ️ {target_no}회차 데이터가 아직 없습니다. (추첨 전이거나 API 지연)")

if __name__ == "__main__":
    main()
