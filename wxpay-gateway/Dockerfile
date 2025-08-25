FROM maven:3.9.9-eclipse-temurin-17-alpine AS build

WORKDIR /app

# 配置Maven使用阿里云镜像
RUN mkdir -p /root/.m2 \
    && echo '<?xml version="1.0" encoding="UTF-8"?>\
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">\
  <mirrors>\
    <mirror>\
      <id>aliyunmaven</id>\
      <mirrorOf>*</mirrorOf>\
      <name>阿里云公共仓库</name>\
      <url>https://maven.aliyun.com/repository/public</url>\
    </mirror>\
  </mirrors>\
</settings>' > /root/.m2/settings.xml

# 复制pom.xml
COPY pom.xml .

# 下载依赖项（利用Docker缓存）
RUN mvn dependency:go-offline -B

# 复制源代码
COPY src/ /app/src/

# 构建应用
RUN mvn package -DskipTests

# 运行阶段
FROM openjdk:17-jdk-alpine

WORKDIR /app

# 设置环境变量
ENV JAVA_OPTS="-Xms512m -Xmx512m" \
    TZ=Asia/Shanghai

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 创建日志和证书目录
RUN mkdir -p /app/logs /app/cert

# 复制构建好的jar包
COPY --from=build /app/target/*.jar app.jar

# 暴露端口
EXPOSE 8081


# 启动命令
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"] 