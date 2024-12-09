from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
from datetime import date
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

# 常量定义
LOGIN_URL = 'https://hyjg.stcma.cn/zyyp.php'
DATA_URL_TEMPLATE = 'https://hyjg.stcma.cn/zyyp.php?&page={page}&c=&o=&t=&n=&p=&s=&u=&d='
HEADER = ['统编代码', '饮片名', '曾用名', '炮制方法', '规格', '单位', '参考采购价信息']
FILENAME = f'stcma_data_{date.today()}.csv'


def init_driver():
    """初始化 WebDriver"""
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)  # 隐式等待，适应动态加载
    return driver


def login(driver, username, password):
    """登录页面"""
    driver.get(LOGIN_URL)
    driver.find_element(By.NAME, 'muser').send_keys(username)
    driver.find_element(By.NAME, 'mpass').send_keys(password)
    driver.find_element(By.NAME, 'Submit').click()


def get_total_pages(driver):
    """获取总页数"""
    try:
        total_count_element = driver.find_element(By.CLASS_NAME, 'pagesinfo')
        total_count_text = total_count_element.text
        total_count = int(total_count_text.split(' ')[1])
        page_count = 1 + total_count // 20
        return page_count
    except Exception as e:
        print(f"获取总页数失败: {e}")
        return 0


def scrape_page(driver, page_number):
    """抓取单页数据"""
    data = []
    url = DATA_URL_TEMPLATE.format(page=page_number)
    driver.get(url)
    
    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'tbl_query'))
        )
        rows = table.find_elements(By.TAG_NAME, 'tr')
        for row in rows[1:]:  # 跳过表头
            cells = row.find_elements(By.TAG_NAME, "td")
            cell_texts = [cell.text for cell in cells[:7]]  # 提取前7列
            if any(cell_texts):
                data.append(cell_texts)
    except Exception as e:
        print(f"抓取页面 {page_number} 数据失败: {e}")
    return data


def save_to_csv(filename, header, data):
    """将数据保存到 CSV 文件"""
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(data)
        print(f"数据已保存到 {filename}")
    except Exception as e:
        print(f"保存 CSV 文件失败: {e}")


def main():
    driver = init_driver()
    try:
        login(driver, username, password)
        total_pages = get_total_pages(driver)
        if total_pages == 0:
            print("未找到有效页数，终止程序。")
            return
        
        print(f"共 {total_pages} 页数据，开始抓取...")
        all_data = []
        
        for page in range(1, total_pages + 1):
            print(f"正在抓取第 {page}/{total_pages} 页...")
            page_data = scrape_page(driver, page)
            all_data.extend(page_data)
            time.sleep(1)  # 防止被反爬，适当延时
        
        save_to_csv(FILENAME, HEADER, all_data)
    
    finally:
        driver.quit()
        print("爬虫任务完成！")


if __name__ == "__main__":
    main()
