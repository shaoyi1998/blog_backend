# 云端环境
Ubuntu 22.04 LTS

# 前端
放/www目录下面,不要放后端!!!!!不然一堆bug

例如后端uwsgi 启动ini ,ini 制定了pid文件,结果uwsgi.log报错没权访问
用root去访问依然nginx依然报错upstream prematurely closed connection
结果排查半天不是nginx.conf和uwsgi的问题,是pid没权限,需要chmod 777