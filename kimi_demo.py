def process_data(data):
    """
    Process a list of numbers by squaring each element.
    This implementation was suggested by Kimi Code.
    """
    try:
        processed = [x**2 for x in data]
        print(f"Processed data: {processed}")
        return processed
    except Exception as e:
        print(f"Error processing data: {e}")
        return None


def main():
    print("Kimi Code Demo")
    # Kimi can suggest improvements to this script
    data = [1, 2, 3, 4, 5]
    process_data(data)


if __name__ == "__main__":
    main()
