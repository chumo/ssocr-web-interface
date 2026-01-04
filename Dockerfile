# Build stage for ssocr
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libimlib2-dev \
    libx11-dev \
    wget \
    bzip2 \
    && rm -rf /var/lib/apt/lists/*

# Copy ssocr source and build
WORKDIR /build
# Download and extract specific version
RUN wget https://www.unix-ag.uni-kl.de/~auerswal/ssocr/ssocr-2.25.1.tar.bz2 \
    && tar -xjf ssocr-2.25.1.tar.bz2 \
    && rm ssocr-2.25.1.tar.bz2

WORKDIR /build/ssocr-2.25.1
RUN make ssocr

# Runtime stage
FROM python:3.12-slim

# Install runtime dependencies for ssocr and python tools
RUN apt-get update && apt-get install -y \
    libimlib2 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
# Using requirements.txt generated from pip or just manually since list is short
RUN pip install flask requests sh

# Copy ssocr binary from builder
COPY --from=builder /build/ssocr-2.25.1/ssocr /app/ssocr
# Ensure it's executable
RUN chmod +x /app/ssocr

# Copy application code
COPY . /app

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
