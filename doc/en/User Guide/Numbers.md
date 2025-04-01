# Numbers

The core of `oloc` is **arithmetic with numbers in fractional form** to ensure maximum precision. `oloc` supports operations across the entire set of real numbers, including mixed operations between rational and irrational numbers.
Adding a `-` (minus sign) before a number indicates that the number is negative. Similarly, you can add a `+` to explicitly declare a number as positive—although this has little practical significance.

## Rational Numbers

**Rational numbers are the core number type in `oloc`**. Any rational number is converted to a proper fraction form (specifically, formed by integers and a fraction line) during lexical analysis of the calculation. However, the supported input types are diverse.

### Integers

**Integers are numbers composed solely of Arabic numerals**.
Here are some examples of integers:
`0`, `1`, `-1`, `15`, `+100`

### Decimals

**Decimals are numbers consisting of integer and decimal parts**. The integer and decimal parts are separated by `.`.

Some examples of decimals:
`0.25`, `3.14`, `10500.12345`, `-0.0001`

#### Infinitely Repeating Decimals

**`oloc` also supports infinitely repeating decimals**. Use 3 to 6 `.` at the end of a decimal to indicate that it is an infinitely repeating decimal. For example, `2.3...`, `123.123......`.

> `oloc` automatically scans for the most recent repeating structure and converts it to fractional form

You can also explicitly specify the repeating part: at the end of the decimal, add the decimal part that needs to repeat, starting with `:`. For example, `1.2:3` is equivalent to `1.233...`.

> When an infinitely repeating decimal begins repeating from the first decimal place, it can only be declared using multiple `.` at the end

### Number Separators

For larger numbers, reading can be challenging. For example, the number `10000000` (one hundred million) is quite large. One approach is to use scientific notation: for instance, representing the above number as `1*10^7`.
`oloc` also supports the use of **number separators**. You can use `,`, as in `10,000,000`. `oloc` does not impose restrictions on the specific intervals.

> **When using number separators, the following restrictions must be observed**:
> - Number separators **must be used in rational numbers**
> - **Number separators cannot appear at the beginning or end**. For example, `,100000,`
> - **Number separators cannot appear consecutively**. For example, `2,,000`
> - **When function parameters use number separators, function parameter separation must use `;` rather than `,`** to avoid parsing errors
> - **For functions with only one parameter, number separators cannot be used**

> Note: Superscript exponents (such as `³`) cannot contain number separators or spaces between them

Another common approach is to use the symbol `_` as a number separator. This symbol is directly eliminated during the preprocessing stage, so there are no restrictions on its use.
**When using number separators in functions, it is recommended to use `_`**.

### Fractions

**Fractions include a numerator and denominator in integer form (the denominator cannot be 0)**. For the sign of a fraction, it is generally recommended to place the `-` before the numerator for better readability. Here are some examples of fractions:
`1/2`, `0/10`, `-314/222`, `+50/-100`
In calculations, `oloc` will automatically convert fractions to their simplest form, i.e., proper fractions or integers (if possible). For example, `-2/4` will be simplified to `-1/2`.

> **`oloc` also supports mixed fractions**. Use an integer followed by the symbol ` \ ` and a fraction. For example, `3\1/2` represents `3+1/2`, which is `7/2`
> > In fact, in `oloc`, ` \ ` is equivalent to `+`

#### Percentage Format

`oloc` also supports data in percentage format. Add `%` to the end of an **integer or finite decimal**.

> **When using percentage format, you cannot omit the multiplication sign, otherwise it will be interpreted as modulo**. For example, `50%(0.1+0.2)` will be interpreted as `0.5%0.3`
> > Only when `%` is immediately followed by arithmetic operators (after mapping) `+`, `-`, `*`, `/`, `^` will it be parsed as a percentage decimal

## Irrational Numbers

