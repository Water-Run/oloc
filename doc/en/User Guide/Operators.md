# Operators

Symbols that represent calculation logic are called operators.
**Symbols can have many different representations**, which will be uniformly converted to the same form during the preprocessing stage of calculation. See [Symbol Mapping Table](../项目说明/数据/符号映射表.md).
> Converted operators all contain only one character

## Arithmetic Operators

Arithmetic operators express operations on calculation units.

### Unary Operators

Unary operators are arithmetic operators that target a single calculation unit. These include:

| Name | Symbol | Description | Example |
|------|--------|-------------|---------|
| Positive Sign | `+` | Placed in front of a calculation unit to indicate a positive calculation unit | `+3` |
| Negative Sign | `-` | Placed in front of a calculation unit to indicate a negative calculation unit | `-2` |
| Square Root | `√` or `┌` | Placed before and after a calculation unit to take the square root of a calculation unit. Essentially the square root function `sqrt` | `√2` |
| Absolute Value | `\|` | Placed before and after a number to take the absolute value of a calculation unit. Essentially the absolute value function `abs` | `\|x\|` |
| Factorial | `!` | Placed after a calculation unit to calculate the factorial of a calculation unit. Essentially the function `fact` | `100!` |
| Degree | `°` or `deg` or `degree` or `^o` | Placed after a calculation unit to indicate that a calculation unit is in degrees. Essentially the degree to radian conversion function `rad` | `45°` |

### Binary Operators

Binary operators are arithmetic operators that target two calculation units. These include:

| Name | Symbol | Description | Example |
|------|--------|-------------|---------|
| Addition | `+` | Indicates addition between calculation units | `1+1` |
| Subtraction | `-` | Indicates subtraction between calculation units | `3-4` |
| Multiplication | `*` or `·` | Indicates multiplication between calculation units | `5*6` |
| Division | `/` or `÷` | Indicates division between calculation units | `3/4` |
| Exponentiation | `^` or `**` | Indicates the first calculation unit raised to the power of the second calculation unit. Essentially the function `pow` | `2^3` |
| Modulo | `%` | Indicates the remainder of the first calculation unit divided by the second calculation unit. Essentially the function `mod` | `5%1` |

*Notes:*

1. The fraction line `/` and division symbol are equivalent in meaning.
2. In some cases, the multiplication symbol can be omitted:
   - When a number is connected to parentheses. For example, `3*(2+3)` can be abbreviated as `3(2+3)`
   - When a number is connected to an irrational number. For example, `2*π/3` can be abbreviated as `2π/3`
   - Mixed forms of the above. For example, `3((-2/3x)y)`
3. When the exponent is an integer, it can be written in subscript form, such as `3²`

## Grouping Operators

Parentheses are used to express **parts of the operation that have priority in calculation**. `(` and `)` are the main symbols. The content within parentheses will be treated as a whole and calculated according to parentheses priority.
Some examples of using parentheses:
```python
oloc.calculate("3/(-1+2)") # Output: 3
oloc.calculate("2*(3+4)") # Output: 14
oloc.calculate("5/(1+1)*(2-1)") # Output: 5/2
```
Expressions can use only parentheses symbols `(` and `)`. `oloc` also supports explicitly distinguishing parentheses levels. From small to large, they are square brackets `[` and `]` and curly braces `{` and `}`.
When **explicitly distinguishing parentheses levels, lower-level parentheses must be deeper than higher-level parentheses**. For example, the expression `3+(3/4+[5/6])` will throw an exception. At the same time, writing higher-level parentheses must ensure that lower-level parentheses already exist. For example, `2+{3*[4+1]}` will also throw an exception.
**`oloc` does not restrict the same level of parentheses from appearing repeatedly at different levels**. For example, `[[2/3π+1]*x]-[sin(π)*(2^1/2-1)]` is a valid expression.

> When using parentheses, remember to ensure correct opening and closing

## Operator Precedence

In `oloc`, operator precedence is set as follows:

1. Grouping operators have the highest precedence. The most deeply nested grouping operators have the highest precedence
2. Unary operators take precedence over binary operators
3. Among binary operators, operators that can be converted to functions take precedence over multiplication/division, and multiplication/division take precedence over addition/subtraction
4. Based on the above conditions, the left side takes precedence over the right side (calculation proceeds from left to right)

*Note*:

When `+` and `-` are used as unary operators (i.e., to indicate positive or negative signs), they essentially implicitly add a `0` before the calculation unit, so they are essentially still binary operators and follow binary operator precedence.

## Other Symbols with No Practical Significance

The following symbols have no practical significance in `oloc`. You can write them in your expressions without affecting the calculation.
These include:
- Spaces
- `rad` or `radians`. If not specified, `oloc` uses radians by default, so this operator will be discarded
- `_`. This symbol is used as a custom separator (e.g., to distinguish irrational numbers) and is not restricted. Therefore, note that `x_y` and `xy` are equivalent
- `=`. You can explicitly add an equal sign to an expression. However, you can only add it at the end, otherwise an exception will be thrown

---
***Next chapter: [Functions](Functions.md)***  
*[Return to Directory](User%20Guide%20Directory.md)*
