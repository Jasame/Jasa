bind='127.0.0.1:8895'
workers=2
threads=4
timeout=60
accesslog='-'
errorlog='-'
capture_output=True
umask=0o077

# Process management is provided by systemd, without a home-directory socket.
control_socket_disable=True
