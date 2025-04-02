# Installation and Basic Usage  

## Installation  

`oloc` is available on PyPi. Therefore, you can install `oloc` using the command:  

```bash
pip install oloc
```  

Then, import `oloc` into your project:  

```python
import oloc
```

## Basic Usage  

**Perform calculations using `oloc.calculate()`**. Pass your expression as the argument to the function.  
For basic usage, you can treat the result as a string and convert it to `float` or `int` if needed.  

```python
import oloc
oloc.calculate("1+1") # Output: 2
oloc.calculate("-1/2+1/3") # Output: -1/6
oloc.calculate("sqrt(1/4)-(1/√2)^2") # Output: 0
```

If you want to access step-by-step calculation results, refer to the `result` attribute of the object returned by `oloc.calculate()`. It is a list of strings that contains the step-by-step results in sequential order.  

> Before diving into the detailed tutorial, feel free to experiment with it intuitively.  

### Command-Line Program

`cli` is the command-line terminal program provided by `oloc_release`:

*Startup:*

```python
import oloc_release
oloc_release.cli()
```

After starting, enter `:help` to get the usage guide.

### GUI Program

`gui` is the graphical program provided by `oloc_release`, implemented with `tkinter`:

*Startup:*

```python
import oloc_release
oloc_release.gui()
```

After starting, click the `help` tab at the top to access the usage guide.

---  
***Next Chapter: [Numbers](Numbers.md)***  
*[Return to Directory](User%20Guide%20Directory.md)*