# 1. Base Image
# O uso da imagem oficial é perfeito. Ela já contém os navegadores.
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# 2. Variáveis de Ambiente (Boas Práticas Django/Python)
# Impede o Python de criar arquivos .pyc desnecessários no container
ENV PYTHONDONTWRITEBYTECODE=1
# Garante que os logs do Django apareçam instantaneamente no console do Docker
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 3. Dependências
COPY requirements.txt .
# --no-cache-dir mantém a imagem leve
RUN pip install --no-cache-dir -r requirements.txt

# 4. Código Fonte
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]