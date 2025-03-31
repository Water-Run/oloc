# Numbers  

The core of `oloc` is **fractional number operations**, ensuring maximum precision. `oloc` supports operations covering the set of real numbers, including mixed operations with rational and irrational numbers.  
Adding a `-` (minus sign) before a number indicates it is negative. Similarly, a `+` can be explicitly added to declare a number as positive—though this is largely unnecessary.  

## Rational Numbers  

**Rational numbers are the core numeric type in `oloc`**. Any rational number is converted into its proper fractional form during lexical analysis. However, the input formats are diverse.  

### Integers  

**Integers are numbers composed of Arabic numerals with an optional `+` or `-` at the beginning.**  
Here are some examples of integers:  
`0`, `1`, `-1`, `15`, `+100`  

### Decimals  

**Decimals are numbers consisting of an integer part and a fractional part**, separated by a `.`. Decimals can also include an optional `-` at the beginning.  

Examples of decimals:  
`0.25`, `3.14`, `10500.12345`, `-0.0001`  

#### Repeating Decimals  

**`oloc` also supports repeating decimals.** Use 3 to 6 `.` at the end of a decimal to indicate it is repeating, e.g., `2.3...`, `123.123......`.  

> `oloc` automatically detects repeating patterns and converts them into fractional form.  

You can also explicitly specify the repeating part by adding it after the decimal number using a `:`. For example, `1.2:3` is equivalent to `1.233...`.  

> When the repeating decimal starts immediately after the decimal point, it must be declared using multiple `.` at the end.  

### Number Separators  

For large numbers, reading can sometimes be challenging. For example, the number `10000000` (ten million) can be hard to interpret. One way to represent it is using scientific notation, like `1*10^7`.  
`oloc` also supports **number separators**. You can use `,`, such as in `10,000,000`. The spacing of the separators is unrestricted in `oloc`.  

> **When using number separators, the following constraints must be followed:**  
> - Number separators **must only be used with rational numbers**.  
> - **Number separators cannot appear at the beginning or end**, e.g., `,100000,`.  
> - **Consecutive separators are not allowed**, e.g., `2,,000`.  
> - **When using number separators in function arguments, the arguments must be separated by `;` instead of `,`** to avoid parsing errors.  
> - **For single-argument functions, number separators cannot be used.**  

> Note: Superscript notation for exponents (e.g., `³`) cannot include number separators or spaces.  

Another common way to represent large numbers is to use the `_` symbol as a number separator. This symbol is directly removed during preprocessing, so it has no restrictions on its usage.  
**When using number separators in functions, it is recommended to use `_`.**  

### Fractions  

**Fractions consist of an integer numerator and a denominator (non-zero).** For readability, it is generally recommended to place the `-` sign before the numerator to indicate negativity. Here are some examples of fractions:  
`1/2`, `0/10`, `-314/222`, `+50/-100`.  
During computation, `oloc` automatically reduces fractions to their simplest form (proper fractions or integers, if possible). For example, `-2/4` is simplified to `-1/2`.  

