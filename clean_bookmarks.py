# 导入requests库，用于发送HTTP请求
import requests
# 导入BeautifulSoup类，用于解析HTML文档
from bs4 import BeautifulSoup
# 导入time模块，用于处理时间相关的操作
import time
# 导入concurrent.futures模块，用于实现并发执行
import concurrent.futures

def parse_bookmarks(html_file):
    """
    解析HTML文件中的书签，返回所有书签的URL列表和BeautifulSoup对象。
    
    参数:
    html_file (str): 包含书签的HTML文件路径
    
    返回:
    list: 所有书签的URL列表
    BeautifulSoup: 解析后的BeautifulSoup对象
    """
    # 打开HTML文件，使用utf-8编码读取内容
    with open(html_file, 'r', encoding='utf-8') as file:
        # 使用BeautifulSoup解析HTML文件内容
        soup = BeautifulSoup(file, 'html.parser')
        # 查找所有<a>标签，获取href属性，生成URL列表
        links = [a['href'] for a in soup.find_all('a', href=True)]
    # 返回URL列表和BeautifulSoup对象
    return links, soup

def check_link_validity(url):
    """
    检测链接是否有效，返回状态码和是否有效。
    增加重试机制，并放宽有效性判断（2xx和3xx状态码均视为有效）。
    不对包含特定字段的链接进行检测，默认这些链接为有效。
    
    参数:
    url (str): 需要检测的URL
    
    返回:
    tuple: (url, status_code, is_valid)
    """
    # 如果链接包含特定字段，默认其为有效链接
    excluded_keywords = ['github', 'google', 'huggingface', 'docker', '127.0.0.1', 'localhost']
    # 检查URL中是否包含排除的关键词
    if any(keyword in url for keyword in excluded_keywords):
        # 返回URL、状态码200和有效标志True
        return url, 200, True

    # 禁用urllib3的InsecureRequestWarning
    import urllib3
    # 禁用SSL警告
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 设置最大重试次数为5
    max_retries = 5  # 增加重试次数
    # 循环尝试检测链接
    for attempt in range(max_retries):
        try:
            # 发送HTTP GET请求，禁用SSL验证，设置超时时间为10秒，允许重定向
            response = requests.get(url, timeout=10, verify=False, allow_redirects=True)
            # 如果状态码在2xx或3xx范围内，视为有效链接
            if 200 <= response.status_code < 400:
                # 返回URL、状态码和有效标志True
                return url, response.status_code, True
            # 如果状态码为403，视为有效链接
            elif response.status_code == 403:
                # 返回URL、状态码和有效标志True
                return url, response.status_code, True
            else:
                # 返回URL、状态码和有效标志False
                return url, response.status_code, False
        except requests.exceptions.SSLError as e:
            # 处理SSL错误，尝试忽略SSL验证
            try:
                # 再次发送HTTP GET请求，禁用SSL验证，设置超时时间为10秒，允许重定向
                response = requests.get(url, timeout=10, verify=False, allow_redirects=True)
                # 如果状态码在2xx或3xx范围内，视为有效链接
                if 200 <= response.status_code < 400:
                    # 返回URL、状态码和有效标志True
                    return url, response.status_code, True
                # 如果状态码为403，视为有效链接
                elif response.status_code == 403:
                    # 返回URL、状态码和有效标志True
                    return url, response.status_code, True
                else:
                    # 返回URL、状态码和有效标志False
                    return url, response.status_code, False
            except requests.RequestException as e:
                # 如果达到最大重试次数，返回URL、None和有效标志False
                if attempt == max_retries - 1:
                    return url, None, False
                # 重试前等待1秒
                time.sleep(1)  # 重试前等待1秒
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            # 如果达到最大重试次数，返回URL、None和有效标志False
            if attempt == max_retries - 1:
                return url, None, False
            # 重试前等待1秒
            time.sleep(1)  # 重试前等待1秒
        except requests.RequestException as e:
            # 如果达到最大重试次数，返回URL、None和有效标志False
            if attempt == max_retries - 1:
                return url, None, False
            # 重试前等待1秒
            time.sleep(1)  # 重试前等待1秒

def clean_bookmarks(html_file, output_file):
    """
    清理书签，检测无效链接，并将清理后的书签保存到新的HTML文件中。
    
    参数:
    html_file (str): 输入的书签HTML文件路径
    output_file (str): 输出的清理后书签HTML文件路径
    """
    # 记录脚本开始执行的时间
    start_time = time.time()
    # 解析HTML文件，获取所有书签URL和BeautifulSoup对象
    links, soup = parse_bookmarks(html_file)
    # 初始化有效链接和无效链接列表
    valid_links = []
    invalid_links = []
    
    # 打印需要检测的链接的条目及数量
    print(f"Total links to check: {len(links)}")
    
    try:
        # 使用线程池并行处理链接检测，最大线程数为10
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # 提交链接检测任务到线程池
            futures = [executor.submit(check_link_validity, link) for link in links if "2025" not in link]
            # 遍历已完成的任务，获取检测结果
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                # 获取检测结果，包括URL、状态码和是否有效
                url, status_code, is_valid = future.result()
                # 打印当前检测的链接信息
                print(f"Checking link {i}/{len(links)}: {url}")
                # 如果链接有效，添加到有效链接列表
                if is_valid:
                    valid_links.append(url)
                else:
                    # 如果链接无效，添加到无效链接列表，并打印无效链接信息
                    invalid_links.append(url)
                    print(f"Invalid link: {url}")
    except KeyboardInterrupt:
        # 如果用户中断进程，打印提示信息并退出
        print("\nProcess interrupted by user. Exiting...")
        return
    
    # 如果存在无效链接
    if invalid_links:
        # 询问用户是否要移除无效链接
        user_input = input(f"\nFound {len(invalid_links)} invalid links. Do you want to remove them? (y/n): ")
        # 如果用户选择移除无效链接
        if user_input.lower() == 'y':
            # 遍历所有<a>标签，移除无效链接
            for a_tag in soup.find_all('a', href=True):
                # 如果链接在无效链接列表中，移除该标签
                if a_tag['href'] in invalid_links:
                    a_tag.decompose()
            # 将清理后的书签保存到文件
            with open(output_file, 'w', encoding='utf-8') as file:
                # 将BeautifulSoup对象转换为字符串并写入文件
                file.write(str(soup))
            # 打印保存文件的信息
            print(f"Cleaned bookmarks saved to {output_file}")
        else:
            # 如果用户选择不移除无效链接，打印提示信息
            print("No changes were made.")
    else:
        # 如果没有无效链接，打印提示信息
        print("No invalid links found.")
    
    # 记录脚本结束执行的时间
    end_time = time.time()
    # 打印脚本执行时间
    print(f"Script execution time: {end_time - start_time:.2f} seconds")

# 示例调用
if __name__ == "__main__":
    # 设置输入的书签HTML文件路径
    html_file = "bookmarks.html"  # 替换为你的书签HTML文件路径
    # 设置输出的清理后书签HTML文件路径
    output_file = "cleaned_bookmarks.html"  # 输出文件路径
    # 调用clean_bookmarks函数，清理书签
    clean_bookmarks(html_file, output_file)