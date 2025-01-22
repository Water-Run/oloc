# oloc: One-Line Calculation  

> Under Development  

## Overview  

`oloc` is a lightweight Python library that provides basic calculation and simplification functions for expressions described in string format.  
`oloc` is very simple and easy to use—it features excellent symbol compatibility (see the symbol conversion table) and supports a wide variety of number types (even mixed fractions and repeating decimals). In many cases, you can start using it without learning anything upfront: simply input the expression you want to calculate or simplify into `oloc.calculate()` to get the result.  
Designed with fraction-based calculations, it ensures the accuracy of results. `oloc` implements a variety of common basic operations, including mixed operations of rational and irrational numbers, as well as frequently used functions. These functions include not just algebraic ones like exponents or factorials but also transcendent functions like trigonometric and logarithmic functions. Moreover, for more advanced usage, `oloc` can display detailed calculation steps. If an error occurs during calculation, `oloc`'s robust exception system provides useful debugging information.  
If you’re looking to integrate basic scientific computation into your program, `oloc` is a great choice.  

> This documentation is for `oloc` version: `alpha-1.0`.  

## Installation  

`oloc` is available on PyPi. You can install it using `pip`:  

```bash
pip install oloc
```

Then, import `oloc` in your project:  
```python
import oloc
```

## Quick Start  

Use `oloc.calculate()` to perform calculations. The function takes a single argument: your calculation expression. The result is returned as a string.  

```python
import oloc
oloc.calculate("1+1") # Output: 2
oloc.calculate("-1/2+1/3") # Output: -1/6
oloc.calculate("cos(pi)*(e^2)") # Output: -e^2
```

> Before diving into the detailed tutorial, feel free to experiment intuitively.  

## Detailed Tutorial  

### Numbers  

`oloc` supports mixed operations of rational and irrational numbers.  
Adding a `-` (negative sign) before a number indicates it is negative.  

#### Rational Numbers  

Rational numbers are the core numeric type in `oloc`. During preprocessing, all rational numbers are converted into proper fraction form. However, the input formats supported are diverse.  

##### Integers  

Integers are numbers consisting solely of Arabic numerals and an optional `-`.  
Examples of integers:  
`0`, `1`, `-1`, `15`, `100`  

##### Fractions  

Fractions consist of a numerator and a denominator (the denominator cannot be 0). Fractions may also include an optional `-`, which can appear before either the numerator or denominator. It is generally recommended to place the `-` before the numerator for readability. Examples of fractions:  
`1/2`, `0/-10`, `-314/222`, `50/100`  
During each calculation, `oloc` automatically simplifies fractions into their lowest terms, i.e., proper fraction form. It also normalizes the negative sign (if both numerator and denominator have one) and moves it to the numerator. For example, `2/-4` is simplified to `-1/2`.  
`oloc` also supports mixed fractions, which can be represented using `_` or `|`. For example, `3_1/2` represents `3 + 1/2`, and `2|-1/4` represents `2 + (-1/4)`. Mixed fractions are converted during preprocessing.  

##### Decimals  

Rational decimals are numbers consisting of an integer part and a decimal part, separated by `.`. Decimals may also include an optional `-` at the beginning.  
Examples of decimals:  
`0.25`, `3.14`, `10500.12345`, `-0.0001`  
`oloc` also supports repeating decimals. Appending 3 to 6 `.` to the end of a decimal represents a repeating decimal. For example, `2.3...` or `123.123......`.  
`oloc` scans for repeating patterns and converts them into fraction form during preprocessing.  
You can explicitly specify the repeating part: after the consecutive `.` symbols, append `:` followed by the repeating portion. For example, `1.2...:3` is equivalent to `1.233...`.  

#### Irrational Numbers  

