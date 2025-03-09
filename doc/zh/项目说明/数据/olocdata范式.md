# olocconfig范式  

## 概要  

`olocconfig.ini`存储在源码路径下的`data`子文件夹中.  
其是一个`simpsave` `ini`文件.  
> 安装`simpsave`: `pip install simpsave`  

## 字段表  

|字段| 说明              |类型| 取值     |缺省值|  
|---|-----------------|---|--------|---|  
|`retain_decimal_places`| 损失精度的转换时保留的小数位数 |`int`| 大于0的整数 |`7`| 
|`symbol_mapping_table`| 符号映射表,预处理符号转换操作根据本表进行 | `dict` | --     | [符号映射表](符号映射表.md) |

## 修改脚本: `_dataloader.py`  

## 缺省值  

---

***[点此](../项目说明梗概.md)跳转回说明梗概页面***

