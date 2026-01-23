import os
import time
import datetime
import random
import string
from playwright.sync_api import sync_playwright


class PlaywrightSnapService1:
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
            try:
                if html_path.startswith("http"):
                    page.goto(html_path, wait_until="networkidle")
                else:
                    page.goto(f"file:///{html_path}", wait_until="load")
            except Exception as e:
                browser.close()
                result["failed"].append({"id": "page_load", "error": f"页面加载失败: {str(e)}"})
                return result

            # 等待页面稳定
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)

            # ---------------------- 处理弹窗 ----------------------
            try:
                # 尝试关闭常见的弹窗
                close_selectors = [
                    "button:has-text('关闭')",
                    "button:has-text('知道了')",
                    "button:has-text('同意')",
                    "button:has-text('接受')",
                    ".popup-close",
                    ".modal-close",
                    ".dialog-close",
                    ".close-btn",
                    ".ad-close",
                    ".notice-close"
                ]

                for selector in close_selectors:
                    try:
                        close_elements = page.locator(selector)
                        if close_elements.count() > 0:
                            # 点击第一个关闭按钮
                            close_elements.first.click(timeout=1000)
                            page.wait_for_timeout(300)
                            print(f"已关闭弹窗: {selector}")
                            break  # 关闭一个弹窗后就跳出
                    except:
                        continue

                # 处理iframe中的弹窗（如广告）
                for frame in page.frames:
                    try:
                        close_elements = frame.locator("button:has-text('关闭'), .close, .ad-close")
                        if close_elements.count() > 0:
                            close_elements.first.click(timeout=1000)
                            page.wait_for_timeout(300)
                            print("已关闭iframe中的弹窗")
                    except:
                        continue

            except Exception as e:
                print(f"处理弹窗时出错（不影响继续）: {e}")

            # ---------------------- 等待懒加载内容 ----------------------
            try:
                # 等待图片加载
                page.evaluate("""
                    () => {
                        const imgs = Array.from(document.getElementsByTagName('img'));
                        return Promise.all(imgs.map(img => {
                            if (img.complete) return Promise.resolve();
                            return new Promise((resolve, reject) => {
                                img.onload = resolve;
                                img.onerror = resolve;  // 即使出错也继续
                                setTimeout(resolve, 100);
                            });
                        }));
                    }
                """)

                # 等待可能的数据加载
                page.wait_for_timeout(500)

            except Exception as e:
                print(f"等待懒加载失败（不影响继续）: {e}")

            # ---------------------- 智能滚动（仅全屏截图需要） ----------------------
            if not element_ids:  # 只有全屏截图时才需要滚动
                try:
                    # 获取页面总高度
                    total_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")
                    viewport_height = page.evaluate("window.innerHeight")

                    if total_height > viewport_height:
                        print(f"开始智能滚动，总高度: {total_height}px")

                        scroll_step = 800
                        scroll_delay = 300
                        current_position = 0
                        max_attempts = total_height // scroll_step + 3

                        for attempt in range(max_attempts):
                            # 滚动一步
                            page.evaluate(f"window.scrollTo(0, {current_position})")
                            page.wait_for_timeout(scroll_delay)

                            # 等待可能的动态加载
                            page.wait_for_timeout(200)

                            # 检查是否到达底部
                            new_height = page.evaluate(
                                "document.body.scrollHeight || document.documentElement.scrollHeight")
                            current_scroll = page.evaluate("window.pageYOffset || document.documentElement.scrollTop")

                            # 如果高度增加，说明有动态加载
                            if new_height > total_height:
                                total_height = new_height

                            # 更新当前位置
                            current_position += scroll_step

                            # 如果已经滚动到底部或超过
                            if current_position >= total_height or current_scroll + viewport_height >= total_height:
                                print(f"滚动完成，当前滚动位置: {current_position}")
                                break

                        # 最终滚回顶部，确保截图从顶部开始
                        page.evaluate("window.scrollTo(0, 0)")
                        page.wait_for_timeout(800)  # 等待滚动完成和重绘
                        print("已滚动回顶部")
                    else:
                        print("页面高度小于视口，无需滚动")

                except Exception as e:
                    print(f"智能滚动失败，使用备用方案: {e}")
                    try:
                        # 备用方案：简单滚动到底部再回到顶部
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(1000)
                        page.evaluate("window.scrollTo(0, 0)")
                        page.wait_for_timeout(800)
                    except:
                        pass

            # ---------------------- 截图逻辑 ----------------------
            if element_ids:
                for element_id in element_ids:
                    selector = f"#{element_id}"
                    try:
                        # 等待元素稳定
                        element = page.wait_for_selector(selector, timeout=15000, state="visible")

                        # 确保元素在视图中（滚动到元素位置）
                        element.scroll_into_view_if_needed()
                        page.wait_for_timeout(500)  # 等待滚动后重绘

                        # 检查元素是否可见
                        is_visible = page.evaluate("""
                            (selector) => {
                                const el = document.querySelector(selector);
                                if (!el) return false;
                                const style = window.getComputedStyle(el);
                                return style.display !== 'none' && 
                                       style.visibility !== 'hidden' && 
                                       style.opacity !== '0' &&
                                       el.offsetWidth > 0 &&
                                       el.offsetHeight > 0;
                            }
                        """, selector)

                        if not is_visible:
                            result["failed"].append({"id": element_id, "error": "Element not visible"})
                            continue

                        filename = f"{element_id}{task_token}{rand_str}.png"
                        output_img = os.path.join(output_dir, filename)

                        # 对元素截图，增加等待确保稳定
                        page.wait_for_timeout(300)

                        # 尝试截图元素
                        element.screenshot(
                            path=output_img,
                            timeout=5000
                        )

                        # 检查截图文件
                        if os.path.exists(output_img) and os.path.getsize(output_img) > 1024:
                            self._chmod_644(output_img)
                            result["success"].append({element_id: filename})
                            print(f"元素截图成功: {element_id}")
                        else:
                            result["failed"].append({"id": element_id, "error": "Screenshot file is empty or too small"})

                    except Exception as e:
                        error_msg = str(e)
                        print(f"元素截图失败 {element_id}: {error_msg}")
                        result["failed"].append({"id": element_id, "error": error_msg})
            else:
                try:
                    filename = f"fullpage{task_token}{rand_str}.png"
                    output_img = os.path.join(output_dir, filename)

                    # 等待页面完全稳定
                    page.wait_for_timeout(800)

                    print("开始全屏截图...")
                    # 尝试全屏截图
                    page.screenshot(
                        path=output_img,
                        full_page=True,
                        timeout=10000
                    )

                    # 检查截图是否有效
                    if os.path.exists(output_img) and os.path.getsize(output_img) > 10240:  # 大于10KB
                        self._chmod_644(output_img)
                        result["success"].append({"full_page": filename})
                        print(f"全屏截图成功，文件大小: {os.path.getsize(output_img)} bytes")
                    else:
                        # 如果截图太小，可能是失败，尝试备用方案
                        print("全屏截图文件太小，尝试备用方案...")
                        self._try_backup_screenshot(page, output_img)
                        if os.path.exists(output_img) and os.path.getsize(output_img) > 10240:
                            self._chmod_644(output_img)
                            result["success"].append({"full_page": filename})
                            print(f"备用截图成功，文件大小: {os.path.getsize(output_img)} bytes")
                        else:
                            result["failed"].append({"id": "full_page", "error": "Screenshot file is empty or too small"})

                except Exception as e:
                    error_msg = str(e)
                    print(f"全屏截图失败: {error_msg}")

                    # 尝试备用方案
                    try:
                        print("尝试备用截图方案...")
                        self._try_backup_screenshot(page, output_img)
                        if os.path.exists(output_img) and os.path.getsize(output_img) > 10240:
                            self._chmod_644(output_img)
                            result["success"].append({"full_page": filename})
                            print("备用截图成功")
                        else:
                            result["failed"].append({"id": "full_page", "error": error_msg})
                    except Exception as backup_error:
                        result["failed"].append(
                            {"id": "full_page", "error": f"{error_msg} | 备用方案也失败: {backup_error}"})

            browser.close()

        print(f"截图任务完成，成功: {len(result['success'])}, 失败: {len(result['failed'])}")
        return result

    def _try_backup_screenshot(self, page, output_path):
        """
        备用截图方案：当全屏截图失败时使用
        """
        try:
            print("执行备用截图方案...")

            # 先尝试设置更大的视口
            original_viewport = page.viewport_size
            total_height = page.evaluate("document.body.scrollHeight || document.documentElement.scrollHeight")

            print(f"页面总高度: {total_height}")

            if total_height > 10000:  # 如果页面非常长，限制最大高度
                total_height = 10000

            # 临时调整视口大小以容纳整个页面
            page.set_viewport_size({"width": 1920, "height": total_height})
            page.wait_for_timeout(1500)  # 等待布局重绘

            # 尝试截图
            page.screenshot(path=output_path, timeout=10000)

            # 恢复原始视口
            if original_viewport:
                page.set_viewport_size(original_viewport)

        except Exception as e:
            print(f"备用截图方案失败: {e}")

            # 最后尝试：仅截取可视区域
            try:
                page.screenshot(path=output_path)
            except:
                raise Exception("所有截图方案都失败")
