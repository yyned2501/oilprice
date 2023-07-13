import logging
from typing import Any, Dict, Optional


from homeassistant import config_entries
from homeassistant.const import CONF_REGION
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    通过ui添加的入口
    最后一个user也是可以变的 和translations配置文件对应
    """

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        _LOGGER.info("async_step_user in config_flow")
        errors: Dict[str, str] = {}
        self.data = user_input
        # 与translations中的配置文件对应
        setup_schema = vol.Schema(
            {
                vol.Required(CONF_REGION): cv.string,
            }
        )
        if self.data:
            return self.async_create_entry(title=self.data["region"], data=self.data)
        return self.async_show_form(
            step_id="user",
            data_schema=setup_schema,
            errors=errors,  # q1暂时还没搞懂stepID的对应关系
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):  # 实际上的入口函数 调佣了这个就开始了流程
        _LOGGER.info("async_get_options_flow sensor oilprice")
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """
    继承点选项时跳出来的界面
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """没找到文档,和translations配置文件对应"""
        errors: Dict[str, str] = {}
        self.data = user_input
        if self.data:
            self.config_entry.data = self.data  # 实际有用的是这一条
            return self.async_create_entry(title="", data=self.data)  # 这条好像写不写都一样
        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_REGION, default=self.config_entry.data[CONF_REGION]
                ): cv.string,
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