**`oloc` supports irrational numbers**. Operations between irrational numbers are supported, and **if the final calculation result includes irrational numbers, they will be preserved accordingly**. For example, `1+π`
Some function results may be irrational numbers. For these **irrational numbers in results, they will also be preserved accordingly**. For example, `√1/2`.

### Native Irrational Numbers

The irrational numbers natively supported by `oloc` include **pi `π`** and **Euler's number `𝑒`**.
`π` can be written as `p` or `pi`, and `𝑒` can be written as `e`, in any case variant.

> When **converting to floating point (`float()`), native irrational numbers default to 7 decimal places**. For example, the default conversion of `π` is `3.1415926`. You can also specify the number of decimal places to keep by entering the desired number before `?` after the irrational number. For example, `p2?` when converted will have a value of `3.14`
> > This is actually the irrational number parameter mentioned below. The irrational number parameter for native irrational numbers can only be a positive integer
>
> > The default number of decimal places can be changed: see the section on `retain_decimal_places` in [Calculation and Exceptions](Calculation%20Results%20and%20Exceptions.md)
>
> For values that may result in irrational numbers (such as functions), the same irrational number parameter is supported. For example, `pow(2,1/2)?3` indicates that the conversion value of this function result (if the result has irrational numbers) will keep 3 decimal places
> > This is also true for functions using operators converted to functions. However, to avoid unexpected parsing errors, when using `?`, it is necessary to add parentheses to the corresponding expression

### Custom Irrational Numbers

In addition to native irrational numbers, `oloc` also supports custom irrational numbers.
These irrational numbers can be used as unknown quantities to utilize `oloc`'s expression simplification functionality.

#### Short Custom Irrational Numbers

In fact, **for any single character that is not a reserved word, `oloc` will treat it as an irrational number**, including `x`, `y`, `z`, `值`, etc. In `oloc`, we call these **short custom irrational numbers**.

> You can use the `is_preserved` method to check if a current string is a reserved word in `oloc`

> Using this feature appropriately allows you to express unknown quantities through `oloc` and perform simplification operations. For example, the result of `oloc.calculation('3x/5xy')` is `3/5y`

**Here are some recommended choices for custom short irrational numbers:**

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

Custom irrational numbers can also support multiple words: use `<` `>` to enclose them, representing **long custom irrational numbers**. The content enclosed in `<>` will be ignored during parsing (including `<>` itself). For example, `<IR>`, `<An irrational number>`, `<无理数>` are all valid long custom irrational numbers.

> Long custom irrational numbers with content starting with `__reserved` are reserved words (such as `<__reserved_param1__>`). You should not use such names

#### Irrational Number Parameters

There are some issues with custom irrational numbers participating in calculations:

- Some functions need to know positivity/negativity to proceed
- When converting to floating point, a target conversion value needs to exist

**Irrational number parameters can add conversion values or positivity/negativity to custom irrational numbers**: add a value (must be a finite decimal or integer (can be viewed as .0), i.e., a floating point number) or a sign between the end of the irrational number (for long irrational numbers, after `>`) and `?`. For example, `X-?` indicates that the irrational number is negative, `<num>1.23?` indicates that the conversion value of the irrational number is `1.23`.

> Example:
> ```python
> import oloc
> oloc.calculation('|x-?|') # Output: -x
> result = oloc.calculation('<num>1/2?') # Output: <num>1/2?
> print(float(result)) # Output: 1/2
> ```
> > When calling the absolute value function or performing floating point conversion, to avoid exceptions, perform the corresponding addition operation

> An expression containing various types of numbers: `1+-2.5+2/3+<一个无理数>-2\1/3+pi+x+2.34...-0.5:5+(<number>+i/3i/500)`, in sequence: *integer, finite decimal, fraction, custom long irrational number, mixed fraction, native irrational number, custom short irrational number, infinitely repeating decimal, infinitely repeating decimal (explicitly specified), and a mixed number*

---
***Next chapter: [Operators](Operators.md)***  
*[Return to Directory](User%20Guide%20Directory.md)*
