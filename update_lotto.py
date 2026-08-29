import csv
import requests
from datetime import datetime

CSV_FILE = 'lotto.csv'

def get_latest_drw_no():
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > 1:
                # 마지막 줄의 첫 번째 값(회차)을 가져옴
                return int(lines[-1].split(',')[0])
    except FileNotFoundError:
        pass
    return 0 # 파일이 없거나 헤더만 있으면 0 반환 (이후 1회차부터 혹은 특정 회차부터 처리 가능)

def fetch_lotto_data(drw_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    response = requests.get(url)
    data = response.json()
    
    if data['returnValue'] == 'success':
        return [
            data['drwNo'],
            data['drwNoDate'],
            data['drwtNo1'], data['drwtNo2'], data['drwtNo3'],
            data['drwtNo4'], data['drwtNo5'], data['drwtNo6'],
            data['bnusNo']
        ]
    return None

def main():
    latest_no = get_latest_drw_no()
    target_no = latest_no + 1
    
    new_data = fetch_lotto_data(target_no)
    
    if new_data:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(new_data)
        print(f"{target_no}회차 업데이트 완료!")
    else:
        print(f"{target_no}회차 데이터가 아직 없습니다.")

if __name__ == "__main__":
    main()