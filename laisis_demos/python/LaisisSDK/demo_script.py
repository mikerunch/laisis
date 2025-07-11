import laisis_sdk

# Initialize SDK (default: localhost:11434)
sdk = laisis_sdk.LAISIS(port=11434)

# Send message via the SDK object
answer = sdk.send_message("Hello, how are you?")

# Wait for the user to press Enter before showing the answer
input("Press [Enter] to see the answer...")

print("AI Answer:", answer)
