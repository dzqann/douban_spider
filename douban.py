import requests
import json
import time
import random
import pymysql
from selenium import webdriver
import re
from lxml import etree

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
    'Cookie': 'll="118172"; bid=AYmLauhBbbk; _vwo_uuid_v2=D196B48C7585621EEB2004661B01E3C43|5d8e96bbf56077615f3505a7cf993de9; gr_user_id=d2a68bf0-8c34-40c4-a754-0b81c6cfb7cc; __utmc=30149280; dbcl2="199152197:k3unxLpAvjs"; ck=eFGX; push_noty_num=0; push_doumail_num=0; __utmv=30149280.19915; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1569061761%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3D-qLKtdiRHn_UFDU9nwCU_ayAdVoc0Lb0DtXSTZf1-YiQZYjDrZxoGCLQlkSf73gw%26wd%3D%26eqid%3Dd1b5d37e0027b19a000000035d85fb79%22%5D; _pk_id.100001.8cb4=12176e2a862075ce.1568970027.2.1569061761.1568970060.; _pk_ses.100001.8cb4=*; ap_v=0,6.0; __utma=30149280.1666213220.1568967768.1569039091.1569061762.7; __utmz=30149280.1569061762.7.4.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; __utmt=1; __utmb=30149280.2.10.1569061762'}


def get_info(page_num):
    base_url = 'https://movie.douban.com/j/search_subjects?type=movie&tag=%E7%83%AD%E9%97%A8&sort=recommend&page_limit=20&page_start={}'
    try:
        res = requests.get(base_url.format(page_num), headers=headers, timeout=30)
        res.raise_for_status()
        res.encoding = res.apparent_encoding
        res = json.loads(res.text)
    except Exception as e:
        print(str(e))
        return None

    result = dict()
    for each in res['subjects']:
        result[each['title']] = each['url']
    return result


def joint(element):
    length = len(element)
    if length == 1:
        return element[0]
    res = ''
    for i in range(length - 1):
        res += element[i]
        res += '/'
    res += element[length - 1]
    return res


def get_detail(name, url):
    driver_path = r'D:\Programme Files\Chrome\geckodriver.exe'
    driver = webdriver.Firefox(executable_path=driver_path)
    driver.set_page_load_timeout(15)
    try:
        driver.get(url)
    except:
        pass
    res = driver.page_source
    with open('test.html', 'w', encoding='utf8') as file:
        file.write(res)
        file.close()
    driver.close()
    x_year = "//div[@id='content']/h1/span[@class='year']/text()"
    x_director = "//div[@id='info']/span[1]/span[2]/a/text()"
    x_actors = "//div[@id='info']/span[3]/span[2]/span/a/text()"
    x_types = "//div[@id='info']/span[@property='v:genre']/text()"
    x_time = "//div[@id='info']/span[@property='v:runtime']/text()"
    x_score = "//strong[@property='v:average']/text()"
    pattern = re.compile(r'<span class="pl">制片国家/地区:</span>(.*?)<br>')
    try:
        places = pattern.findall(res)
        places = [x.strip() for x in places[0].split('/')]
    except:
        places = ''
    res = etree.HTML(res)
    year = res.xpath(x_year)
    score = res.xpath(x_score)[0]
    director = res.xpath(x_director)[0]
    types = res.xpath(x_types)
    actors = res.xpath(x_actors)
    if len(actors) == 0:
        actors = res.xpath("//div[@id='info']//a[@rel='v:starring']/text()")
    time = res.xpath(x_time)
    year = year[0].replace('(', '').replace(')', '')
    if len(actors) > 5:
        actors = actors[:5]
    try:
        time = re.search(r'([0-9]+)?', time[0]).group()
    except:
        time = 0
    print(name, year, director, time, score, actors, types)
    result = dict()
    result['name'] = name
    result['year'] = year
    result['director'] = director
    result['time'] = int(time)
    result['score'] = float(score)
    result['actors'] = joint(actors)
    result['places'] = joint(places)
    result['types'] = joint(types)
    # print(result)
    return result


def main():
    result = dict()
    for i in range(15):
        each = get_info(i * 20)
        result.update(each)
        time.sleep(random.uniform(0, 2))
        print(str(i) + ':' + str(len(each)))
    print(len(result))
    print(result)
    with open('result.json', 'w', encoding='utf8') as file:
        file.write(json.dumps(result, ensure_ascii=False, indent=4))
        file.close()


def insert():
    movies = json.loads(open('result.json', encoding='utf8').read())
    for each in movies:
        result = get_detail(each, movies[each])
        conn = pymysql.connect('localhost', 'root', '123456', 'douban')
        cursor = conn.cursor()
        base_sql = """
                    insert into movies(movie_name,director,places,actors,score,movie_year,types)
                    values('{movie_name}','{director}','{places}','{actors}',{score},{movie_year},'{types}')
                """
        try:
            sql = base_sql.format(movie_name=result['name'], director=result['director'],
                                  places=result['places'], actors=result['actors'], score=result['score'],
                                  movie_year=result['year'], types=result['types'])
            # print(sql)
            cursor.execute(sql)
            conn.commit()
            print('insert one')
        except Exception as e:
            print(str(e))
            conn.rollback()
        time.sleep(random.uniform(0, 2))

# 后来发现猪猪侠没有主演，所以没有添加进数据库
def test():
    each = "猪猪侠·不可思议的世界"
    result = get_detail(each, "https://movie.douban.com/subject/30324775/")
    conn = pymysql.connect('localhost', 'root', '123456', 'douban')
    cursor = conn.cursor()
    base_sql = """
                        insert into movies(movie_name,director,places,actors,score,movie_year,types)
                        values('{movie_name}','{director}','{places}','{actors}',{score},{movie_year},'{types}')
                    """
    try:
        sql = base_sql.format(movie_name=result['name'], director=result['director'],
                              places=result['places'], actors=result['actors'], score=result['score'],
                              movie_year=result['year'], types=result['types'])
        # print(sql)
        cursor.execute(sql)
        conn.commit()
        print('insert one')
    except Exception as e:
        print(str(e))
        conn.rollback()


test()
