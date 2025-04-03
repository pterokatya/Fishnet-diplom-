from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re
import os
import django
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fishnet_backend.settings')
django.setup()

from subscriber.models import Subscriber

def normalize_address(raw_address):
    address = raw_address.lower()
    address = address.replace("мкр", "").replace("микрорайон", "").replace("дом", "").replace("кв", "")
    address = re.sub(r"[^\d, а-яёa-z/]", "", address)
    parts = [p.strip() for p in address.split(",") if p.strip()]

    if len(parts) >= 3 and parts[-1].isdigit():
        return f"{parts[0]}, {parts[1]}", parts[2]
    else:
        return ", ".join(parts), None

def open_user_profile(driver, address, apartment=None):
    search_input = driver.find_element(By.ID, "top_field")
    search_input.clear()
    search_input.send_keys(address)
    time.sleep(2.5)

    if address.strip().isdigit():
        suggestions = driver.find_elements(By.XPATH, "//div[@id='top_find_result']//a")
        for suggestion in suggestions:
            if address in suggestion.text:
                driver.execute_script("arguments[0].click();", suggestion)
                time.sleep(3)
                return
        print("❗ Договор не найден в подсказках.")
        return

    if apartment:
        suggestions = driver.find_elements(By.XPATH, "//div[@id='top_find_result']//a")
        for suggestion in suggestions:
            href = suggestion.get_attribute("href")
            suggestion_text = suggestion.text.strip().lower()
            address_parts = address.lower().split()
            if "address_building" in href and all(part in suggestion_text for part in address_parts):
                driver.execute_script("arguments[0].click();", suggestion)
                time.sleep(4)
                break

        rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'table_item')]")
        for row in rows:
            try:
                apt_cell = row.find_element(By.XPATH, ".//td[3]/a")
                if apt_cell.text.strip() == str(apartment):
                    apt_cell.click()
                    time.sleep(3)
                    break
            except:
                continue

    else:
        search_input.send_keys(Keys.RETURN)
        time.sleep(4)
        try:
            link = driver.find_element(By.ID, "linkTable-1Id")
            link.click()
            time.sleep(3)
        except:
            print("❗ Не удалось найти строку абонента для частного сектора")

def parse_and_save_subscriber_data(driver, norm_address):
    # ОБЩИЕ
    fio_block = driver.find_element(By.XPATH, "//div[@class='left_data' and contains(text(), 'ФИО:')]/following-sibling::div")
    username = fio_block.text.strip()

    tariff = driver.find_element(By.ID, "tariffName0Id").text.strip()

    balance = driver.find_element(By.ID, "spanBalanceCurrentId").text.strip()

    phone_block = driver.find_element(By.XPATH, "//div[contains(text(), '+7')]")
    phone = phone_block.text.strip().split()[0]

    status = driver.find_element(By.ID, "spanCurrentStateId").text.strip()


    # ТМЦ
    tmts_tab = driver.find_element(By.XPATH, "//span[@id='tabCustomerCardName52Id']")
    driver.execute_script("arguments[0].click();", tmts_tab)
    time.sleep(2)

    print("⏬ Переключаемся на iframe с ТМЦ...")
    # Ждём, пока появится сам контейнер
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "customerTabSection52Id"))
    )

    # Переключаемся на iframe внутри блока
    iframe = driver.find_element(By.CSS_SELECTOR, "#customerTabSection52Id iframe")
    driver.switch_to.frame(iframe)

    # И теперь можно искать dv_table уже внутри iframe
    print("⏳ Ждём dv_table...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "dv_table"))
    )

    # Читаем таблицу
    model = driver.find_element(By.XPATH, '//*[@id="dv_table"]/table/tbody/tr[2]/th[5]').text.strip()
    address_from_tmts = driver.find_element(By.XPATH, '//*[@id="dv_table"]/table/tbody/tr[2]/th[4]').text.strip()

    print(f"✅ Адрес: {address_from_tmts}")
    print(f"✅ Оборудование: {model}")

    # Не забудь переключиться обратно в основное окно после парсинга
    driver.switch_to.default_content()



    # 🔹 IPTVPORTAL
    print("🟡 Переход на вкладку IPTVPORTAL")

    iptv_tab = driver.find_element(By.XPATH, "//span[@id='tabCustomerCardName23Id']")
    driver.execute_script("arguments[0].click();", iptv_tab)
    time.sleep(2)

    # Скроллим до блока
    driver.execute_script("window.scrollBy(0, 600);")
    print("⏳ Ждём iframe IPTVPORTAL...")

    # Ждём появления iframe
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//div[@id='customerTabSection23Id']/iframe"))
    )

    # Переключаемся в iframe
    iptv_iframe = driver.find_element(By.XPATH, "//div[@id='customerTabSection23Id']/iframe")
    driver.switch_to.frame(iptv_iframe)

    # Получаем текст из div
    iptv_text_block = driver.find_element(By.XPATH, "/html/body/div").text
    lines = iptv_text_block.splitlines()

    iptv_login = ""
    iptv_password = ""

    for line in lines:
        if "Логин абонента" in line:
            iptv_login = line.replace("Логин абонента:", "").strip()
        elif "Пароль абонента" in line:
            iptv_password = line.replace("Пароль абонента:", "").strip()

    # Возвращаемся в основной фрейм
    driver.switch_to.default_content()

    print(f"✅ IPTV Login: {iptv_login}")
    print(f"✅ IPTV Password: {iptv_password}")



    # 🔄 Проверка и сохранение
    subscriber, created = Subscriber.objects.get_or_create(
        phone=phone,
        address=address_from_tmts or norm_address,
        defaults={
            "username": username or "Имя не указано",
            "role": "абонент",
            "tariff": tariff,
            "balance": balance,
            "status": status,
            "iptv_login": iptv_login,
            "iptv_password": iptv_password,
            "equipment": model,
        }
    )

    if not created:
        subscriber.username = username or subscriber.username
        subscriber.tariff = tariff
        subscriber.balance = balance
        subscriber.status = status
        subscriber.iptv_login = iptv_login
        subscriber.iptv_password = iptv_password
        subscriber.equipment = model
        subscriber.save()
        print(f"⚠️ Абонент уже существует. Обновлено: {subscriber}")
    else:
        print(f"✅ Абонент создан: {subscriber}")

# Запуск
chrome_options = Options()
chrome_options.add_argument("--headless")  # включаем headless
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")  # важно для корректной загрузки
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://userside.fish-net.kz/oper/index.php")
time.sleep(2)

driver.find_element(By.NAME, "username").send_keys("ormanova.e")
pw = driver.find_element(By.NAME, "password")
pw.send_keys("141179k")
pw.send_keys(Keys.RETURN)
time.sleep(4)

user_input = "01689"
norm_address, apartment = normalize_address(user_input)

open_user_profile(driver, norm_address, apartment)
parse_and_save_subscriber_data(driver, norm_address)

time.sleep(3)
driver.quit()
