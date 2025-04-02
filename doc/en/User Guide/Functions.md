# Functions

In `oloc`, functions consist of a function name followed by parameters enclosed in parentheses `()`. If a function supports multiple parameters, they are separated by `,` or `;`.

> **If you use numeric delimiters, you must use `;` to separate parameters**, such as `power(100,000;2)`; otherwise, parsing errors will occur.  
>> **This rule also applies to numeric values within expressions involving nested functions.**

> An example of a valid `oloc` expression containing a function:
> ```python
> oloc.calculate("pow(2,3)+1/2") # Output: 17/2
> ```

In `oloc`, functions are hard-coded. However, there are multiple ways to invoke them. Refer to the [Symbol Mapping Table](../项目说明/数据/符号映射表.md) for function name mappings and the [Operators](运算符.md) section for operators that can be converted into functions.  
Some functions can also be represented in operator form. See [Operators](运算符.md) for more details.

## Supported Functions

`oloc` supports both algebraic and transcendental functions.

### Algebraic Functions

`oloc` supports the following types of algebraic functions (`x`, `y` represent parameters):

#### **Exponential Function**: `pow(x, y)`

- **Description**  
  Computes `x` raised to the power of `y`.

- **Properties**  
  - *Domain*:  
    `x ∈ ℝ` and `y ∈ ℝ`
  - *Range*:  
    `ℝ`

- **Variants**  
  - Operator Form: `x^y`, `x**y`, and `√x` (square root) or `┌x`. See [Operators](运算符.md).
  - Square root function: `sqrt(x)` (equivalent to `pow(x, 1/2)`)
  - Square function: `square(x)` (equivalent to `pow(x, 2)`)
  - Cube function: `cube(x)` (equivalent to `pow(x, 3)`)
  - Reciprocal function: `reciprocal(x)` (equivalent to `pow(x, -1)`)
  - Exponential function: `exp(x)` (equivalent to `pow(e, x)`)

- **Examples**
  ```python
  oloc.calculate("pow(4,1/2)") # Output: 2; Equal: sqrt(4), x^1/2, x**1/2
  oloc.calculate("pow(2, 3)") # Output: 8
  oloc.calculate("pow(16, 1/4)") # Output: 2
  oloc.calculate("sqrt(9)") # Output: 3
  oloc.calculate("cube(-3)") # Output: -27
  oloc.calculate("reciprocal(2/3)") # Output: 3/2
  oloc.calculate("exp(2)") # Output: e^2  
  ```

#### **Modulo Function**: `mod(x, y)`

- **Description**  
  Computes the remainder of `x` divided by `y`.

- **Properties**  
  - *Domain*:  
    `x ∈ ℝ`, and `y ∈ ℝ - {0}`
  - *Range*:  
    `[0, |y|)`

- **Variants**  
  - Operator Form: `x%y`. See [Operators](运算符.md).

- **Examples**
  ```python
  oloc.calculate("mod(9, 4)")  # Output: 1; Equal: 9 % 4
  oloc.calculate("mod(-9, 4)") # Output: 3; Equal: -9 % 4
  ```

#### **Factorial Function**: `fact(x)`

- **Description**  
  Computes the factorial of `x`, which is the product of all integers from `1` to `x`.

- **Properties**  
  - *Domain*:  
    `x ∈ ℕ`
  - *Range*:  
    `ℝ - {0}`

- **Variants**  
  - Operator Form: `x!`. See [Operators](运算符.md).

- **Examples**
  ```python
  oloc.calculate("fact(5)") # Output: 120; Equal: 5!
  oloc.calculate("fact(0)") # Output: 1
  ```

#### **Absolute Value Function**: `abs(x)`

- **Description**  
  Computes the absolute value of `x`.

- **Properties**  
  - *Domain*:  
    `x ∈ ℝ`
  - *Range*:  
    `x ≥ 0`

- **Variants**  
  - Operator Form: `|x|`. See [Operators](运算符.md).

- **Examples**
  ```python
  oloc.calculate("abs(-3)") # Output: 3; Equal: |3|
  ```

#### **Sign Function**: `sign(x)`

- **Description**  
  Computes the sign of `x`, returning -1, 0, or 1:
  - If `x` is negative, returns `-1`.
  - If `x` is zero, returns `0`.
  - If `x` is positive, returns `1`.

- **Properties**  
  - *Domain*:  
    `x ∈ ℝ`
  - *Range*:  
    `{-1, 0, 1}`

- **Variants**  
  - None.

- **Examples**
  ```python
  oloc.calculate("sign(-5)")  # Output: -1
  oloc.calculate("sign(0)")   # Output: 0
  oloc.calculate("sign(5)")   # Output: 1
  ```

#### **Greatest Common Divisor (GCD)**: `gcd(x, y)`

- **Description**  
  Computes the greatest common divisor of `x` and `y`, which is the largest positive integer that divides both `x` and `y`.

- **Properties**  
  - *Domain*:  
    `x, y ∈ ℕ`
  - *Range*:  
    `ℝ - {0}`

- **Variants**  
  - None.

- **Examples**
  ```python
  oloc.calculate("gcd(12, 18)")  # Output: 6
  oloc.calculate("gcd(7, 13)")   # Output: 1
  ```

#### **Least Common Multiple (LCM)**: `lcm(x, y)`

- **Description**  
  Computes the least common multiple of `x` and `y`, which is the smallest positive integer that is divisible by both `x` and `y`.

- **Properties**  
  - *Domain*:  
    `x, y ∈ ℕ`
  - *Range*:  
    `ℝ - {0}`

- **Variants**  
  - None.

- **Examples**
  ```python
  oloc.calculate("lcm(4, 5)")   # Output: 20
  oloc.calculate("lcm(7, 9)")   # Output: 63
  ```

---

### Transcendental Functions

#### **Trigonometric Functions**

##### **Sine Function**: `sin(x)`

- **Description**: Computes the sine of `x`.

- **Examples**
  ```python
  oloc.calculate("sin(0)")          # Output: 0
  oloc.calculate("sin(π/2)")        # Output: 1
  oloc.calculate("sin(90°)")        # Output: 1
  ```

##### **Cosine Function**: `cos(x)`

- **Description**: Computes the cosine of `x`.

- **Examples**
  ```python
  oloc.calculate("cos(0)")          # Output: 1
  oloc.calculate("cos(π/2)")        # Output: 0
  oloc.calculate("cos(90°)")        # Output: 0
  ```

##### **Tangent Function**: `tan(x)`

- **Description**: Computes the tangent of `x`.

- **Examples**
  ```python
  oloc.calculate("tan(0)")          # Output: 0
  oloc.calculate("tan(π/4)")        # Output: 1
  oloc.calculate("tan(45°)")        # Output: 1
  ```

##### **Other Trigonometric Functions**

`cosec(x)`, `sec(x)`, `cot(x)` and their inverses are also supported.  

Refer to the full documentation for specific details and examples.

---

### Logarithmic Functions

#### **Logarithm Function**: `log(x, y)`

- **Description**: Computes the logarithm of `y` with base `x`.

- **Examples**
  ```python
  oloc.calculate("log(2, 8)")   # Output: 3
  oloc.calculate("lg(100)")    # Output: 2; Equal: log(10, 100)
  oloc.calculate("ln(e)")      # Output: 1; Equal: log(e, e)
  ```

---

**Next Chapter**: [Calculations, Results and Exceptions](Calculation,%20Results%20and%20Exceptions.md)  
**[Back to Table of Contents](User%20Guide%20Directory.md)**