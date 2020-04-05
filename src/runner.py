import data
import errors
import parse

# Very long lambda function that converts a type to a method so code can use it.
# We want all types to be available as both objects and as methods.
# That way, we can do stuff like number: x and x = number(5), without having two seperate methods.
# This function returns a method object that, when given no arguments, returns the type, and
# otherwise creates an object.
type_method = lambda type, *other: data.Method(lambda *args: type if not args or len(args) < len(other) else type(*other, *args))

# This is a dictionary of all the names to try to find the method to call for a particular operator.
# For each name, the code will search for both the name and the name prefixed with an underscore.
op_names = {
    '+':['add'],
    '=':['eq'],
	'index':['index']
}

def ref(obj):
    # Given a value, this function will convert any references it is passed to their values.
	if isinstance(obj, data.Reference):
		return obj.to
	return obj

def call(obj, *args):
    # Attempts to call an object.
	obj = ref(obj) # Make sure we aren't calling a reference
	if get(obj, 'call', error=False): # Check for call method
		func = get(obj, 'call')
		if isinstance(obj, data.Method): # If we find it, call that
			return func(*args)
		return get(obj, 'call').attrs['_call'](*args)
	elif get(obj, '_call', error=False): # Check for _call method
		func = get(obj, '_call')
		if isinstance(obj, data.Method): # If we find it, call that
			return func(*args)
		return get(obj, '_call').attrs['_call'](*args)
	else:
		errors.error(f'Object {obj.string().val} is not callable') # Otherwise, the object is not callable


def get(obj, attr, error=True):
    # Gets an attribute of an object.
	obj = ref(obj) # Make sure we don't have a reference
	attr = data.Symbol(attr) # Convert the attribute to a symbol
	if 'get' in obj.attrs: # If the object has a get method, call that
		return call(obj.attrs['get'], attr)
	elif '_get' in obj.attrs: # If it has a _get method, call that
		return call(obj.attrs['_get'], attr)
	elif attr.val in obj.attrs: # Otherwise, check in the object attributes
		return obj.attrs[attr.val]
	else:
		if error:
			errors.error(f'Cannot get attribute of object {obj.string().val}') # If error is True, throw an error
		else:
			return # Otherwise, return None

def op(obj, op):
    # Gets the method for an operator of an object.
	obj = ref(obj) # Again, make sure we don't have a reference
	if op.val not in obj.attrs: # Only go through op_names if the object doesn't already have the operator as an attribute
		if op.val in op_names: # Check if it's in op_names
			for name in op_names[op.val]: # Iterate over every name, usually just one
				if get(obj, name, error=False): # Check for the name
					return get(obj, data.Symbol(name))
				elif get(obj, '_' + name, error=False): # Check for the name prefixed with an underscore
					return get(obj, data.Symbol('_' + name))
				else: # If it doesn't have either of those, throw an error
					errors.error(f'{obj.string().val} does not have operator {op.string().val}')
		else:
			return get(obj, data.Symbol(op)) # Throw an error otherwise
    return obj.attrs[op.val]

def get_name(name, scope):
    # Given a scope, splits a name into parts seperated by dots.
	name = name.split('.') # Split the name
	while name: # Iterate over every part of the name
		part = name.pop(0) # Get one part of the name
		old = scope # Store the old scope
		scope = get(scope, data.Symbol(part)) # Get the next scope
		if not scope:
			errors.error(f'Object {old.string().val} has no attribute {part}') # Throw an error if the attribute doesn't exist
	return scope

