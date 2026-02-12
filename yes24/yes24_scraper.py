import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from loguru import logger

# --- 로거 설정 ---
# 기본 로거를 제거하고 특정 포맷으로 새로운 로거를 추가합니다.
logger.remove()
logger.add(
    "yes24/yes24_scraper.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    rotation="10 MB",
    encoding="utf-8"
)

# --- 상수 설정 ---
# 데이터 디렉토리가 없으면 생성합니다.
DATA_DIR = "yes24/data"
os.makedirs(DATA_DIR, exist_ok=True)
CSV_FILE_PATH = os.path.join(DATA_DIR, "yes24_ai.csv")

# 명세서에서 제공된 URL 및 헤더 정보
BASE_URL = "https://www.yes24.com/product/category/CategoryProductContents"
HEADERS = {
    'host': 'www.yes24.com',
    'referer': 'https://www.yes24.com/product/category/display/001001003032',
    'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest'
}

def fetch_book_data(page: int, size: int = 24) -> list[dict]:
    """
    Yes24의 특정 카테고리 페이지에서 도서 데이터를 가져옵니다.

    Args:
        page (int): 가져올 페이지 번호.
        size (int): 페이지 당 아이템 수.

    Returns:
        list[dict]: 각 도서를 나타내는 딕셔너리의 리스트.
    """
    params = {
        'dispNo': '001001003032',
        'order': 'SINDEX_ONLY',
        'addOptionTp': '0',
        'page': page,
        'size': size,
        'statGbYn': 'N',
        'viewMode': '',
        '_options': '',
        'directDelvYn': '',
        'usedTp': '0',
        'elemNo': '0',
        'elemSeq': '0',
        'seriesNumber': '0'
    }

    scraped_books = []

    try:
        logger.info(f"{page} 페이지의 데이터를 가져오는 중...")
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()  # 잘못된 응답(4xx 또는 5xx)에 대해 HTTPError를 발생시킵니다.
        logger.success(f"{page} 페이지 데이터를 성공적으로 가져왔습니다. 상태 코드: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        item_units = soup.find_all('div', class_='itemUnit')
        logger.info(f"{page} 페이지에서 {len(item_units)}개의 아이템을 찾았습니다.")

        for item in item_units:
            # 엘리먼트에서 텍스트를 안전하게 가져오는 헬퍼 함수
            def get_text(element, selector):
                target = element.select_one(selector)
                return target.get_text(strip=True) if target else None

            # 엘리먼트에서 속성을 안전하게 가져오는 헬퍼 함수
            def get_attribute(element, selector, attribute):
                target = element.select_one(selector)
                return target.get(attribute) if target else None

            # --- 데이터 추출 ---
            title = get_text(item, 'a.gd_name')
            subtitle = get_text(item, 'span.gd_nameE')
            author = get_text(item, '.info_auth a')
            publisher = get_text(item, '.info_pub a')
            pub_date = get_text(item, '.info_date')
            
            # 가격
            original_price_elem = item.select_one('.txt_num.dash .yes_m')
            original_price = original_price_elem.text.replace(',', '') if original_price_elem else None

            discounted_price_elem = item.select_one('.txt_num .yes_b')
            discounted_price = discounted_price_elem.text.replace(',', '') if discounted_price_elem else None
            
            # 판매 지수
            sales_index_elem = item.select_one('.saleNum')
            sales_index = int(sales_index_elem.text.replace('판매지수', '').replace(',', '').strip()) if sales_index_elem else None

            # 평점 및 리뷰 수
            rating = get_text(item, '.rating_grade em.yes_b')
            review_count_elem = item.select_one('.rating_rvCount .txC_blue')
            review_count = int(review_count_elem.text.strip('()')) if review_count_elem else 0

            # 태그
            tags = [tag.get_text(strip=True) for tag in item.select('.info_tag .tag a')]
            
            # 이미지 URL
            image_url = get_attribute(item, '.lazy', 'data-original')

            # 상세 페이지 URL
            detail_path = get_attribute(item, 'a.gd_name', 'href')
            detail_url = f"https://www.yes24.com{detail_path}" if detail_path else None

            scraped_books.append({
                'Title': title,
                'Subtitle': subtitle,
                'Author': author,
                'Publisher': publisher,
                'Publication Date': pub_date,
                'Original Price': original_price,
                'Discounted Price': discounted_price,
                'Sales Index': sales_index,
                'Rating': rating,
                'Review Count': review_count,
                'Tags': ', '.join(tags), # 태그를 하나의 문자열로 합칩니다.
                'Image URL': image_url,
                'URL': detail_url
            })
        
        logger.info(f"{page} 페이지에서 {len(scraped_books)}권의 도서 정보를 성공적으로 파싱했습니다.")

    except requests.exceptions.RequestException as e:
        logger.error(f"{page} 페이지에 대한 HTTP 요청 실패: {e}")
    except Exception as e:
        logger.critical(f"스크래핑 중 예상치 못한 오류 발생 ({page} 페이지): {e}")
        
    return scraped_books

def main():
    """스크래핑 과정을 제어하는 메인 함수입니다."""
    logger.info("Yes24 스크래퍼 작업을 시작합니다.")
    
    # 예시로 1페이지부터 5페이지까지 스크래핑합니다.
    all_books = []
    num_pages_to_scrape = 5 
    
    for i in range(1, num_pages_to_scrape + 1):
        books_on_page = fetch_book_data(page=i)
        if not books_on_page:
            logger.warning(f"{i} 페이지에서 데이터를 반환하지 않아 스크래핑을 중단합니다.")
            break
        all_books.extend(books_on_page)

    if not all_books:
        logger.error("스크랩된 도서가 없습니다. 출력 파일을 생성하지 않습니다.")
        return

    # DataFrame으로 변환
    df = pd.DataFrame(all_books)
    logger.info(f"총 스크랩된 도서 수: {len(df)}")
    
    # --- 데이터 정제 (간단) ---
    df['Original Price'] = pd.to_numeric(df['Original Price'], errors='coerce')
    df['Discounted Price'] = pd.to_numeric(df['Discounted Price'], errors='coerce')
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    
    # CSV로 저장
    try:
        df.to_csv(CSV_FILE_PATH, index=False, encoding='utf-8-sig')
        logger.success(f"{CSV_FILE_PATH}에 {len(df)}개의 레코드를 성공적으로 저장했습니다.")
    except Exception as e:
        logger.error(f"CSV 파일 저장 실패: {e}")

if __name__ == "__main__":
    main()
