# Calculation, Results and Exceptions

This chapter introduces how to use `oloc` for calculation operations, and how to obtain corresponding results and exceptions.

## Calculation

> `oloc` currently only supports decimal calculations

**Calculations in `oloc` use the `calculate()` function**.
`calculate()` accepts **two parameters**:

- `expression`: `str` **The expression to be calculated**
- `time_limit`: `float` **Calculation time limit** (seconds). The default value is `-1`, **modifications need to be explicitly specified**. Setting the time limit to any negative number disables it, and `oloc` will never throw a calculation timeout exception

For an empty calculation expression, `oloc`'s default result is `0`.

> **Since the calculation timer significantly affects performance (about 0.25s on the tested device), the default value of `time_limit` is `-1`, meaning this feature is not enabled by default. It is only recommended when the result may be particularly large or when there are strict time constraints on generating results**

For more information about `time_limit` and the specific implementation of the calculation flow, see [Project Description](../项目说明/项目说明梗概.md).

*Example:*

```python
import oloc

oloc.calculate('1+2+3') # Output: 6 
oloc.calculate('1/2^2-3/4') # Output: -1/2
oloc.calculate('100!', time_limit=1) # except OlocTimeOutError 
```

## Comments
`oloc` supports adding comments to expressions. This is a useful feature when you have a large number of expressions to share.
Comments will be removed during preprocessing.

> To get comment information in the result: read the original expression stored in the `expression` field

### Concluding Comments
As the name suggests, **concluding comments can only be added to the end of an expression**. Use the `@` symbol to declare, and the content after it is the comment.
Example:  
`1+2+3 @This is a concluding note.`

### Free Comments
Unlike concluding comments, **free comments can appear anywhere in the expression**. Free comments are **wrapped in two `#` symbols**.
Example:
`1/2-#A free comment located before the mixed fraction.#4_1/2`.
There can be any number of free comments in an expression.

## Results

**The output of the calculation function `calculate()` is an instance of the `OlocResult` class**.
In most cases, you can use `OlocResult` as a string; of course, you can also explicitly convert it using `str`.

*Example:*
```python
import oloc

result = oloc.calculate('1+1') # result is an instance of OlocResult
print(result) # Output: 2
result = str(result) # Explicit conversion  
```

> `OlocResult` is read-only: once created, it cannot be modified

### Getting Results

An `OlocResult` has two attributes:

- `result`: `list[str]` A list of strings containing step-by-step results from the end of preprocessing. Converting `OlocResult` to `str` is essentially getting the last item in the `result` list
- `expression`: `str` The original expression for calculation, including comments and other information

By accessing these attributes, you can get the results you want.

> The attributes in `OlocResult` are private, including the original expression (`_expression`) and the result list (`_result`). The attributes `expression` and `result` are implemented through `@property`.

### Converting to Numeric Values

**Use `float` to convert `OlocResult` to a floating-point value**.

> The number of decimal places to keep when converting irrational numbers is stored in the key `retain_decimal_places` in `olocconfig.ini`. Without modification, this value is 7

When converting custom irrational numbers to floating-point, you need to ensure that the irrational number has declared a conversion value (using `?`, see [Numbers](Numbers.md), the same symbol is also used to manually set the conversion precision of native irrational numbers).
**`int` conversion results are based on floating-point conversion**.

*Example:*
```python
import oloc

num1 = oloc.calculate('π?2')
print(float(num1)) # 3.14
print(int(num1)) # 3
```  

> Due to the imprecision of floating-point numbers, after conversion to numeric values, `oloc` will lose its original fraction-based result precision properties

#### Converting to Python Native `Fraction`
There is another way to better protect the precision of `oloc` results: **convert to Python's native fraction format `Fraction`**.
Just call the `get_fractions()` method provided by `OlocResult`. It returns a value of type `fractions`.

> Before using, remember to import Python's native fraction format with `from fractions import Fraction`

*Example:*
```python
import oloc
from fractions import Fraction

num1 = oloc.calculate('3/4')
print(num1.get_fractions().numerator) # 3
print(num1.get_fractions().denominator) # 4
```

> Since `fractions` is not compatible with irrational numbers, the handling of irrational numbers is consistent with the conversion to floating-point numbers

### Summary

For the `calculate()` calculation result `OlocResult`, the following uses are summarized:

- Get the result: call directly (in most cases it will be converted to a string) or explicitly convert using `str`, or access the last item in the `result` list
- Get the calculation process: access the `result` attribute
- Get the original expression (including comments, etc.): access the `expression` attribute
- Convert to floating-point: use `float` for type conversion
- Convert to integer: use `int` for type conversion
- Convert to native fraction: use the `get_fractions()` method

## Output Filter

For `oloc` results, output filtering is performed to achieve more aesthetically pleasing formatted output.
**The output filter function is optional**: see [Formatted Output Filter Configuration Table](../项目说明/数据/格式化输出过滤器配置表.md).
The main functions include:
1. Adding spaces between calculation units
2. Adding number separators, scientific notation, etc. for large numbers
3. Converting functions that can be represented as operators to operator form
4. Other unified style settings