def expr(val, scope):
    # Evaluates one node in the AST.
	if val.type == 'string': # If it is a string, return that
	    return data.String(val.val[0])
	elif val.type == 'number': # If it is a number, return that
	    return data.Number(val.val[0])
	elif val.type == 'decl': # If it is a declaration, declare it
		t = call(get_name(val.val[0], scope)) # Get the type, and call it, given us the type object
		if t == data.Number:
			default = data.Number(0) # The default value for a number is 0
		elif t == data.String:
			default = data.String('') # The default value for a string is the empty string
		elif t == data.Func:
            # The default value of a function is an empty AST
			default = data.Func(scope, data.Block(Program(parse.Node('program'))))
			default.val.val.globals = scope
		elif t == data.Class:
            # The default value for a class is the same as for functions
			default = data.Class(scope, data.Block(Program(parse.Node('program'))))
			default.val.val.globals = scope
		elif t == data.List:
            # The default value for a list is empty
			default = data.List(data.Type)
		else:
            # Otherwise, just create a type object
			default = data.Type()
		scope.set(data.Symbol(val.val[1]), default) # Set the name to the default value
	elif val.type == 'name': # If it is a name, simply get the value of the name
		return get_name(val.val[0], scope)
	elif val.type == 'call': # If it is a function call, evaluate that
		func = expr(val.val[0], scope) # Get the function
		args = []
		for arg in val.val[1].val: # Create the list of arguments
			if arg.type == 'decl': # Don't evaluate arguments that are declarations
				args.append(arg)
			else: # Evaluate all other arguments
				args.append(expr(arg, scope))
		return call(func, *args) # Call the function
	elif val.type == 'op': # If it is an operator, we need to call op
		a = expr(val.val[0], scope) # Get the left-hand side
		func = op(a, data.Symbol(val.val[1])) # Get the method to call
		return call(func, expr(val.val[2], scope)) # Call the left-hand side with the right one
	elif val.type == 'block': # If it is a block, create a new Program
		program = Program(val.val[0]) # Create the object
		program.globals = scope # Set the scope
		return data.Block(program) # Return a block
	elif val.type == 'array': # If it  is a list literal, build a list
		array = []
		for item in val.val[0].val:
			array.append(expr(item, scope)) # Evaluate each item in turn
		return data.List(type(array[0]), *array) # Create an array
	elif val.type == 'index': # If it is an indexing expression, simply call the index operator
		index = op(expr(val.val[0], scope), data.Symbol('index'))
		return call(index, expr(val.val[1], scope))
	elif val.type == 'child': # If it is a child expression (a.b), simply call the get method of the parent
		return get(expr(val.val[0], scope), val.val[1])

class Program():
    # The actual program object. Stores the AST and the global scope.
	def __init__(self, ast):
		self.ast = ast
		self.globals = data.Map(data.Symbol, data.Type) # Set up globals to map symbols to anything
		self.globals.set(data.Symbol('import'), data.Method(self._import)) # Set up all the builtins
		self.globals.set(data.Symbol('if'), data.Method(self._if))
		self.globals.set(data.Symbol('return'), data.Method(lambda *args: args[0] if args else None))
		self.globals.set(data.Symbol('py'), data.Method(lambda x: eval(x.val)))
		self.globals.set(data.Symbol('number'), type_method(data.Number))
		self.globals.set(data.Symbol('string'), type_method(data.String))
		self.globals.set(data.Symbol('func'), type_method(data.Func, self.globals))
		self.globals.set(data.Symbol('class'), type_method(data.Class, self.globals))
		self.globals.set(data.Symbol('list'), type_method(data.List))
		self.globals.set(data.Symbol('range'), type_method(data.Range))
		self.globals.set(data.Symbol('type'), type_method(data.Type))
		self.globals.set(data.Symbol('symbol'), type_method(data.Symbol))
		self.globals.set(data.Symbol('map'), type_method(data.Map))
		self.globals.set(data.Symbol('void'), data.Method(lambda: type(None)))

	def print(self, *args):
        # Prints every value passed to it as a string.
		for val in args:
			print(call(get(val, '_string')).val)
	def _import(self, *args):
        # Loads a .qyl file relative to the current directory and adds it's scope to the global one.
		name = args[0].val
		try:
			file = open(f'{name}.qyl') # Open the file
			ast = parse.Parser().parse(parse.Lexer().tokenize(file.read())) # Lex and parse it
			program = Program(ast) # Create a program object
			program.run() # Run it
             # Set the name of the library in globals to a map containing the exported variables from that module.
			self.globals.set(data.Symbol(name.split('/')[-1]), program.globals)
		except FileNotFoundError: # Throw an error if the file is not found.
			errors.error('File not found')
	def _if(self, *args):
        # Executes the block passed to it only if the expression given to it is true.
		args[0].val.globals = self.globals # Set the scope of the block to run.
		if data.Bool(args[1]).val: # Convert the value to a boolean.
			call(args[0]) # Call the block if it is true.
	def run(self):
        # Runs the AST.
		for node in self.ast.val[:-1]: # Run all but the last node as expressions.
			expr(node, self.globals)
		return expr(self.ast.val[-1], self.globals) # Return the value of the last node.


def run(ast):
    # Shorthand for Program(ast).run()
    Program(ast).run()
