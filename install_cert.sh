openssl s_client -showcerts -connect $1:$2 | openssl x509 -out /tmp/$1.crt
sudo cp /tmp/$1.crt /usr/local/share/ca-certificates/$1.crt
sudo update-ca-certificates
