# oloc: One-Line Of Calculation  

> The Chinese version is the original documentation. The English version is translated from the Chinese version using LLM.  
> Under development.  

***[中文文档](README_zh.md)***  

## Overview  

`oloc` is a lightweight Python library that provides basic operations and simplification functionality for expressions described as strings.  
`oloc` has the following standout features:  

- **Fraction-based operations to ensure accurate results**  
- **Support for common functions**  
- **Robust compatibility with input**:  
    - Implements multiple forms of the same content through a symbol mapping table  
      - For example, the mathematical constant `π` can be represented as `pi`, `p`, etc., while the multiplication symbol can be represented as `*`, `×`, `・`, etc. In some cases, it can even support near-natural language inputs like `One plus one equals` or `一百的阶层`.  
      - The symbol mapping table supports custom extensions.  
    - Implements different ways to call the same function through a function conversion table  
      - For instance, the expressions `1/2^0.5`, `pow(1/2,1/2)`, and `sqrt(1/2)` are equivalent.  
      - The function conversion table supports custom extensions.  
    - Supports various formats of numerical input  
      - The primary format is fractions (e.g., `3/4`), but it also supports common integers (e.g., `100`), decimals (e.g., `-0.1234`), and even less common formats like mixed fractions (e.g., `2\1/2`) and repeating decimals (e.g., `2.33...`).  
      - Compatible with diverse input forms, such as number separators and scientific notation.  
- **Supports irrational numbers**  
  - In addition to built-in irrational numbers like `π` and `𝑒`, custom irrational numbers are also supported, including short custom irrational numbers (e.g., `x`, `y`) and long custom irrational numbers enclosed in `<>` (e.g., `<Irrational>`, which can easily represent variables in expressions). These can be used for expression simplification.  
- **Supports adding comments in expressions**, such as `1+1 #The Most basic calculation# =`  
- **Comprehensive exception handling, precisely pointing out errors and their locations with corresponding suggestions**  
- **Neat and formatted output results**  
  - The formatting features can be customized.  
- **Ability to retrieve step-by-step calculation results**  
- **Multi-type conversion support**, including `int`, `float`, and the native `Fraction` type  
  - Includes controllable floating-point conversion precision: explicitly specify it using the `?` operator or modify the default precision.  
- **Computation timeout restrictions**  

`oloc` relies on the `simpsave` library for data storage functionality (e.g., symbol mapping tables).  
> `simpsave` is a simple Python-native data persistence library. See [simpsave](https://github.com/Water-Run/SimpSave).  

## Documentation  

`oloc` offers **comprehensive documentation support**.  

1. **Read the usage tutorial at [Usage Tutorial](doc/zh/使用教程/使用教程目录.md)**  
2. **Understand the working principles at [Project Description](doc/zh/项目说明/项目说明梗概.md)**  

> This document applies to `oloc` version: `0.1.0`.