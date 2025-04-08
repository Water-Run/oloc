# olocconfig范式  

## 概要  

`olocconfig.ini`存储在源码路径下的`data`子文件夹中.  
其是一个`simpsave` `ini`文件.  
> 安装`simpsave`: `pip install simpsave`  

## 字段  

| 字段                                         | 说明                        | 类型     | 取值                                           | 缺省值                     |  
|--------------------------------------------|---------------------------|--------|----------------------------------------------|-------------------------|  
| `version`                                  | oloc版本                    | `str`  | 版本号字符串                                       | `7`                     | 
| `retain_decimal_places`                    | 损失精度的转换时保留的小数位数           | `int`  | 大于0的整数                                       | `7`                     | 
| `symbol_mapping_table`                     | 符号映射表,预处理符号映射操作根据本表进行     | `dict` | 键为字符串,值为字符串列表(且**值中包含键**).注意处理由上至下,由左至右的有序性. | [符号映射表](符号映射表.md)       |
| `function_mapping_table`                   | 函数映射表,预处理函数映射操作根据本表进行     | `dict` | 键为字符串,值为字符串列表(且**值中包含键**).注意处理由上至下,由左至右的有序性. | [函数映射表](函数映射表.md)       |  
| `formatting_output_function_options_table` | 格式化输出过滤器配置表.格式化输出配置将读取本表. | `dict` | 键为字符串,值根据配置项的不同各不相同.                         | [格式化输出过滤器配置表](格式化输出过滤器配置表.md) |  


## 修改脚本: `_dataloader.py`  

在`data`路径下,可以看到修改脚本`_dataloader.py`.修改脚本中的数据并运行该脚本执行修改.  
**对应项的变量名上表的字段名与保持一致.**  
运行出现`olocconfig updated`表明已成功修改数据.  
输出以下信息说明修改成功:  
```plaintext
dataloader: writing to olocconfig.ini
dataloader: olocconfig updated
```

---

***[点此](../项目说明梗概.md)跳转回说明梗概页面***

