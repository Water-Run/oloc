# oloc: One-Line Calculation  

> The Chinese version is the original document. The English version is translated from the Chinese version using an LLM.  
> Under development  

## Overview  

`oloc` is a lightweight Python library that provides basic operations and simplification for expressions described in strings.  
`oloc` has the following standout features:  

- **Fraction-based calculations** to ensure accurate results  
- **Built-in support for various algebraic functions**  
- **Support for irrational numbers**:  
  - Including custom irrational numbers, such as short irrational numbers (e.g., `x`, `y`) and long irrational numbers wrapped in `<>` (e.g., `<irrational_number>`, which conveniently represents corresponding variables in expressions). These can be used for expression simplification.  
- **Strong compatibility with input**:  
  - A **symbol mapping table** allows multiple representations of the same content:  
    - For example, the symbol for pi `π` can be represented as `pi`, `p`, etc., and multiplication can be represented as `*`, `×`, `・`, etc.  
  - A **function conversion table** allows different ways to call the same function:  
    - For instance, the expressions `1/2^0.5`, `pow(1/2,1/2)`, and `sqrt(1/2)` are equivalent.  
  - **Support for various number formats**:  
    - The primary format is fractions (e.g., `3/4`), but it also supports common integers (e.g., `100`), decimals (e.g., `-0.1234`), mixed fractions (e.g., `2_1/2`), and even repeating decimals (e.g., `2.33...`), which are not supported by many other calculation libraries.  
- **Support for adding comments in expressions**, such as `1+1 # The most basic calculation #`  
- **Comprehensive error handling**, pinpointing the exact location of errors with corresponding suggestions  
- **Neat, formatted output results**  
- **Step-by-step results** for calculations  

## Documentation  

`oloc` comes with comprehensive documentation.  

1. Read the usage guide: [Usage Guide]()  
2. Learn about the underlying principles: [Project Notes]()  

> This document applies to the `oloc` version: `alpha-1.0`