import os
import time
import datetime
import random
import string
from playwright.sync_api import sync_playwright

class PlaywrightSnapService2:
    @staticmethod
    def _chmod_644(path):
        """统一设置图片权限为 644"""
        try:
            os.chmod(path, 0o644)
        except Exception as e:
            print(f"[WARN] chmod failed: {path}, {e}")

    @staticmethod
    def _generate_storage_dir(base_dir="app/static/storage/files"):
        """生成存储目录：年月日 + 8位随机字符串"""
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        full_path = os.path.join(base_dir, f"{date_str}")
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def capture_snap(self, html_path: str, task_token: str, element_ids: list = None):
        """
        :param html_path: HTML 文件路径或 URL
        :param task_token: 任务唯一标识，用于生成文件名
        :param element_ids: 需要截图的元素 id 列表，默认空则截图全页
        :return: dict 包含 success 与 failed，同时返回截图目录
        """
        element_ids = element_ids or []
        # 自动生成输出目录
        output_dir = self._generate_storage_dir()
        result = {"success": [], "failed": [], "dir": output_dir}
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--start-maximized"
                ]
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/114.0.0.0 Safari/537.36",
                java_script_enabled=True
            )
            page = context.new_page()

            # 打开页面
            if html_path.startswith("http"):
                page.goto(html_path, wait_until="networkidle")
            else:
                page.goto(f"file:///{html_path}", wait_until="load")

            # 滚动页面
            page.evaluate("""
                () => {
                    return new Promise(resolve => {
                        let totalHeight = 0;
                        let distance = 300;
                        const timer = setInterval(() => {
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            if(totalHeight >= document.body.scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)

            if element_ids:
                for element_id in element_ids:
                    selector = f"#{element_id}"
                    try:
                        page.wait_for_selector(selector, timeout=15000)
                        filename = f"{element_id}{task_token}{rand_str}.png"
                        output_img = os.path.join(output_dir, filename)
                        page.locator(selector).screenshot(path=output_img)
                        self._chmod_644(output_img)
                        result["success"].append({element_id: filename})
                    except Exception as e:
                        result["failed"].append({"id": element_id, "error": str(e)})
            else:
                try:
                    filename = f"fullpage{task_token}{rand_str}.png"
                    output_img = os.path.join(output_dir, filename)
                    page.screenshot(path=output_img, full_page=True)
                    self._chmod_644(output_img)
                    result["success"].append({"full_page": filename})
                except Exception as e:
                    result["failed"].append({"id": "full_page", "error": str(e)})
            browser.close()
        return result