`oloc` supports irrational numbers. Operations between irrational numbers are supported, and if the final result contains irrational numbers, they are retained in the output.  
Native irrational numbers include `π` (also written as `p`, `P`, `pi`, or `PI`) and `e` (or `E`, `𝑒`).  
Some functions may yield irrational results. For example, `√1/2`.  
You can define custom irrational numbers using a `?` followed by a single letter, e.g., `?i`, `?s`.  
Alternatively, you can use `<` and `>` to enclose any non-space content to represent a custom irrational number, e.g., `<irrationalNumber>`, `<ie.ir>`, `<@sample>`, `<无理数>`.  
> Since irrational numbers are preserved in calculations, you can also use them as placeholders for structures you'd like to retain. Therefore, `oloc` natively supports using `x`, `y`, `z`, `i`, `j`, `k`, `u`, `a`, `b`, `c`, `d` (and their uppercase forms) as irrational variables.  
> For example, the result of `oloc.calculate(3x/6xy)` will be `1/2y`.  

### Operators  

`oloc` currently supports the following major operators:  

#### Basic Arithmetic  

The basic arithmetic operators are `+`, `-`, `*`, and `÷`.  
The fraction bar `/` is equivalent to the division symbol.  
Common multiplication symbols include `*` and `·`. In some cases, the multiplication symbol can be omitted:  
- When a number is adjacent to parentheses. For example, `3*(2+3)` can be written as `3(2+3)`.  
- When a number is adjacent to an irrational number. For example, `2*π/3` can be written as `2π/3`. This also applies when irrational numbers are used as variables, e.g., `-6*x` can be written as `-6x`.  
- When two irrational numbers are adjacent. For example, `π*e` can be written as `πe`.  
- In mixed forms of the above, e.g., `3((-2/3x)y)`.  

> It is recommended to use `+`, `-`, `*`, and `/` as arithmetic operators. Multiplication should only be omitted when connecting numbers and irrational numbers or between irrational numbers.  

#### Parentheses  

Parentheses are used to define operation precedence. `(` and `)` are the primary forms of parentheses. The content inside parentheses is treated as a unit and computed with priority according to the parentheses' nesting level.  
Examples of parentheses usage:  
```python
oloc.calculate("3/(-1+2)") # Output: 3
oloc.calculate("2*(3+4)") # Output: 14
oloc.calculate("5/(1+1)*(2-1)") # Output: 5/2
```
Expressions can use only parentheses `(` and `)` (this is the recommended practice). However, `oloc` also supports explicit distinctions among levels of parentheses: square brackets `[` and `]` and curly braces `{` and `}`.  
When distinct nesting levels are used, smaller levels must be deeper than larger ones. For example, the expression `3+(3/4+[5/6])` will throw an exception. Additionally, larger levels of brackets must have smaller levels already present. For example, `2+{3*[4+1]}` will also throw an exception.  
`oloc` does not limit the repetition of the same type of parentheses at different levels. For example, `[[2/3π+1]*x]-[sin(π)*(2^1/2-1)]` is a valid expression.  

#### Operator-Like Functions  

Some symbols are essentially shorthand for functions, making them convenient to use.  
In the examples, `x` and `y` represent parameters.  
Supported forms include:  
- `x^y` or `x**y`: Equivalent to the power function `pow`. For example, `2^3` (2 raised to the power of 3) is equivalent to `pow(2,3)`.  
- `√x` or `┌x`: Equivalent to the square root function, a variant of `pow` (i.e., raising to the 1/2 power). For example, `√1/2` equals `pow(1/2,1/2)`. For irrational numbers, the `√` symbol is retained. Example: `√2`.  
- `x%y`: Equivalent to the modulus function. For example, `2%1` equals `mod(2,1)`.  
- `|x|`: Equivalent to the absolute value function. For example, `|-2|` equals `abs(-2)`.  
- `x!`: Equivalent to the factorial function. For example, `4!` equals `fact(4)`.  
- `x°` or `xdeg`, `xdegree`, `x^o`: Equivalent to the degree-to-radian conversion function. For example, `30°` equals `rad(30)`.  
- `xrad` or `xradians`: By default, `oloc` assumes radian measure, so this operator is omitted. For example, `1rad` equals `1`.  

