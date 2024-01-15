import os
import requests
import img2pdf
import ssl
import time

from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

import urllib3
import urllib.request
import ssl

class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)

def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session

# THESIS_URL = "https://thesis.fudan.edu.cn/onlinePDF?dbid=72&objid=56_56_50_54_52_51&flag=online"
# URL = "https://thesis.fudan.edu.cn/onlinePDF?dbid=72&objid=48_50_56_57_49_51&flag=online"
# SAVE_DIR = "D:/毕业论文"


MAX_RETRY = 5
SLEEP_TIME = 5


def init_base_header(cookie=None):
    header = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "thesis.fudan.edu.cn",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "Document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

    if cookie:
        header["Cookie"] = cookie
    return header


def get_system_session(url="https://thesis.fudan.edu.cn/"):
    resp = requests.get(url=url,
                        headers=init_base_header())
    assert resp.status_code == 200
    return resp.headers["Set-Cookie"].split(";")[0]


def get_thesis_pdf_location(thesis_url, cookie):
    resp = requests.get(url=thesis_url,
                        headers=init_base_header(cookie),
                        allow_redirects=False)
    assert resp.status_code == 302 # should be redirect
    return resp.headers["Location"]


def parse_host_from_location(loc):
    return loc.split("/")[2]


def get_pdf_index(location, host):
    def __init_header():
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": host,
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
    
    with get_legacy_session().get(url=location,
                                  headers=__init_header(),
                                  allow_redirects=False) as resp:
        assert resp.status_code == 302
        return resp.headers["Location"], resp.headers["Set-Cookie"].split(";")[0]
    # resp = requests.get(url=location,
    #                     headers=__init_header(),
    #                     allow_redirects=False,
    #                     verify=False)
    assert resp.status_code == 302 # should be redirect
    return resp.headers["Location"], resp.headers["Set-Cookie"].split(";")[0]


def get_read_url_base(host):
    return "http://{}/read".format(host)


