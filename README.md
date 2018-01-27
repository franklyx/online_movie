### short-video使用方法

#### 环境准备
1.
    docker pull nginx:latest
2.
    docker pull python:3.6.3-slim-stretch

#### 正式部署
1. 第一步
    运行./built.sh 创建生成镜像文件
    ps: 运行 docker images 查看生成的镜像
2. 第二步
    运行 ./run.sh product 启动镜像文件
    ps: 运行 docker ps -a 查看正在运行的镜像
3. 第三步
    打开浏览器访问

#### 测试环境
1. 第一步
    运行 ./run.sh test 启动镜像文件
    ps: 运行 docker ps -a 查看正在运行的镜像


####  修改成docker-compose环境部署
1. docker up -d --build 命令启动
