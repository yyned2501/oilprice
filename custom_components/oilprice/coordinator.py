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


async def fetch_data(hass, region: str) -> dict:
    """自目标网站 qiyoujiage.com 获取并解析油价数据（纯函数，高鲁棒设计）"""
    _LOGGER.info(f"正在从 qiyoujiage.com 获取 {region} 的最新油价数据...")
    sensors = {}
    
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 采用 Home Assistant 全局共享连接池，避免高频创建和释放连接
    session = async_get_clientsession(hass)
    url = f"http://www.qiyoujiage.com/{region}.shtml"
    
    try:
        # 使用 Python 3.11+ 标准原生的 asyncio.timeout 机制，严格限制 10 秒超时
        async with asyncio.timeout(10):
            async with session.get(url, headers=header) as response:
                response.encoding = "utf-8"  # 强制指定 UTF-8 编码，防止中文乱码
                res = await response.text()
    except asyncio.TimeoutError:
        _LOGGER.error(f"从 qiyoujiage.com 获取 {region} 油价数据连接超时")
        raise
    except Exception as err:
        _LOGGER.error(f"网络拉取油价数据失败: {err}")
        raise

    # 统一采用原生、免 C 编译的 html.parser 解析引擎，保障在树莓派等 ARM 网关上的零依赖运行
    soup = BeautifulSoup(res, "html.parser")
    
    # 1. 极高鲁棒解析：下次调整时间
    try:
        divs = soup.select("#youjiaCont > div")
        if len(divs) > 1:
            target_text = ""
            # 遍历 div 内的所有直接子节点，精准定位包含“调整/24时”的非 HTML 标签纯文本内容
            for content in divs[1].contents:
                if isinstance(content, str):
                    cleaned = content.strip()
                    if cleaned and ("调整" in cleaned or "24时" in cleaned or "预测" in cleaned):
                        target_text = cleaned
                        break
            # 备选容错方案：如果无法通过子节点抓取，使用 get_text 的首行进行保底
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

    # 2. 极高鲁棒解析：单项汽柴油价格列表
    try:
        dls = soup.select("#youjia > dl")
        for dl in dls:
            dts = dl.select("dt")
            dds = dl.select("dd")
            if dts and dds:
                # 提取地区或标号文本中的首组数字（支持 89#, 92#, 95#, 98#, 0# 柴油等）
                match = re.search(r"\d+", dts[0].text)
                if match:
                    k = match.group()
                    sensors[k] = dds[0].text.strip()
    except Exception as err:
        _LOGGER.warning(f"解析油价价格列表失败: {err}")

    # 3. 极高鲁棒解析：油价涨跌 Tips 提示
    try:
        # 优先提取特定布局下红字加粗的预测文本
        spans = soup.select("#youjiaCont > div:nth-of-type(2) > span")
        if spans:
            sensors["tips"] = spans[0].text.strip()
        else:
            # 备选容错方案：如果页面结构有变，则深度模糊搜索所有不处于 JS 脚本中的带关键字符的 Span 标签
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

    # 自动记录每次成功更新的时间
    sensors["update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return sensors


class MyCoordinator(DataUpdateCoordinator):
    """用于油价传感器异步协同更新的协调器，实现集中拉取，分发通知"""

    def __init__(self, hass, _config_entry) -> None:
        from . import DOMAIN

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{_config_entry.data[CONF_REGION]}",
            # 油价日内通常没有多次更新，为降低服务器开销，高频拉取无意义，统一每 6 小时刷新一次
            update_interval=timedelta(hours=6),
        )
        self._config_entry = _config_entry
        self.sensors = {}

    async def _async_update_data(self) -> dict:
        """异步拉取数据的核心入口（带全局超时限制与异常向上传播，触发 HA 自动退避机制）"""
        try:
            # 外层套用 15 秒超时保护
            async with asyncio.timeout(15):
                return await self.fetch_data()
        except Exception as err:
            raise UpdateFailed(f"更新油价数据超时或拉取失败: {err}")

    async def fetch_data(self) -> dict:
        """调用爬取解析纯函数，更新并同步全局状态缓存"""
        sensors = await fetch_data(self.hass, self._config_entry.data[CONF_REGION])
        self.sensors = sensors
        _LOGGER.info(f"今日油价刷新成功: {sensors}")
        return sensors
