# TradeWise Backend Service

## Overview

TradeWise-python is a Python-based backend service designed to handle requests to ML modules and provide APIs for various clients.

The backend includes the following components:
- **Domain Layer**: Contains service interfaces and core business logic.
- **Service Layer**: Implements business logic.
- **gRPC Layer**: Exposes APIs using gRPC for communication with clients.

---

## Getting Started

### Prerequisites

Ensure you have the following installed on your system:
- Python 3.12 or higher
- `pip` (Python package manager)
- A gRPC client tool for testing (e.g., Postman, BloomRPC) (optional)

### Installation

1. Create a virtual environment:

    - On macOS/Linux:
    ```bash
    python3 -m venv .venv
    ```

    - On Windows:
    ```bash
    python -m venv .venv
    ```

2. Activate the virtual environment:

    - On Windows:
        ```bash
        .venv\Scripts\activate
        ```
    - On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```

3. Install project dependencies:

    ```bash
   # windows
   pip install -r requirements.txt
   ```
   
   ```bash
   # mac
   pip3 install -r requirements.txt
    ```

4. Regenerate python classes for proto (Optional):
   ```bash
    python3 -m grpc_tools.protoc -I=externalClients/TInvestApi/proto --python_out=externalClients/TInvestApi/proto --grpc_python_out=externalClients/TInvestApi/proto externalClients/TInvestApi/proto/*.proto
    python3 -m grpc_tools.protoc -I=app/proto --python_out=app/proto --grpc_python_out=app/proto app/proto/*.proto
   ```
   ```bash
    python -m postProcessing.Processor
   ```

5. Set up your `.env` file (for **debug purposes only**):
    - Create a `.env` file in the root directory of the project.
    - Add the following line to the file, replacing `your_token_here` with your actual token:
      ```
      INVEST_TOKEN=your_token_here
      ```

---

## Running the Backend Service

To start the backend server, follow these steps:

1. Navigate to the project root directory.
2. Ensure the `.env` file is properly configured with your token for **debug purposes**.
3. Run the main server script:

    ```shell
    python -m app.server
    ```

4. You should see the following output in your console:

    ```plaintext
    Starting server on localhost:50051...
    ```

This indicates the gRPC server is running and ready to accept client connections.

---

## Running Migrations
To apply database migrations, follow these steps:

1. Navigate to the project root directory.
2. Ensure the .env file is properly configured with your database connection details (if applicable).
3. Run the migration script as a module:

    - On macOS/Linux:
    ```bash
    python3 -m migrations.migrate
    ```

    - On Windows:
    ```bash
    python -m migrations.migrate
    ```
The migration runner will:

1) Load all migration classes from the migrations folder.
2) Apply any pending migrations to the database.
3) Log the results (skipped, failed, and applied migrations).

---

## Token Management

### Debug Option: `.env` File
The `.env` file can be used to store your `INVEST_TOKEN` for local testing and debugging purposes. For example:
```plaintext
INVEST_TOKEN=your_token_here
