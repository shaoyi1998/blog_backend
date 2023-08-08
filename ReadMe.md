# 介绍
基于django实现的博客后端系统
需本人blog前端项目配合使用

# 云端环境
2c2g 
Ubuntu 22.04 LTS
sqlite

# 注意

放/www目录下面,不要放后端!!!!!不然一堆bug

例如后端uwsgi 启动ini ,ini 制定了pid文件,结果uwsgi.log报错没权访问
用root去访问依然nginx依然报错upstream prematurely closed connection
结果排查半天不是nginx.conf和uwsgi的问题,是pid没权限,需要chmod 777

# 配置

uswgi参见rywy.ini
后端放在 /home/ubuntu里面
前端放在 /www/blog
nginx 修改第一行user为 ubuntu; 防止权限问题或自行修改用户组确保前端默认www-data有权访问后端media下保存的文件
nginx配置如下
server {
        listen       443 ssl http2;
        listen       [::]:443 ssl http2;
        server_name  riyueweiyi.cn;
        root         /www/riyueweiyi;
		index 		index.html index.htm;

        ssl_certificate "/home/ubuntu/ssls/riyueweiyi.cn.pem";
        ssl_certificate_key "/home/ubuntu/ssls/riyueweiyi.cn.key";
        ssl_session_cache shared:SSL:1m;
        ssl_session_timeout  10m;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        include /etc/nginx/default.d/*.conf;

		location @router {
			rewrite ^.*$ /index.html last;
		}

		
        location / {
                try_files $uri $uri/ /index.html;
        }
		
		location /api { 
			gzip off;		
			include uwsgi_params;
	        uwsgi_connect_timeout 65;
	        uwsgi_pass 127.0.0.1:1234;
		}

		location /media {
				alias /home/ubuntu/django/riyueweiyi/media;
			}
    }


# 效果
riyueweiyi.cn
