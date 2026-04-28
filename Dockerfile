# Build Go binaries
FROM golang:1.22-bullseye AS gobuilder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# Compile the TGD decoder (dddparser)
RUN go build -mod=mod -o dddparser ./cmd/dddparser
# Compile the Web Server
RUN go build -mod=mod -o webserver ./web/main.go

# Final runtime image
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, Python3-pip, Node.js and python-is-python3 (so "python" command works)
RUN apt-get update && apt-get install -y \
    python3 python3-pip python-is-python3 \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN pip3 install pandas openpyxl

# Install Node dependencies (xlsx) locally in root so catalina_processor.mjs finds it
RUN npm install xlsx

# Copy the entire codebase and built binaries
COPY --from=gobuilder /app/ /app/
COPY --from=gobuilder /app/dddparser /app/
COPY --from=gobuilder /app/webserver /app/

# Create output and upload directories just in case
RUN mkdir -p web/uploads web/outputs

EXPOSE 8080

CMD ["./webserver"]