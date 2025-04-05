FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install grpcio-tools

COPY app/proto/ app/proto/
COPY externalClients/TInvestApi/proto/ externalClients/TInvestApi/proto/
RUN python -m grpc_tools.protoc -I=externalClients/TInvestApi/proto --python_out=externalClients/TInvestApi/proto --grpc_python_out=externalClients/TInvestApi/proto externalClients/TInvestApi/proto/*.proto
RUN python -m grpc_tools.protoc -I=app/proto --python_out=app/proto --grpc_python_out=app/proto app/proto/*.proto

COPY . .

CMD ["python", "-u", "-m", "app.server"]