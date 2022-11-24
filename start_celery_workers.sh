ps auxww | awk '/celery -A weitter worker/ {print $2}' | xargs kill -9
nohup celery -A weitter worker -l INFO > celery.logs &
