# Generate 32 bytes and convert them to hex
dd if=/dev/urandom bs=32 count=1 2>/dev/null | xxd -ps -c 64
