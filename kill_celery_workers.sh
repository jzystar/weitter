ps auxww | awk '/celery -A weitter worker/ {print $2}' | xargs kill -9
