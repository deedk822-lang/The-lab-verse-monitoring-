import argparse
from .service import main

def cli():
    """
    Command-line interface for the cost optimizer service.
    """
    parser = argparse.ArgumentParser(description="Cost Optimizer Service")
    parser.add_argument(
        "--port",
        type=int,
        default=8083,
        help="Port to run the service on."
    )
    args = parser.parse_args()

    # The main function in service.py currently hardcodes the port,
    # but this sets up the CLI for future expansion.
    main()

if __name__ == "__main__":
    cli()