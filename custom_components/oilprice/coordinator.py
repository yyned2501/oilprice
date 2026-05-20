import re
import logging
import datetime
import asyncio
from datetime import timedelta
from bs4 import BeautifulSoup

from homeassistant.const import CONF_REGION
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

async def fetch_data(hass, region):
    _LOGGER.info(f"正在从 qiyoujiage.com 获取 {region} 的油价数据...")
    sensors = {}
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36"
    }
    
    # 使用 Home Assistant 共享的高性能连接池，免去自行高频创建连接池的开销
    session = async_get_clientsession(hass)
    url = f"http://www.qiyoujiage.com/{region}.shtml"
    
    async with session.get(url, headers=header, timeout=10) as response:
        response.encoding = "utf-8"  # 强制指定 UTF-8 编码防乱码
        res = await response.text()

    # 改用 python 原生免编译的 html.parser，极大提升跨平台（如树莓派）的安装成功率
    soup = BeautifulSoup(res, "html.parser")
    
    # 1. 鲁棒解析：下次调整时间
    try:
        divs = soup.select("#youjiaCont > div")
        if len(divs) > 1 and divs[1].contents:
            sensors["next_change_date"] = str(divs[1].contents[0]).strip()
        else:
            sensors["next_change_date"] = "未知"
    except Exception as err:
        _LOGGER.warning(f"解析下次油价调整时间失败: {err}")
        sensors["next_change_date"] = "未知"

    # 2. 鲁棒解析：单项油价列表
    try:
        dls = soup.select("#youjia > dl")
        for dl in dls:
            dts = dl.select("dt")
            dds = dl.select("dd")
            if dts and dds:
                match = re.search(r"\d+", dts[0].text)
                if match:
                    k = match.group()
                    sensors[k] = dds[0].text.strip()
    except Exception as err:
        _LOGGER.warning(f"解析油价列表时发生错误: {err}")

    # 3. 鲁棒解析：油价涨跌 Tips 提示
    try:
        spans = soup.select("#youjiaCont > div:nth-of-type(2) > span")
        if spans:
            sensors["tips"] = spans[0].text.strip()
        else:
            divs = soup.select("#youjiaCont > div")
            sensors["tips"] = divs[1].text.strip() if len(divs) > 1 else "无最新涨跌提示"
    except Exception as err:
        _LOGGER.warning(f"解析油价涨跌提示失败: {err}")
        sensors["tips"] = "无最新涨跌提示"

    sensors["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return sensors


class MyCoordinator(DataUpdateCoordinator):
    """用于油价传感器异步协同更新的协调器"""

    def __init__(self, hass, _config_entry):
        from . import DOMAIN

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{_config_entry.data[CONF_REGION]}",
            update_interval=timedelta(hours=6),  # 油价一天只变一次，高频刷新意义不大，改为 6 小时刷新一次
        )
        self._config_entry = _config_entry
        self.sensors = {}

    async def _async_update_data(self):
        """异步拉取数据，使用标准的异常重试退避机制"""
        try:
            async with asyncio.timeout(15):  # 使用 Python 3.11+ 标准库原生的超时控制
                return await self.fetch_data()
        except Exception as err:
            raise UpdateFailed(f"拉取油价数据超时或失败: {err}")

    async def fetch_data(self):
        sensors = await fetch_data(self.hass, self._config_entry.data[CONF_REGION])
        self.sensors = sensors
        _LOGGER.info(f"今日油价刷新成功: {sensors}")
        return sensors
