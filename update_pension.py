import os
import csv
import requests

CSV_FILE = 'data/pension720.csv'

def check_csv_integrity():
    """
    CSV 파일의 무결성을 검사한다.
    반환값: (is_valid: bool, latest_drw: int, reason: str)
    - 파일 존재 및 내용 유무
    - 1회차부터 누락 없는 연속성
    - 각 행 포맷 (회차: int, 조: str, 번호: 6자리 str)
    """
    if not os.path.exists(CSV_FILE):
        return False, 0, "파일이 존재하지 않음"

    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            valid_rows = [row for row in reader if row]

        if not valid_rows:
            return False, 0, "파일 내용이 비어있음"

        prev_drw = 0
        for idx, row in enumerate(valid_rows):
            if len(row) < 3:
                return False, 0, f"{idx + 1}번째 행 컬럼 부족 (3개 필요, 현재 {len(row)}개)"

            # 1. 회차 검사
            drw_str = row[0].replace(',', '').strip()
            if not drw_str.isdigit():
                return False, 0, f"{idx + 1}번째 행 회차가 숫자가 아님: '{row[0]}'"
            
            drw = int(drw_str)
            
            # 첫 번째 행은 1회차여야 함
            if idx == 0 and drw != 1:
                return False, 0, f"첫 번째 행이 1회차가 아님: {drw}회차"

            # 연속적인 회차 증가 검사 (중간 누락/역전 방지)
            if idx > 0 and drw != prev_drw + 1:
                return False, 0, f"회차 불연속 감지 ({prev_drw}회 다음 {drw}회)"

            # 2. 조 검사
            jo = row[1].strip()
            if not jo:
                return False, 0, f"{drw}회차 조 데이터 누락"

            # 3. 당첨 번호 검사 (6자리 숫자)
            num = row[2].strip()
            if len(num) != 6 or not num.isdigit():
                return False, 0, f"{drw}회차 당첨번호가 6자리 숫자가 아님: '{num}'"

            prev_drw = drw

        return True, prev_drw, "정상"

    except Exception as e:
        return False, 0, f"파일 검사 중 오류: {e}"

def fetch_all_pension_data():
    """
    동행복권 API에서 연금복권 전체 당첨 데이터를 받아와 정제하여 반환한다.
    반환값: List[[회차(int), 조(str), 당첨번호(str)]] (회차 기준 오름차순 정렬)
    """
    url = "https://www.dhlottery.co.kr/pt720/selectPstPt720WnList.do"

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
            pension_list = res_json.get("data", {}).get("result", [])

            parsed_list = []
            for item in pension_list:
                item_epsd = item.get("psltEpsd")
                wn_bnd_no = item.get("wnBndNo")
                wn_rnk_vl = item.get("wnRnkVl")

                if item_epsd is not None and wn_bnd_no is not None and wn_rnk_vl is not None:
                    epsd = int(item_epsd)
                    jo = str(wn_bnd_no).strip()
                    nums = str(wn_rnk_vl).strip().zfill(6)
                    parsed_list.append([epsd, jo, nums])

            # 회차 기준 오름차순 정렬 (1회차부터 순서대로)
            parsed_list.sort(key=lambda x: x[0])
            return parsed_list

    except Exception as e:
        print(f"❌ [디버그] API 호출 실패: {e}")

    return None

def main():
    is_valid, latest_no, reason = check_csv_integrity()
    
    print(f"🔍 CSV 무결성 검사 결과: {'[정상]' if is_valid else '[이상 감지]'} ({reason}, 현재 마지막: {latest_no}회)")

    # API 데이터 전체 호출
    all_data = fetch_all_pension_data()
    if not all_data:
        print("❌ API로부터 데이터를 가져오지 못했습니다. 기존 파일을 안전하게 유지합니다.")
        return

    # 1. 파일에 문제가 없는 경우: 마지막 회차 뒤에 최신 회차만 쓱 추가 (Append)
    if is_valid:
        new_rows = [row for row in all_data if row[0] > latest_no]
        
        if not new_rows:
            print(f"ℹ️ 이미 최신 회차({latest_no}회)까지 모두 반영되어 있어 추가할 데이터가 없습니다.")
            return

        # 혹시 기존 데이터와 API 최신 데이터 사이에 갭(누락)이 있는 경우 전체 교체로 전환
        if new_rows[0][0] != latest_no + 1:
            print(f"⚠️ 기존 마지막 회차({latest_no})와 API 첫 신규 회차({new_rows[0][0]}) 사이 누락 감지 -> 전체 교체로 전환!")
            is_valid = False

        if is_valid:
            needs_newline = False
            if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
                with open(CSV_FILE, 'rb') as f:
                    f.seek(-1, os.SEEK_END)
                    if f.read(1) not in (b'\n', b'\r'):
                        needs_newline = True

            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                if needs_newline:
                    f.write('\n')
                writer = csv.writer(f)
                writer.writerows(new_rows)

            added_epsds = [str(r[0]) for r in new_rows]
            print(f"✅ 연금복권 최신 {len(new_rows)}개 회차 추가 완료! (추가된 회차: {', '.join(added_epsds)}회)")
            return

    # 2. 파일에 문제가 있는 경우 (파일 없음, 누락, 포맷 깨짐 등): 전체 교체로 자동 복구
    if not is_valid:
        # 안전장치: API 응답 개수가 너무 적으면(예: 300건 미만) 기존 파일 보호
        if len(all_data) < 300:
            print(f"⚠️ 안전 경고: API 데이터({len(all_data)}건)가 기준치(300건)에 못 미쳐 덮어쓰지 않습니다.")
            return

        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(all_data)

        print(f"🔄 CSV 자동 복구 완료: 1회차 ~ {all_data[-1][0]}회차 전체 교체 완료! (총 {len(all_data)}건)")

if __name__ == "__main__":
    main()
