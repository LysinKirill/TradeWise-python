# TradeWise Backend Service

## Overview

TradeWise-python is a Python-based backend service designed to handle requests to ML module and provide APIs for various clients

The backend includes the following components:
- **Domain Layer**: Contains service interfaces and core business logic.
- **Service Layer**: Implements business logic.
- **gRPC Layer**: Exposes APIs using gRPC for communication with clients.

---

## Getting Started

### Prerequisites

Ensure you have the following installed on your system:
- Python 3.9 or higher
- `pip` (Python package manager)
- A gRPC client tool for testing (e.g., Postman, BloomRPC) (optional)

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/tradewise-backend.git
    cd tradewise-backend
    ```

2. Create a virtual environment:

    ```bash
    #mac
    python3 -m venv .venv
    ```
    ```bash
    #windows
    python -m venv .venv
    ```

3. Activate the virtual environment:

    - On Windows:
        ```bash
        .venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```

4. Install project dependencies:

    ```bash
    pip install -r requirements.txt
    ```

---

## Running the Backend Service

To start the backend server, follow these steps:

1. Navigate to the project root directory.
2. Run the main server script:

    ```bash
    python -m app.server
    ```

3. You should see the following output in your console:

    ```plaintext
    Starting server on localhost:50051...
    ```

This indicates the gRPC server is running and ready to accept client connections.

---

## Connecting to the Backend

### Using a gRPC Client
1. Open a gRPC client tool (e.g., Postman, BloomRPC).
2. Import the `app/proto/hello.proto` file.
3. Use the connection details:
   - **Host**: `localhost`
   - **Port**: `50051`

### Interacting with the API
The backend exposes two methods via gRPC:
- **SayHello**: Returns a greeting message.
- **Echo**: Echoes back the provided message.

For detailed instructions, refer to the `hello.proto` file.

---
