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
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    response = requests.get(url)
    data = response.json()
    
    # 추첨일(drwNoDate)을 빼고 정확히 8개 항목만 리턴!
    if data['returnValue'] == 'success':
        return [
            data['drwNo'],
            data['drwtNo1'], data['drwtNo2'], data['drwtNo3'],
            data['drwtNo4'], data['drwtNo5'], data['drwtNo6'],
            data['bnusNo']
        ]
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