### Functions  

> This section is incomplete.  

In `oloc`, functions consist of a function name followed by parameters enclosed in parentheses.  
> Example of a valid expression containing a function in `oloc`:  
> ```python
> oloc.calculate("pow(2,3)+1/2") # Output: 17/2
> ```  

There are two categories of functions: algebraic functions and transcendental functions.  

#### Algebraic Functions  

`oloc` supports the following types of algebraic functions (`x`, `y` represent parameters):  

- **Exponential Function**: `pow(x, y)`  
  - **Description**  
    Computes `x` raised to the power `y`.  
  - **Properties**  
    - *Domain*:  
      `x ∈ R`, `y ∈ R`.  
    - *Range*:  
      `R`.  
  - **Variants**  
    - Operator variants: `x^y` and `x**y` (see above).  
    - Square root function: `sqrt(x)`, equivalent to `pow(x, 1/2)`.  
    - Square function: `square(x)`, equivalent to `pow(x, 2)`.  
    - Cube function: `cube(x)`, equivalent to `pow(x, 3)`.  
    - Reciprocal function: `reciprocal(x)`, equivalent to `pow(x, -1)`.  
    - Exponential function: `exp(x)`, equivalent to `pow(e, x)`.  
  - **Examples**  
    ```python
    oloc.calculate("pow(4,1/2)") # Output: 2; Equivalent: sqrt(4), 4^1/2, 4**1/2
    oloc.calculate("pow(2, 3)") # Output: 8
    oloc.calculate("pow(16, 1/4)") # Output: 2
    oloc.calculate("pow(-2, 3)") # Output: -8
    oloc.calculate("sqrt(9)") # Output: 3
    oloc.calculate("square(2)") # Output: 4
    oloc.calculate("cube(-3)") # Output: -27
    oloc.calculate("reciprocal(2/3)") # Output: 3/2
    oloc.calculate("exp(2)") # Output: e^2
    ```

- **Factorial Function**: `fact(x)`  
  - **Description**  
    Computes the factorial of `x`, the product of all integers from `1` to `x`.  
  - **Properties**  
    - *Domain*:  
      `x ∈ ℕ` (non-negative integers).  
    - *Range*:  
      `R - {0}`.  
  - **Variants**  
    - Operator variant: `x!` (see above).  
  - **Examples**  
    ```python
    oloc.calculate("fact(5)") # Output: 120; Equivalent: 5!
    oloc.calculate("fact(0)") # Output: 1
    ```

- **Absolute Value Function**: `abs(x)`  
  - **Description**  
    Computes the absolute value of `x`.  
  - **Examples**  
    ```python
    oloc.calculate("abs(-5)") # Output: 5
    ```

- **Sign Function**: `sign(x)`  
  - **Description**  
    Returns the sign of `x`: `-1` for negative numbers, `0` for zero, and `1` for positive numbers.  
  - **Examples**  
    ```python
    oloc.calculate("sign(-10)") # Output: -1
    oloc.calculate("sign(0)") # Output: 0
    oloc.calculate("sign(15)") # Output: 1
    ```

- **Greatest Common Divisor**: `gcd(x, y)`  
  - **Description**  
    Computes the greatest common divisor of `x` and `y`.  
  - **Examples**  
    ```python
    oloc.calculate("gcd(12, 18)") # Output: 6
    ```

- **Least Common Multiple**: `lcm(x, y)`  
  - **Description**  
    Computes the least common multiple of `x` and `y`.  
  - **Examples**  
    ```python
    oloc.calculate("lcm(4, 6)") # Output: 12
    ```

#### Transcendental Functions  

`oloc` supports two categories of transcendental functions: trigonometric functions (including inverse trigonometric functions) and logarithmic functions.  

