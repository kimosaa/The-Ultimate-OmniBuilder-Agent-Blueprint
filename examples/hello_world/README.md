# Hello World Example

This is a simple example demonstrating OmniBuilder's basic capabilities.

## Goal

Create a simple "Hello World" application in multiple languages.

## Running with OmniBuilder

```bash
# Navigate to this directory
cd examples/hello_world

# Run the example
omnibuilder run "Create hello world scripts in Python, JavaScript, and Rust"
```

## Expected Output

OmniBuilder should:
1. Create `hello.py` with a Python hello world
2. Create `hello.js` with a JavaScript hello world
3. Create `hello.rs` with a Rust hello world
4. Ensure all scripts are executable

## Manual Testing

```bash
python hello.py
node hello.js
rustc hello.rs && ./hello
```
