import re
import logging
import asyncio
from datetime import timedelta
from bs4 import BeautifulSoup

from homeassistant.const import CONF_REGION
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


async def fetch_data(hass, region: str) -> dict:
    """Fetch and parse oil price data from qiyoujiage.com — tries HTTPS first, falls back to HTTP."""
    _LOGGER.info(f"正在从 qiyoujiage.com 获取 {region} 的最新油价数据...")
    sensors = {}

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Use Home Assistant's shared connection pool to avoid creating/releasing connections frequently
    session = async_get_clientsession(hass)

    # Try HTTPS first, fall back to HTTP
    res = None
    for scheme in ("https", "http"):
        url = f"{scheme}://www.qiyoujiage.com/{region}.shtml"
        try:
            async with asyncio.timeout(10):
                async with session.get(url, headers=header) as response:
                    response.encoding = "utf-8"  # Force UTF-8 to prevent garbled Chinese
                    res = await response.text()
            _LOGGER.info(f"成功通过 {scheme.upper()} 获取数据")
            break
        except asyncio.TimeoutError:
            _LOGGER.warning(f"{scheme.upper()} 连接超时，尝试备用协议...")
            continue
        except Exception as err:
            _LOGGER.warning(f"{scheme.upper()} 请求失败: {err}，尝试备用协议...")
            continue

    if res is None:
        _LOGGER.error(f"所有协议尝试均失败，无法获取 {region} 油价数据")
        raise UpdateFailed(f"无法获取 {region} 油价数据")

    # Use native html.parser — zero C-ext dependency, runs on ARM gateways like Raspberry Pi
    soup = BeautifulSoup(res, "html.parser")

    # 1. Parse: next price adjustment date
    try:
        divs = soup.select("#youjiaCont > div")
        if len(divs) > 1:
            target_text = ""
            # Iterate over direct child nodes of the div, precisely locating non-tag text
            # containing "调整", "24时", or "预测"
            for content in divs[1].contents:
                if isinstance(content, str):
                    cleaned = content.strip()
                    if cleaned and ("调整" in cleaned or "24时" in cleaned or "预测" in cleaned):
                        target_text = cleaned
                        break
            # Fallback: use first line of get_text if child-node parsing fails
            if not target_text:
                cleaned_text = divs[1].get_text(separator="\n").strip()
                if cleaned_text:
                    target_text = cleaned_text.split("\n")[0].strip()

            sensors["next_change_date"] = target_text if target_text else "未知"
        else:
            sensors["next_change_date"] = "未知"
    except Exception as err:
        _LOGGER.warning(f"解析“下次油价调整时间”失败 (已执行降级容错): {err}")
        sensors["next_change_date"] = "未知"

    # 2. Parse: individual fuel price entries
    try:
        dls = soup.select("#youjia > dl")
        for dl in dls:
            dts = dl.select("dt")
            dds = dl.select("dd")
            if dts and dds:
                # Extract the first digit group from the label (supports 89#, 92#, 95#, 98#, 0# diesel)
                match = re.search(r"\d+", dts[0].text)
                if match:
                    k = match.group()
                    sensors[k] = dds[0].text.strip()
    except Exception as err:
        _LOGGER.warning(f"解析油价价格列表失败: {err}")

    # 3. Parse: price change tips / forecast
    try:
        # Prefer the specific red bold forecast text in the known layout
        spans = soup.select("#youjiaCont > div:nth-of-type(2) > span")
        if spans:
            sensors["tips"] = spans[0].text.strip()
        else:
            # Fallback: fuzzy search all spans outside <script> for fuel-related keywords
            all_spans = soup.select("#youjiaCont > div span")
            useful_span = None
            for s in all_spans:
                if s.parent and s.parent.name == "script":
                    continue
                text = s.text.strip()
                if any(word in text for word in ("元/吨", "升", "涨", "跌", "下调", "上调")):
                    useful_span = text
                    break

            if useful_span:
                sensors["tips"] = useful_span
            else:
                divs = soup.select("#youjiaCont > div")
                sensors["tips"] = divs[1].text.strip() if len(divs) > 1 else "无最新涨跌提示"
    except Exception as err:
        _LOGGER.warning(f"解析油价涨跌预测提示失败 (已执行降级容错): {err}")
        sensors["tips"] = "无最新涨跌提示"

    return sensors


class MyCoordinator(DataUpdateCoordinator):
    """Coordinator for async oil price updates — centralized fetch, distributed notification."""

    def __init__(self, hass, _config_entry) -> None:
        from . import DOMAIN

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{_config_entry.data[CONF_REGION]}",
            # Oil prices rarely update intraday; 6-hour refresh is sufficient
            update_interval=timedelta(hours=6),
        )
        self._config_entry = _config_entry
        self.sensors = {}

    async def _async_update_data(self) -> dict:
        """Core entry point for async data fetch — with global timeout and exception propagation."""
        try:
            # Outer 15-second timeout protection
            async with asyncio.timeout(15):
                return await self.fetch_data()
        except Exception as err:
            raise UpdateFailed(f"更新油价数据超时或拉取失败: {err}")

    async def fetch_data(self) -> dict:
        """Call the scraping/parsing function, update and sync global state cache."""
        sensors = await fetch_data(self.hass, self._config_entry.data[CONF_REGION])
        self.sensors = sensors
        _LOGGER.info(f"今日油价刷新成功: {sensors}")
        return sensors
