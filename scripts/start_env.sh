echo 'Start ssh'
sudo service ssh start
echo 'Start mysql'
sudo service mysql start
echo 'Start memcached'
/usr/bin/memcached -u memcache -m 1024 -p 11211 -l 0.0.0.0 -d start
echo 'Start Redis'
nohup redis-server > /dev/null 2>&1 &
echo 'Start celery workers'
nohup celery -A weitter worker -l INFO > celery.logs &
echo 'Start Hbase'
sudo /home/jiuzhang/tools/hbase-2.4.15/bin/start-hbase.sh
echo 'Start hbase thrift'
sudo hbase-daemon.sh start thrift
