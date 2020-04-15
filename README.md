# Quill
[![Run on Repl.it](https://repl.it/badge/github/Quill-Language/Quill)](https://repl.it/github/Quill-Language/Quill)


Quill is a statically typed, interpreted language.
That means variables are like in C, and can only have one type, in case you didn't know.
To create a variable, you must declare it and then give it a value.
For example:
```
number: a
a = 5
```
This creates a variable named a, which is a number.
Then it sets it to 5.
The available types for variables are number, string, list, class, symbol, map, and func, though more will probably be added later.
Most types, like func or class, require that you call them directly to set them up.
However, these types take what is called a block as an argument.
A block is just a program inside two curly brackets.
However, typing stuff like
```
func({
  <code>
});
```
is ugly and cumbersome.
Thus, there is syntatic sugar:
```
func() {
  <code>
}
```
is the same as the above.
Each block has it's own local scope, so you don't have to worry about interfering with global variables.
Functions can take parameters like so:
```
func(number: param1, string: param2)
```
Note that the last argument to func should be the return type.
So the correct way to declare the above function would be:
```
func(number: param1, string: param2, number)
```
if it returned a number.
Classes are similar: you just provide a block and treat it like a program.
All variables inside the block will be accessible outside.
Here is a minimal example:
```
class: myclass
myclass = class() {
  number: a
  a = 5
}
myclass: myobj
myobj = myclass()
print(myobj.a)
```
This will print out 5.
Loops and if statements do not have their own constructs; they are done using functions.
if takes two parameters: a value and a block.
You would use it like so:
```
if(a) {
  <code>
}
```
There is no built-in for loop. However, the range class has a method `.each`, that given a declaration and a block, will execute that block over itself.
For example:
```
range(10).each(number: i) {
  print(i)
}
```
Please note that Quill is in active beta. New features will be added often. For more info, check out
[the website](https://quill-language.github.io).