- **Trigonometric Functions**  
  Trigonometric functions include `sin(x)`, `cos(x)`, `tan(x)`, and their inverses: `asin(x)`, `acos(x)`, and `atan(x)`.  
  - Example:  
    ```python
    oloc.calculate("sin(pi/2)") # Output: 1
    oloc.calculate("cos(0)") # Output: 1
    oloc.calculate("tan(pi/4)") # Output: 1
    oloc.calculate("asin(1)") # Output: pi/2
    ```

- **Logarithmic Functions**  
  Logarithmic functions include `log(x, y)` (logarithm of `x` with base `y`) and the natural logarithm `ln(x)`.  
  - Example:  
    ```python
    oloc.calculate("log(8, 2)") # Output: 3
    oloc.calculate("ln(e)") # Output: 1
    ```

### Calculations  

#### Using `calculate()`  

`calculate()` is the only interface exposed to users by `oloc`. Interaction with `oloc` happens entirely through this function.  
The function `calculate()` is defined as follows:  
```python
def calculate(expression: str, /, process_list: bool = False, time_limit: int = 5) -> str | list[str]:
    ...
```

*Parameter Details*:  

#### Calculation Process  

> Note: `oloc` only supports real number calculations.  

When calling `calculate()`, `oloc` performs the following steps in sequence:  

##### Preprocessing  

`oloc` first scans the input expression and performs preprocessing using regular expressions.  
Preprocessing operations include:  
1. Removing spaces.  
2. Removing the trailing `=` from the expression (if present).  
3. Adding omitted multiplication symbols.  
4. Converting mixed fractions and repeating decimals into fraction form (if present).  
5. Validating the correctness of parentheses and converting all types of brackets into parentheses (`(`, `)`) (if present).  
6. Mapping alias symbols to their standardized forms using the symbol conversion table.  
7. Converting all numeric values into fraction form.  
8. Mapping alias functions to their standardized forms using the function conversion table.  
9. Performing static checks on the expression.  

##### Calculation  

##### Other: Output Restoration  

### Exceptions  

> This section is incomplete.  

`oloc` includes the following custom exceptions:  

#### Parsing Exceptions  

- **FormatError**  

- **FunctionConversionError**  

#### Calculation Exceptions  

##### General Calculation Exceptions  

- **DivideByZeroError**  
  - **Description**  
    Raised when the expression contains a division by zero.  
  - **When It Occurs**  
    Modify terms that use `0` as a divisor.  
  - **Example**  
    ```python
    oloc.calculate("5/0 % -1/4 =")
    ```
    ```bash
    DivideByZeroError:
    ___
    5/0%-1/4
      ^
    The divisor cannot be 0
    ```

- **TimeOutError**  
  - **Description**  
    Raised when the calculation exceeds the allowed time limit without producing a result.  
  - **When It Occurs**  
    The result may be too large, or the time limit may be too short (default is 5 seconds). Modify the expression or increase the time limit to avoid this issue. Note that the performance of your computer may also affect this.  
  - **Example**  
    ```python
    oloc.calculate("10000!", time_limit=3)
    ```
    ```bash
    TimeOutError:
    10000!
    ^
    The calculation was aborted because it could not be completed within the time limit of 3s. Check the range of calculation results.
    ```

##### Function Calculation Exceptions  

- **FunctionParameterError**  

## Conversion Table  

> This section is incomplete.  

## Example Program: Scientific Calculator  

> This section is incomplete.  

Below is an example program that provides a terminal-based scientific calculator. It also uses `simpsave` to support local storage of results and processes.  
Before running the example program, ensure that `oloc` and `simpsave` are installed via `pip`:  

```python
import simpsave as ss
import oloc

FILE_NAME = 'OlocScientificCalculatorDemo.ini' # Local storage for calculations

def console(file: str):
    print("Oloc Scientific Calculator\n")
    while True:
        expression = input(">> ")
        try:
            result = oloc.calculate(expression)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    console(FILE_NAME)
```