> **`oloc` also supports mixed fractions.** Use an integer followed by the `\` symbol and a fraction, e.g., `3\1/2` represents `3+1/2`, which equals `7/2`.  
> > In `oloc`, `\` is equivalent to `+`.  

#### Percent Format  

`oloc` supports percentage-format numbers. Add `%` at the end of an **integer or finite decimal** to represent a percentage.  

> **When using percentage format, you cannot omit the multiplication operator, or it will be interpreted as a modulo operation.** For example, `50%(0.1+0.2)` will be interpreted as `0.5%0.3`.  
> > Only when `%` is directly followed by arithmetic operators (mapped as `+`, `-`, `*`, `/`, `^`) will it be parsed as a percentage.  

## Irrational Numbers  

**`oloc` supports irrational numbers.** Irrational numbers can interact with rational numbers, and **if the result of a calculation includes irrational numbers, they will be preserved** (e.g., `1+π`).  
Some functions may produce results that are irrational numbers. These **irrational results are also preserved** (e.g., `√1/2`).  

### Built-in Irrational Numbers  

`oloc` natively supports irrational numbers like **π (pi)** and **e (Euler's number)**.  
`π` can be written as `p` or `pi`, and `e` can be written as `e`, in any case (uppercase or lowercase).  

> When **converting to floating-point (`float()`)**, built-in irrational numbers are rounded to 7 decimal places by default. For example, the default conversion of `π` is `3.1415926`. You can specify the number of decimal places by appending it after the irrational number followed by a `?`. For example, `p2?` converts to `3.14`.  
> > This is essentially a feature of irrational number parameters. For built-in irrational numbers, only the integer part of the parameter is parsed.  
> 
> > The default number of decimal places can be changed—see the [Calculation and Exceptions](Calculation Results and Exceptions.md) section on `retain_decimal_places`.  
>
> For results that may contain irrational numbers (e.g., functions), the same parameter syntax is supported. For example, `pow(2,1/2)?3` specifies the result (if irrational) should retain 3 decimal places.  
> > The same applies to operators used as functions, but to avoid parsing errors, parentheses should enclose expressions using `?`.  

### Custom Irrational Numbers  

In addition to built-in irrational numbers, `oloc` also supports custom irrational numbers.  
These irrational numbers can be used as variables to simplify expressions using `oloc`.  

#### Short Custom Irrational Numbers  

**In fact, `oloc` treats any single non-reserved character as an irrational number**, including `x`, `y`, `z`, and even Chinese characters. In `oloc`, these are referred to as **short custom irrational numbers**.  

> Use the `is_preserved` method to check if a string is a reserved word in `oloc`.  

> This feature allows you to represent unknown variables and simplify expressions. For example, `oloc.calculation('3x/5xy')` results in `3/5y`.  

**Some recommended custom short irrational numbers include:**  

- `x`  
- `y`  
- `z`  
- `a`  
- `b`  
- `c`  
- `i`  
- `j`  
- `k`  

#### Long Custom Irrational Numbers  

Custom irrational numbers can also consist of multiple characters by enclosing them in `< >`. These are referred to as **long custom irrational numbers**. The content inside `< >` is ignored during parsing (including the `< >` itself). For example, `<IR>`, `<An irrational number>`, and `<无理数>` are all valid long custom irrational numbers.  

> Long custom irrational numbers that start with `__reserved` (e.g., `<__reserved_param1__>`) are reserved words. Avoid using such names.  

#### Irrational Number Parameters  

Custom irrational numbers used in calculations may pose certain issues:  

- Some functions may require the sign (positive or negative) of the irrational number.  
- Converting to floating-point requires a target value for the irrational number.  

**Irrational number parameters** allow you to specify conversion values or signs for custom irrational numbers. Add the value or sign (must be a finite decimal or integer, i.e., a float) between the irrational number and `?`. For example, `X-?` specifies the number is negative, and `<num>1.23?` specifies the conversion value as `1.23`.  

> Examples:  
> ```python
> import oloc
> oloc.calculation('|x-?|') # Output: -x
> result = oloc.calculation('<num>1/2?') # Output: <num>1/2?
> print(float(result)) # Output: 1/2
> ```
> > Add these parameters to avoid exceptions when calling absolute value functions or converting to floating-point.  

> An example expression containing various types of numbers:  
> `1+-2.5+2/3+<一个无理数>-2\1/3+pi+x+2.34...-0.5:5+(<number>+i/3i/500)` — this includes *integers, finite decimals, fractions, custom short irrational numbers, mixed fractions, built-in irrational numbers, custom short irrational numbers, repeating decimals, explicitly defined repeating decimals, and a mixed number*.  

---  
***Next Chapter: [Operators](Operators.md)***  
*[Return to Directory](User Guide Directory.md)*
