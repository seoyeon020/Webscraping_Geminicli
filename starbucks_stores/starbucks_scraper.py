
import requests
import pandas as pd
from loguru import logger

logger.add("starbucks_stores/starbucks_scraper.log", rotation="500 MB")

def get_starbucks_stores():
    url = "https://www.starbucks.co.kr/store/getStore.do"
    headers = {
        "host": "www.starbucks.co.kr",
        "origin": "https://www.starbucks.co.kr",
        "referer": "https://www.starbucks.co.kr/store/store_map.do",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    
    all_stores = []
    
    for sido_code in range(1, 18):
        sido_code_str = str(sido_code).zfill(2)
        payload = {
            "in_biz_cds": "0",
            "in_scodes": "0",
            "ins_lat": "37.38330327376894",
            "ins_lng": "126.94937539775802",
            "search_text": "",
            "p_sido_cd": sido_code_str,
            "p_gugun_cd": "",
            "isError": "true",
            "in_distance": "0",
            "in_biz_cd": "",
            "iend": "1000",
            "searchType": "C",
            "set_date": "",
            "rndCod": "ED6F8Y3PHZ",
            "todayPop": "0",
            "all_store": "0",
            "T03": "0",
            "T01": "0",
            "T27": "0",
            "T12": "0",
            "T09": "0",
            "T30": "0",
            "T05": "0",
            "T22": "0",
            "T21": "0",
            "T36": "0",
            "T43": "0",
            "Z9999": "0",
            "T64": "0",
            "T66": "0",
            "P02": "0",
            "P10": "0",
            "P50": "0",
            "P20": "0",
            "P60": "0",
            "P30": "0",
            "P70": "0",
            "P40": "0",
            "P80": "0",
            "whcroad_yn": "0",
            "P90": "0",
            "P01": "0",
            "new_bool": "0",
        }
        
        logger.info(f"Requesting stores for sido_code: {sido_code_str}")
        response = requests.post(url, data=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            stores = data.get("list", [])
            if stores:
                logger.info(f"Found {len(stores)} stores for sido_code: {sido_code_str}")
                all_stores.extend(stores)
            else:
                logger.warning(f"No stores found for sido_code: {sido_code_str}")
        else:
            logger.error(f"Failed to fetch data for sido_code: {sido_code_str}, Status code: {response.status_code}")
            
    return all_stores

if __name__ == "__main__":
    all_stores = get_starbucks_stores()
    if all_stores:
        df = pd.DataFrame(all_stores)
        output_path = "starbucks_stores/data/starbucks_stores.csv"
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"Successfully saved {len(df)} stores to {output_path}")
    else:
        logger.warning("No stores were scraped.")
