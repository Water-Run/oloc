# 科学计算器CLI  

以下提供代码编写了一个示例的科学计算器终端程序,以加深对`oloc`的了解.  
使用`simpsave`进行数据持久化存储(使用`pip install simpsave`).  

## 示例程序  

```python
import oloc
import simpsave as ss

if __name__ == '__main__':
    print("oloc示例程序: 科学计算器CLI\n在'>>'后输入表达式进行计算.输入'quit'退出,`help`获取帮助")  
    while True:
        expression:str = input('>>')
        # if...else
        try:
            ...
        except OlocException as e:
            print(e)
            input('continue>>')
    input('close CLI>>')
```

---  
*[返回目录](使用教程目录.md)*  