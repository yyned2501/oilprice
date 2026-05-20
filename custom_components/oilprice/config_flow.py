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
    """通过 UI 添加集成时的配置流控制器"""

    data: Optional[Dict[str, Any]] = None

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """第一步：向用户展示并收集输入的省份拼音代码（如 jiangsu）"""
        _LOGGER.info("触发今日油价 ConfigFlow 初始步骤")
        errors: Dict[str, str] = {}
        
        setup_schema = vol.Schema(
            {
                vol.Required(CONF_REGION): cv.string,
            }
        )
        
        if user_input is not None:
            self.data = user_input
            # 自动使用输入的地区名（拼音）作为集成条目的名称
            return self.async_create_entry(title=user_input[CONF_REGION], data=self.data)
            
        return self.async_show_form(
            step_id="user",
            data_schema=setup_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """注册并加载自定义选项流程"""
        _LOGGER.info("加载今日油价选项卡配置流")
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """通过系统“选项”按钮修改已有集成时的配置流控制器"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """初始化选项步骤，允许用户直接更改省份/地区"""
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            # 核心优化：禁止直接修改只读的 config_entry.data (HA 架构设计红线)。
            # 必须使用 async_update_entry 异步流在 Hass 内部完成属性的事务性修改。
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            return self.async_create_entry(title="", data=user_input)

        # 默认展示已有配置项
        default_region = self.config_entry.data.get(CONF_REGION, "")
        options_schema = vol.Schema(
            {
                vol.Required(CONF_REGION, default=default_region): cv.string,
            }
        )
        
        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )
