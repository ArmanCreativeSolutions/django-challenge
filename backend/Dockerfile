FROM python:3.10
ENV PYTHONUNBUFFERED 1

WORKDIR /backend

COPY ./requirements.txt requirements.txt
RUN pip --no-cache-dir --timeout=1000 install -r requirements.txt

COPY . /backend/

# Install supervisor
RUN apt-get update && apt-get install -y supervisor

# Install netcat
RUN apt-get update && apt-get install -y netcat-openbsd

# Copy supervisor configuration
COPY scripts/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Ensure the entrypoint script is executable
RUN chmod +x scripts/entrypoint.sh

RUN mkdir -p /var/log
RUN chown -R nobody:nogroup /var/log

EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["scripts/entrypoint.sh"]

# Default command to run supervisord
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]