def get_jpg_url(pdf_id, cookie, host):
    def __init_header():
        return {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": cookie,
            "Host": host,
            "Pragma": "no-cache",
            "Referer": "{}/{}".format(get_read_url_base(host), pdf_id),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
    
    url = "{}/jumpServlet?page=0&{}".format(get_read_url_base(host), pdf_id.split("?")[1])
    url = url.replace("http", "https")
    with get_legacy_session().get(url=url,
                                  headers=__init_header()) as resp:
        assert resp.status_code == 200
        content = resp.json()
        src = content["list"][0]["src"]
        return "/".join(src.split("/")[: -1])
    # resp = requests.get(url=url,
    #                     headers=__init_header())
    assert resp.status_code == 200

    content = resp.json()
    src = content["list"][0]["src"]
    return "/".join(src.split("/")[: -1])


def get_jpg_binary(host, jpg_url, page, cookie, pdf_id):
    def __init_header():
        return {
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": cookie,
            "Host": host,
            "Pragma": "no-cache",
            "Referer": "{}/{}".format(get_read_url_base(host), pdf_id),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

    def __get_jpg_name(page):
        return "P01_{:0>5d}.jpg".format(page)

    url = "{}/{}/{}".format(get_read_url_base(host), 
                          jpg_url,
                          __get_jpg_name(page))
    resp = requests.get(url=url,
                        headers=__init_header())
    
    if resp.status_code == 200:
        return resp.content
    else:
        return None


def save_jpg(path, data):
    with open(path, "wb") as f:
        f.write(data)


def download_pages(save_dir, host, jpg_url, cookie, pdf_id,
                   low = 1, high=100, to_pdf=False):
    jpgs = []

    for page in range(low, high + 1, 1):
        print("\rDownloading page {}...".format(page), end="")

        bin_data = get_jpg_binary(host, jpg_url, cookie=cookie, pdf_id=pdf_id,
                                  page=page)
        
        if bin_data is None:
            print("page ended.")
            break

        filename = "{}/{}.jpg".format(save_dir, page)
        save_jpg(filename, bin_data)
        if to_pdf:
            jpgs.append(filename)
    
    if to_pdf:
        with open("{}/merged.pdf".format(save_dir), "wb") as f:
            f.write(img2pdf.convert(jpgs))
    
    print("Done!")


def run(save_dir, low, high, to_pdf):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # preparation
    loc = get_thesis_pdf_location(thesis_url=URL,
                                  cookie=get_system_session())
    host = parse_host_from_location(loc)
    print("Got host: {}".format(host))

    pdf_id, pdf_session = get_pdf_index(loc, host)
    print("Got pdf cookie: {}".format(pdf_session))

    jpg_url = get_jpg_url(pdf_id, pdf_session, host)
    print("Got pdf base url: {}".format(jpg_url))

    # batch download
    download_pages(save_dir=save_dir,
                   host=host,
                   jpg_url=jpg_url,
                   cookie=pdf_session,
                   pdf_id=pdf_id,
                   low=low, high=high, to_pdf=to_pdf)
    
'''
V2: 修改
'''
def get_jpg_list(pdf_id, cookie, host, page=0):
    def __init_header():
        return {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": cookie,
            "Host": host,
            "Pragma": "no-cache",
            "Referer": "{}/{}".format(get_read_url_base(host), pdf_id),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
    
    url = "{}/jumpServlet?page={}&{}".format(get_read_url_base(host), page, pdf_id.split("?")[1])
    url = url.replace("http", "https")

    attempt_cnt = 0
    while (attempt_cnt < MAX_RETRY):
        with get_legacy_session().get(url=url,
                                    headers=__init_header()) as resp:
            if resp.status_code == 200:
                try:
                    content = resp.json()
                except RequestsJSONDecodeError as e:
                    content = None
                finally:
                    return content

            else:
                print(f"Failed to get page, response code = {resp.status_code}. Retrying {attempt_cnt}/{MAX_RETRY}...")
                attempt_cnt += 1
                time.sleep(SLEEP_TIME)
    raise Exception("ERROR")

        

def get_pdf_V2(cookie, host, pdf_id, pdf_url):
    def __init_header():
        return {
            "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cookie": cookie,
            "Referer": "{}/{}".format(get_read_url_base(host), pdf_id),
            "Sec-Ch-Ua": r'"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
            "Sec-Ch-Ua-Mobile": r"?0",
            "Sec-Fetch-Dest": r"image",
            "Sec-Fetch-Mode": r"no-cors",
            "Sec-Fetch-Site": r"same-origin",
            "Sec-Ch-Ua-Platform": "Windows",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }


    with get_legacy_session().get(url=pdf_url,
                                  headers=__init_header()) as resp:
        if resp.status_code == 200:
            return resp.content
        else:
            return None


def download_pages_V2(save_dir, host, cookie, pdf_id,
                       to_pdf=False):
    jpgs = []
    cur_page = 0

    while (True):
        page_list = get_jpg_list(pdf_id, cookie, host, page=cur_page)
        if page_list is None:
            break
        page_list = page_list['list']

        for each in page_list:
            pdf_url = each['src']
            print("\rDownloading page {}...".format(each['id']), end="")

            bin_data = get_pdf_V2(cookie, host, pdf_id, pdf_url)
        
            if bin_data is None:
                print("page ended.")
                break
            
            filename = "{}/{}.jpg".format(save_dir, each['id'])
            save_jpg(filename, bin_data)
            if to_pdf:
                jpgs.append(filename)

        skip_step = len(page_list)
        cur_page += skip_step

    
    if to_pdf:
        with open("{}/merged.pdf".format(save_dir), "wb") as f:
            f.write(img2pdf.convert(jpgs))
    
    print("Done!")

def run_V2(thesis_url,save_dir, to_pdf):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # preparation
    loc = get_thesis_pdf_location(thesis_url=thesis_url,
                                  cookie=get_system_session())
    host = parse_host_from_location(loc)
    print("Got host: {}".format(host))

    pdf_id, pdf_session = get_pdf_index(loc, host)
    print("Got pdf cookie: {}".format(pdf_session))

    download_pages_V2(save_dir=save_dir,
                   host=host,
                   cookie=pdf_session,
                   pdf_id=pdf_id,
                   to_pdf=to_pdf)
    
def main():
    import argparse

    parser = argparse.ArgumentParser(description='sovits4 inference')

    # 一定要设置的部分
    parser.add_argument('-p', '--paper', type=str, default="https://thesis.fudan.edu.cn/onlinePDF?dbid=72&objid=48_50_56_57_49_51&flag=online", help='模型路径')
    parser.add_argument('-s', '--save_path', type=str, default="D:/毕业论文", help='配置文件路径')
    args = parser.parse_args()

    url = args.paper
    save_dir = args.save_path

    run_V2(thesis_url=url,save_dir=save_dir, to_pdf=True)

if __name__ == "__main__":
    main()