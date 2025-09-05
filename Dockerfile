FROM linuxserver/wireguard:latest

RUN apk add --no-cache python3 py3-pip

COPY wg-proxy.py /app/wg-proxy.py
RUN chmod +x /app/wg-proxy.py

RUN mkdir -p /etc/s6-overlay/s6-rc.d/wg-proxy/dependencies.d

COPY <<EOF /etc/s6-overlay/s6-rc.d/wg-proxy/type
longrun
EOF

COPY <<EOF /etc/s6-overlay/s6-rc.d/wg-proxy/run
#!/command/execlineb -P
python3 /app/wg-proxy.py
EOF

RUN chmod +x /etc/s6-overlay/s6-rc.d/wg-proxy/run
RUN echo wg-proxy > /etc/s6-overlay/s6-rc.d/user/contents.d/wg-proxy

EXPOSE 51822