#!/data/data/com.termux/files/usr/bin/bash

# Vypni protected mode priamo v bežiacom Redise
redis-cli CONFIG SET protected-mode no

# Overenie
redis-cli CONFIG GET protected-mode

# Vytvor config pre trvalé nastavenie (lokálny dev)
cat > redis.conf << 'CONF'
bind 127.0.0.1
port 6379
protected-mode no
daemonize yes
CONF

# Reštart Redisu s novým configom
pkill redis-server
sleep 1
redis-server redis.conf

# Overenie, že beží
redis-cli INFO server | grep redis_version

# Test funkčnosti
redis-cli HSET waste:1 type plast weight 2.5 user_id 123
redis-cli HGETALL waste:1
redis-cli LPUSH queue:processing waste:1
redis-cli LRANGE queue:processing 0 -1

echo "Redis je nastavený a funguje."
