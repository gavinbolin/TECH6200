def get_number(prompt):
    """Repeatedly asks the user for a number until they provide a valid one."""
    while True:
        user_input = input(prompt)
        try:
            return float(user_input)
        except ValueError:
            print(f"⚠️ Error: '{user_input}' is not a valid number. Please try again.")

def main():
    print("--- 🧮 Simple Command Line Calculator ---")
    print("Type your numbers and choose an operator to get started.\n")

    # 1. Prompt for first number
    num1 = get_number("Enter the first number: ")

    # 2. Prompt for operation
    while True:
        operator = input("Enter an operation (+, -, *, /): ").strip()
        if operator in ['+', '-', '*', '/']:
            break
        print("⚠️ Error: Invalid operator. Please use +, -, *, or /.")

    # 3. Prompt for second number
    num2 = get_number("Enter the second number: ")

    # 4. Calculate and handle potential errors
    result = None
    error_message = None

    if operator == '+':
        result = num1 + num2
    elif operator == '-':
        result = num1 - num2
    elif operator == '*':
        result = num1 * num2
    elif operator == '/':
        if num2 == 0:
            error_message = "Division by zero is not allowed."
        else:
            result = num1 / num2

    # 5. Display the result
    print("\n--- Result ---")
    if error_message:
        print(f"❌ {error_message}")
    else:
        # We format the output to remove unnecessary decimals (e.g., 5.0 becomes 5)
        formatted_result = f"{result:g}"
        print(f"✅ {num1:g} {operator} {num2:g} = {formatted_result}")
    print("--------------\n")

if __name__ == "__main__":
    main()