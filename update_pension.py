import csv
import requests
from bs4 import BeautifulSoup
import time

CSV_FILE = 'data/pension720.csv'

def get_latest_drw_no():
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            valid_rows = [row for row in reader if row]
            if len(valid_rows) > 1:
                return int(valid_rows[-1][0].replace(',', '').strip())
    except Exception as e:
        pass
    return 0

def fetch_pension_data(target_no, max_retries=3):
    url = "https://www.dhlottery.co.kr/pt720/result"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 페이지 내에서 현재 렌더링된 회차 번호 추출 (옵션 클래스 찾기)
            current_drw_element = soup.select_one('#drwNo option[selected]')
            if current_drw_element:
                current_drw = int(current_drw_element.text.replace('회', '').strip())
                
                # 갱신이 안 됐으면 재시도
                if current_drw < target_no:
                    delay = 2 ** attempt # 1초, 2초, 4초 대기...
                    print(f"⚠️ 아직 {target_no}회차가 업데이트되지 않았습니다. {delay}초 후 재시도...")
                    time.sleep(delay)
                    continue
            
            # 정상적으로 타겟 회차 이상이 렌더링 되었다면 번호 추출 시작
            win_area = soup.select_one('.wf720-num-list')
            if win_area:
                jo = win_area.select_one('.pension-jo').text.strip()
                nums = "".join([win_area.select_one(f'.wf-{i}n').text.strip() for i in range(1, 7)])
                
                if jo and len(nums) == 6:
                    return [target_no, jo, nums]
                    
        except Exception as e:
            print(f"파싱 에러: {e}")
            time.sleep(2 ** attempt)
            
    return None

def main():
    latest_no = get_latest_drw_no()
    target_no = latest_no + 1
    
    new_data = fetch_pension_data(target_no)
    
    if new_data:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(new_data)
        print(f"✅ 연금복권 {target_no}회차 무적 업데이트 완료!")
    else:
        print(f"❌ {target_no}회차 데이터를 가져오지 못했습니다. 추첨 지연이거나 구조 변경을 확인하세요.")

if __name__ == "__main__":
    main()