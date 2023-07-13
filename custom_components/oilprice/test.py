import aiohttp, asyncio, datetime, re
from bs4 import BeautifulSoup


async def fetch_data(region):
    sensors = {}
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        response = await session.get(
            "http://www.qiyoujiage.com/" + region + ".shtml", headers=header
        )
    res = await response.text()

    soup = BeautifulSoup(res, "lxml")
    dls = soup.select("#youjia > dl")
    sensors["next_change_date"] = (
        soup.select("#youjiaCont > div")[1].contents[0].strip()
    )
    for dl in dls:
        k = re.search("\d+", dl.select("dt")[0].text).group()
        sensors[k] = dl.select("dd")[0].text
    sensors["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
    sensors["tips"] = soup.select("#youjiaCont > div:nth-of-type(2) > span")[
        0
    ].text.strip()  # 油价涨跌信息
    print(sensors)
    return sensors


if __name__ == "__main__":
    asyncio.run(fetch_data("jiangsu"))
