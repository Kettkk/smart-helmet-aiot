FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY telemetry_simulator.py .
RUN useradd --system --uid 10001 simulator
USER simulator
CMD ["python", "telemetry_simulator.py"]
