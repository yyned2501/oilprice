import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.const import CONF_REGION
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

PROVINCES = {
    "北京(beijing)": "beijing",
    "上海(shanghai)": "shanghai",
    "天津(tianjin)": "tianjin",
    "重庆(chongqing)": "chongqing",
    "河北(hebei)": "hebei",
    "山西(shanxi)": "shanxi",
    "内蒙古(neimenggu)": "neimenggu",
    "辽宁(liaoning)": "liaoning",
    "吉林(jilin)": "jilin",
    "黑龙江(heilongjiang)": "heilongjiang",
    "江苏(jiangsu)": "jiangsu",
    "浙江(zhejiang)": "zhejiang",
    "安徽(anhui)": "anhui",
    "福建(fujian)": "fujian",
    "江西(jiangxi)": "jiangxi",
    "山东(shandong)": "shandong",
    "河南(henan)": "henan",
    "湖北(hubei)": "hubei",
    "湖南(hunan)": "hunan",
    "广东(guangdong)": "guangdong",
    "广西(guangxi)": "guangxi",
    "海南(hainan)": "hainan",
    "四川(sichuan)": "sichuan",
    "贵州(guizhou)": "guizhou",
    "云南(yunnan)": "yunnan",
    "西藏(xizang)": "xizang",
    "陕西(shaanxi)": "shaanxi",
    "甘肃(gansu)": "gansu",
    "青海(qinghai)": "qinghai",
    "宁夏(ningxia)": "ningxia",
    "新疆(xinjiang)": "xinjiang",
}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow controller for adding the integration via UI."""

    data: Optional[Dict[str, Any]] = None

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """First step: present province dropdown selector."""
        _LOGGER.info("触发今日油价 ConfigFlow 初始步骤")
        errors: Dict[str, str] = {}

        setup_schema = vol.Schema(
            {
                vol.Required(CONF_REGION): vol.In(PROVINCES),
            }
        )

        if user_input is not None:
            self.data = user_input
            # Use the selected province pinyin as the integration entry title
            return self.async_create_entry(title=user_input[CONF_REGION], data=self.data)

        return self.async_show_form(
            step_id="user",
            data_schema=setup_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Register and load the custom options flow."""
        _LOGGER.info("加载今日油价选项卡配置流")
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow controller for modifying an existing integration entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initialize options step — allow user to change province/region via dropdown."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Use async_update_entry to modify the config entry transactionally
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            return self.async_create_entry(title="", data=user_input)

        # Pre-select the currently configured province
        default_region = self.config_entry.data.get(CONF_REGION, "")
        options_schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=default_region): vol.In(PROVINCES),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
