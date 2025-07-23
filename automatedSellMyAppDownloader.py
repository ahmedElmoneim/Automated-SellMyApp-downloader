import time
import os
import re
from playwright.sync_api import sync_playwright

EMAIL = "[Your Mail]"
PASSWORD = "[Password]"


DOWNLOAD_DIR = "/Users/ahmedel-moneim/sellMyApp/downloaded/"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = p.chromium.launch_persistent_context(
            user_data_dir="/tmp/sellmyapp-user-data",
            headless=False,
            accept_downloads=True,
            downloads_path=DOWNLOAD_DIR
        )

        page = context.pages[0] if context.pages else context.new_page()

        print(">>> Logging into SellMyApp...")
        page.goto("https://www.sellmyapp.com/login/")
        time.sleep(2)

        page.get_by_role("textbox", name="Username").fill(EMAIL)
        page.get_by_role("textbox", name="Password").fill(PASSWORD)
        page.get_by_text("Remember Me").click()
        page.get_by_role("textbox", name=re.compile("Security question", re.I)).fill(SECURITY_ANSWER)

        input(">>> بعد تسجيل الدخول يدويًا إذا لزم الأمر، اضغط Enter للمتابعة...")

        page.wait_for_url("**/dashboard/**", timeout=15000)
        print(">>> Logged in successfully.")

        # الذهاب لصفحة المشتريات
        page.goto("https://www.sellmyapp.com/dashboard/?task=purchases")
        page.wait_for_load_state("domcontentloaded")
        print(">>> Fetching purchase links...")

        purchase_links = page.locator("a[href*='view-purchase']").all()
        print(f"Found {len(purchase_links)} purchases.")
        bundle_folder='unknown'
        game_title='unknown'
        for i, link in enumerate( purchase_links[27:], start=27  ):
            href = link.get_attribute("href")
            print(f"\n[{i+1}] Visiting: {href}")
            purchase_page = context.new_page()
            purchase_page.goto(href)
            time.sleep(2)

            # استخراج كارت اللعبة
            card = purchase_page.locator("div.thank-you-cart-item").first
            try:
                # bundle_title = purchase_page.locator("h1").first.inner_text().strip()
                raw_title = card.locator(".thank-you-cart-item-name").inner_text().strip()
                if not card.locator("a.thank-you-download-link").is_visible():
                    bundle_folder = sanitize_filename(raw_title.strip())
                    game_path = os.path.join(DOWNLOAD_DIR, bundle_folder)
                else:
                    game_title = sanitize_filename(raw_title.strip())
                    game_path = os.path.join(DOWNLOAD_DIR, game_title)
            except:
                bundle_folder = f"bundle_{i+1}"
                game_title = f"game_{i+1}"

            # إنشاء المسار الصحيح
            
            os.makedirs(game_path, exist_ok=True)
            print(f"📁 Game folder: {game_path}")

            # تحميل صورة اللعبة باستخدام Playwright
            try:
                img_url = card.locator("img").get_attribute("src")
                if img_url:
                    response = purchase_page.request.get(img_url)
                    img_path = os.path.join(game_path, "preview.png")
                    with open(img_path, "wb") as f:
                        f.write(response.body())
                    print(f"   ✓ Saved image to: {img_path}")
                else:
                    print("   ⚠️ No image URL found.")
            except Exception as e:
                print(f"   ⚠️ Failed to download image: {e}")

            # تحميل ملفات اللعبة
            download_buttons = purchase_page.locator(".thank-you-download-link")
            count = download_buttons.count()
            print(f" - Found {count} download(s)")

            for j in range(count):
                card = purchase_page.locator("div.thank-you-cart-item").nth(j+1)
                try:
                    # bundle_title = purchase_page.locator("h1").first.inner_text().strip()
                    raw_title = card.locator(".thank-you-cart-item-name").inner_text().strip()
                    if card.locator("a.thank-you-download-link").is_visible():
                        game_title = sanitize_filename(raw_title.strip())
                except:
                    bundle_folder = f"bundle_{i+1}"
                    game_title = f"game_{i+1}"

                # إنشاء المسار الصحيح
                game_path = os.path.join(DOWNLOAD_DIR, bundle_folder, game_title)
                os.makedirs(game_path, exist_ok=True)
                print(f"📁 Game folder: {game_path}")

                 # تحميل صورة اللعبة باستخدام Playwright
                try:
                    img_url = card.locator("img").get_attribute("src")
                    if img_url:
                        response = purchase_page.request.get(img_url)
                        img_path = os.path.join(game_path, "preview.png")
                        with open(img_path, "wb") as f:
                            f.write(response.body())
                        print(f"   ✓ Saved image to: {img_path}")
                    else:
                        print("   ⚠️ No image URL found.")
                except Exception as e:
                    print(f"   ⚠️ Failed to download image: {e}")
                try:
                     file_path_zip = os.path.join(game_path, f"{game_title}.zip")
                     file_path_rar = os.path.join(game_path, f"{game_title}.rar")
                     if os.path.exists(file_path_zip) or os.path.exists(file_path_rar):
                        print(f"   ⚠️ File already exist!")   
                     else:
                        with purchase_page.expect_download() as download_info:
                            download_buttons.nth(j).click()
                        download = download_info.value
                        ext = os.path.splitext(download.suggested_filename)[1]
                        is_zip = ext.lower() == ".zip"
                        is_rar = ext.lower() == ".rar"
                        
                        old_name = str(os.path.join(game_path, sanitize_filename(download.suggested_filename)))
                        new_name = file_path_rar

                        if os.path.exists(old_name):
                            os.rename(old_name, new_name)
                            print("⚠️ has Renamed Done!")
                        


                        if is_zip:
                            file_path = os.path.join(game_path, f"{game_title}.zip")
                        elif is_rar:
                            
                            file_path = os.path.join(game_path, f"{game_title}.rar")
                        else:
                            file_path = os.path.join(game_path, sanitize_filename(download.suggested_filename))
                        if os.path.exists(file_path):
                            print(f"   ⚠️ File already exist!")   
                        else:
                            download.save_as(file_path)
                            print(f"   ✓ Saved to: {file_path}")
                except Exception as e:
                    print(f"   ⚠️ Failed to download file #{j+1}: {e}")

            purchase_page.close()

        print("\n✅ Done downloading all games.")
        context.close()
        browser.close()

if __name__ == "__main__":
    run()
