# Upstream no longer distributes public images. Build its final community release.
FROM golang:1.24.8-alpine AS build
RUN apk add --no-cache git ca-certificates
RUN go install github.com/minio/minio@RELEASE.2025-10-15T17-29-55Z
FROM alpine:3.22
RUN apk add --no-cache ca-certificates && adduser -D -u 10001 minio && mkdir -p /home/minio/data && chown -R minio:minio /home/minio/data
COPY --from=build /go/bin/minio /usr/local/bin/minio
USER minio
ENTRYPOINT ["minio"]
