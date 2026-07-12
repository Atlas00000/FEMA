# Wave 1 API image
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /work/ops/api
COPY ops/api/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt
COPY AI/requirements.txt /tmp/ai-req.txt
RUN pip install --no-cache-dir -r /tmp/ai-req.txt || true
COPY ops/api /work/ops/api
# fema_ops mounted at runtime; stub for import path
ENV PYTHONPATH=/work/AI:/work/ops/api
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
