import re, logging, datetime, aiohttp, async_timeout

from datetime import timedelta
from homeassistant.const import CONF_REGION
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from bs4 import BeautifulSoup


_LOGGER = logging.getLogger(__name__)


async def fetch_data(region):
    _LOGGER.info("fetch_data")
    sensors = {}
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        response = await session.get(
            "http://www.qiyoujiage.com/" + region + ".shtml", headers=header
        )
    response.encoding = "utf-8"  # 不写这句会乱码
    res = await response.text()

    soup = BeautifulSoup(res, "lxml")
    dls = soup.select("#youjia > dl")
    sensors["next_change_date"] = (
        soup.select("#youjiaCont > div")[1].contents[0].strip()
    )
    for dl in dls:
        k = re.search("\d+", dl.select("dt")[0].text).group()
        sensors[k] = dl.select("dd")[0].text
    sensors["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sensors["tips"] = soup.select("#youjiaCont > div:nth-of-type(2) > span")[
        0
    ].text.strip()  # 油价涨跌信息

    return sensors


class MyCoordinator(DataUpdateCoordinator):
    """用于多个传感器同时更新信息的一个协调器"""

    def __init__(self, hass, _config_entry):
        """Initialize my coordinator."""
        from . import DOMAIN

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN + "_" + _config_entry.data[CONF_REGION],
            update_interval=timedelta(hours=1),
        )
        self.err_times = 0
        self._config_entry = _config_entry
        _LOGGER.info("init MyCoordinator")

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(10):
                self.err_times = 0
                return await self.fetch_data()
        except:
            if self.err_times < 10:
                self.err_times += 1
                await self._async_update_data()

    async def fetch_data(self):
        _LOGGER.info("MyCoordinator fetch data")
        sensors = await fetch_data(self._config_entry.data[CONF_REGION])
        self.sensors = sensors
        _LOGGER.info(sensors)
