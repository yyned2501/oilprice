# oilprice

这是一个用Python编写的爬虫程序，可以从[https://oilprice.com/](https://oilprice.com/)网站获取最新的石油价格数据，并传递到homeassistant。

## 功能

- 可以按不同省\直辖市获取不同品号的油价

## 依赖

- requests
- BeautifulSoup4

## 安装
- 下载并复制`custom_components/oilprice`文件夹到HomeAssistant根目录下的`custom_components`文件夹即可完成安装

## 配置

配置 > 设备与服务 >  集成 >  添加集成 > 搜索`oilprice`

或者点击: [![添加集成](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=oilprice)



