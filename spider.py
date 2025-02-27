# -*- coding = utf-8 -*-

from bs4 import BeautifulSoup
import re
import urllib.request, urllib.error, urllib.parse
import xlwt
import sqlite3


def main():
    baseurl = 'https://movie.douban.com/top250?start='
    # 1、爬取网页
    datalist = getData(baseurl)

    savepath1 = "./豆瓣电影Top250.xls"
    saveData(datalist,savepath1)

    savepath2 = "./豆瓣电影Top250.db"
    initDB(savepath2)
    saveData2DB(datalist,savepath2)


# 影片链接的匹配规则
findLink = re.compile(r'<a href="(.*?)">')    # 匹配规则的正则表达式对象
# 影片图片
findImg = re.compile(r'<img.*src="(.*?)"', re.S)    #re.S忽略换行符
# 影片片名
findTitle = re.compile(r'<span class="title">(.*)</span>')
# 影片的评分
findRating = re.compile(r'<span class="rating_num" property="v:average">(.*)</span>')
# 影片评价人数
findJudge = re.compile(r'<span>(\d*)人评价</span>', re.S)
# 影片的概况
findInq = re.compile(r'<span class="inq">(.*)</span>')
# 影片的相关内容
findBd = re.compile(r'<p class="">(.*?)</p>', re.S)


def getData(baseurl):
    datalist = []
    num = 0
    # 2、逐一解析数据
    for i in range(0, 25):   # 调用获取页面信息的函数 10次
        url = baseurl + str(i*25)
        html = askURL(url)  # 保存获取到的单个页面的网页源码
        # html = urllib.request.urlopen(url).read()
        # 逐一解析数据
        soup = BeautifulSoup(html, 'html.parser')
        for item in soup.find_all("div", class_="item"):# 定位获取所需的标签内容
            # print(item) # 测试：单个电影item
            data = []
            item = str(item)

            link = re.findall(findLink, item)[0].replace('\xa0', "")    # \xa0（不间断空白符）
            data.append(link)

            imgSrc = re.findall(findImg, item)[0].replace('\xa0', "")
            data.append(imgSrc)

            title = re.findall(findTitle, item)
            if(len(title) >= 2):
                ctitle = title[0].replace('\xa0', "")
                data.append(ctitle)
                ftitle = title[1].replace('/',"").replace('\xa0', "")
                data.append(ftitle)
            elif(len(title) == 1):
                data.append(title[0].replace('\xa0', ""))
                data.append(" ")    # 第二个名称留空

            rating = re.findall(findRating, item)[0].replace('\xa0', "")
            data.append(rating)

            judge = re.findall(findJudge, item)[0].replace('\xa0', "")
            data.append(judge)

            inq = re.findall(findInq, item)
            if len(inq) != 0:
                inq = inq[0].replace('。',"").replace('\xa0', "")
                data.append(inq)
            else:
                data.append(" ")

            bd = re.findall(findBd, item)[0].replace('\xa0', "")
            bd = re.sub(r'<br(\s+)?/>(\s+)?', " ", bd)
            bd = re.sub('/', ' ', bd)
            data.append(bd.strip())

            if data:
                num +=1
            datalist.append(data)

    print(datalist)
    print(num)
    return datalist


# 得到指定一个URL的网页内容
def askURL(url):
    # 模拟浏览器头部信息
    head = {    # 这里访问的是www.douban.com，加上cookie才成功访问，不然会403
        "cookie":'''bid=lmDVVK_MwCE; dbcl2="287312225:gaIljLl3paE"; ck=A87B; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1740403496%2C%22https%3A%2F%2Faccounts.douban.com%2F%22%5D; _pk_id.100001.4cf6=c5aee2ffb5a4b0b1.1740403496.; push_noty_num=0; push_doumail_num=0; __yadk_uid=FMUehx3EWLsxQlgs8OU0iEQf5rgnlRfM''',
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0" }
    # 用户代理： 表示告诉浏览器我们是什么类型的机器、浏览器（我们能接受什么信息）
    req = urllib.request.Request(url, headers=head)

    html = ""
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode("utf-8")
        # print(html)
    except urllib.error.URLError as e:
        if hasattr(e, 'code'):  # hasattr 含有指定变量与否
            print(e.code)
        if hasattr(e, 'reason'):
            print(e.reason)

    return html


def saveData(datalist,savepath):
    print("save...")
    book = xlwt.Workbook(encoding='utf-8', style_compression = 0)
    sheet = book.add_sheet('豆瓣电影Top250', cell_overwrite_ok=True)
    col = ("电影详情链接", "图片链接", "影片中文名", "影片外国名", "评分", "评价数", "概括", "相关信息")
    for i in range(0, 8):
        sheet.write(0, i, col[i])
    for i in range(0,250):
        print("第%d条"%(i+1))
        data = datalist[i]
        for j in range(0,8):
            sheet.write(i+1, j, data[j])

    book.save(savepath)


def saveData2DB(datalist,savepath):
    conn = sqlite3.connect(savepath)
    c = conn.cursor()
    print("豆瓣电影-------------------------------------------",len(datalist))
    for data in datalist:
        for i in range(len(data)):
            if i == 4 or i == 5:
                pass
            else:
                data[i] = '"'+str(data[i])+'"'
        sql = '''
            insert into movie250 (info_link,pic_link,cname,fname,score,rated,instroduction,relax_info)
            values (%s)'''%",".join(data)
        print(sql)
        c.execute(sql)

    conn.commit()
    conn.close()

    print("成功保存到数据库")


def initDB(dbpath):
    sql = '''
        create table if not exists movie250 (
            id integer primary key autoincrement,
            info_link text,
            pic_link text,
            cname varchar,
            fname varchar,
            score numeric,
            rated numeric,
            instroduction text,
            relax_info text
        )
    '''
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()