> The content of each step in the final result will go through the formatted output filter (including step-by-step calculation results)

## Exceptions

In `oloc`, all exceptions inherit from the abstract base class `OlocException`.

> Due to serialization issues, you need to use `except Exception` to catch exceptions

### Exception Format

For `OlocException`, it has the following general format:

```plaintext
[Oloc Exception Name]: [Oloc Exception Content]
[Expression]
[Exception Location Marker]
Hint: [Hint]  
--------------------------------------------------------------------------------------------
Try visit https://github.com/Water-Run/oloc for more information on oloc related tutorials :)
```

- **Oloc Exception Name**: The class name of the exception
- **Oloc Exception Content**: Description of the exception content. For some exceptions, the content includes variables. For example, the timeout exception will indicate the set timeout duration
- **Expression**: The expression that caused the exception. For calculation exceptions, it will be formatted by the output filter
- **Exception Location Marker**: The `^` symbol marks the location that caused the exception. Depending on the exception, `^` may point to one, multiple characters, or the entire expression
> Due to terminal output limitations, the exception location marker may not be precise for non-ASCII characters
- **Hint**: Hint information for resolving the exception
- **Oloc GitHub Tutorial Link**: At the end of the exception information, includes a dividing line composed of `-`, the `github` link for `oloc`, and a `:)`
> The `github` part is hidden in the following part examples

*Example:*  
```plaintext
OlocCalculationError: Divide-by-zero detected in the computational expression `5/0`
5/0
^^^
Hint: The divisor or denominator may not be zero. Check the expression.
--------------------------------------------------------------------------------------------
Try visit https://github.com/Water-Run/oloc for more information on oloc related tutorials :)
```

### Exception Types

oloc provides the following main exception types:

1. **OlocSyntaxError**: Syntax errors, including issues with comments, irrational number format, bracket matching, equal sign position, etc.
2. **OlocValueError**: Invalid values or format errors, including invalid number formats, operators, functions, etc.
3. **OlocCalculationError**: Calculation errors, such as division by zero
4. **OlocTimeOutError**: Calculation timeout

#### Syntax Error (OlocSyntaxError)

Thrown when the syntax format of the expression is incorrect. Includes the following common types:

- **Comment-related**: Comment symbols do not match
  ```plaintext
  OlocSyntaxError: Mismatch '#' detected
  123#unclosed+456
     ^
  Hint: The content of free comments should be wrapped in a before and after '#'.
  ```

- **Irrational Number Format**: Irrational number declaration format error
  ```plaintext
  OlocSyntaxError: Mismatch '>' detected
  <custom_irrational
  ^                
  Hint: When declaring a custom long irrational number, '>' must match '<'. Check your expressions.
  ```

- **Bracket Matching**: Brackets do not match or level errors
  ```plaintext
  OlocSyntaxError: Mismatch `(` detected
  (1+2
  ^   
  Hint: The left bracket must be matched by an identical right bracket. Check your expressions.
  ```

- **Number Separators**: Number separators used incorrectly
  ```plaintext
  OlocSyntaxError: Invalid numeric separator detected
  π,10,,000,
   ^  ^^   ^
  Hint: Ensure commas are used correctly as numeric separators in rational numbers. If you expect `,` to be a function parameter, check that the function name is a legal function name in oloc. Commas must not appear at the start, end, or consecutively. When using numeric separators in a function, only `;` can be used to separate the arguments of the function.
  ```

#### Value Error (OlocValueError)

Thrown when Token self-check fails or the format of the value is incorrect:

- **Invalid Token**: Token is of unknown type
  ```plaintext
  OlocValueError: Token that Tokenizer could not parse `@`
  1+@2
    ^
  Hint: Check the documentation for instructions and check the expression.
  ```

- **Invalid Number Format**: Number format does not comply with regulations
  ```plaintext
  OlocValueError: Invalid infinite-decimal number `345......`
  345......
  ^^^^^^^^^
  Hint: An infinite cyclic decimal must be followed by a finite cyclic decimal ending in 3-6 ` . ` or `:` followed by an integer. e.g. 1.23..., 2.34......, 10.1:2. The declaration `:` cannot be used when the first decimal place is a round-robin place.
  ```

#### Calculation Error (OlocCalculationError)

When a mathematical error is encountered during calculation:

- **Division by Zero Error**: Division by zero occurs in the calculation
  ```plaintext
  OlocCalculationError: Divide-by-zero detected in the computational expression `5/0`
  5/0
  ^^^
  Hint: The divisor or denominator may not be zero. Check the expression.
  ```

#### Timeout Error (OlocTimeOutError)

When the calculation time exceeds the set limit:

- **Calculation Timeout**: Calculation time exceeds the limit
  ```plaintext
  OlocTimeOutError: Calculation time exceeds the set maximum time of 1.0s
  100!
  ^^^^   
  Hint: Check your expression or modify time_limit to a larger value.
  ```

---  
***Next chapter: [Scientific Calculator CLI](Scientific%20Calculator%20CLI.md)***  
*[Return to Directory](User%20Guide%20Directory.md)*
