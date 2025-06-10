 geth --http --http-addr 0.0.0.0 --http-port 8545 \
     --ws --ws-addr 0.0.0.0 --ws-port 8546 \
     --ws-api eth,net,web3,txpool,debug \
     --http-api eth,net,web3,txpool,debug \
     --http-corsdomain '*' --ws-origins '*' \
     --syncmode snap \
     --metrics --metrics.addr 0.0.0.0 \
     --datadir /path/to/ethereum/data \
     --authrpc.addr 0.0.0.0 --authrpc.port 8551 --authrpc.vhosts '*' \
     --authrpc.jwtsecret /path/to/jwt.hex