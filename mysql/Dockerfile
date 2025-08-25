FROM mysql:8.0

# 设置字符集和排序规则
ENV LANG=C.UTF-8 \
    TZ=Asia/Shanghai

# 设置时区为东八区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制初始化SQL脚本
COPY ./db_struct_data.sql /docker-entrypoint-initdb.d/

# 配置MySQL
COPY ./my.cnf /etc/mysql/conf.d/my.cnf

# MySQL数据文件将存储在/var/lib/mysql
VOLUME /var/lib/mysql 