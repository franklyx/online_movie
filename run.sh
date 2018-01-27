#!/usr/bin/env bash
# 生产环境部署 ./run.sh product
# 测试环境部署 ./run.sh test


case $1 in
    'product')
    path=$(pwd)
        # nginx
        sudo docker run -d --network host --name video-nginx nginx

        sudo docker cp $path/doc/nginx/nginx.conf video-nginx:/etc/nginx/
        sudo docker cp $path/doc/nginx/localtime video-nginx:/etc/
        sudo docker -d video-nginx service nginx reload
        # server
        sudo docker run -tid -v $path/code:/home/code -p 8887:8887 --name video-server1 video-server:v1
        sudo docker run -tid -v $path/code:/home/code -p 8888:8888 --name video-server2 video-server:v1
        sudo docker run -tid -v $path/code:/home/code -p 8889:8889 --name video-server3 video-server:v1
        #
        docker exec -d video-server1 python manage.py runserver --host 0.0.0.0 --port 8887
        docker exec -d video-server2 python manage.py runserver --host 0.0.0.0 --port 8888
        docker exec -d video-server3 python manage.py runserver --host 0.0.0.0 --port 8889
    ;;
    'test')
    path=$(pwd)
        sudo docker run -tid -p 5000:5000 -v $path/code:/home/code --name video-server python:3.6.3-slim-stretch
    ;;
esac